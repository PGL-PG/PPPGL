"""
主要的Flask应用 - 集成智能场景分析系统
替代复杂的app.py，提供精简而强大的Excel分析功能
"""

from flask import Flask, request, jsonify
import json
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename

# 导入我们的智能分析系统
from enhanced_analysis_api import enhanced_analyze_data

app = Flask(__name__)

# 简单的CORS处理
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = None

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_convert_value(value):
    """安全地转换值为可JSON序列化的类型"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (bool, np.bool_)):
        return bool(value)
    elif isinstance(value, (int, float)) or str(type(value)).startswith("<class 'numpy.int") or str(type(value)).startswith("<class 'numpy.float"):
        if 'int' in str(type(value)):
            return int(value)
        else:
            return float(value)
    elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    else:
        return value

def detect_data_type(series):
    """检测数据类型"""
    if series.empty or series.isna().all():
        return 'empty'
    
    non_null_series = series.dropna()
    
    if pd.api.types.is_numeric_dtype(series):
        return 'numeric'
    
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'
    
    try:
        pd.to_datetime(non_null_series.head(10))
        return 'datetime'
    except:
        pass
    
    if len(non_null_series) > 0:
        unique_ratio = len(non_null_series.unique()) / len(non_null_series)
        unique_count = len(non_null_series.unique())
        
        if unique_ratio < 0.5 and unique_count < 20:
            return 'categorical'
    
    return 'text'

def read_excel_file(filepath):
    """读取Excel文件并返回所有工作表信息"""
    try:
        if not os.path.exists(filepath):
            raise Exception(f"文件不存在: {filepath}")
        
        excel_file = pd.ExcelFile(filepath)
        sheets_info = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
            # 分析每列信息
            columns_info = {}
            for col in df.columns:
                try:
                    col_data = df[col]
                    data_type = detect_data_type(col_data)
                    
                    sample_values = []
                    for val in col_data.dropna().head(5):
                        try:
                            if pd.isna(val):
                                sample_values.append(None)
                            elif isinstance(val, (bool, np.bool_)):
                                sample_values.append(bool(val))
                            elif isinstance(val, (pd.Timestamp, pd.Timedelta)):
                                sample_values.append(str(val))
                            elif isinstance(val, (np.integer, np.floating)):
                                sample_values.append(float(val))
                            else:
                                sample_values.append(str(val))
                        except:
                            sample_values.append(str(val))
                    
                    columns_info[str(col)] = {
                        'type': data_type,
                        'non_null_count': int(col_data.count()),
                        'total_count': len(col_data),
                        'sample_values': sample_values
                    }
                except Exception as e:
                    columns_info[str(col)] = {
                        'type': 'error',
                        'non_null_count': 0,
                        'total_count': len(df),
                        'sample_values': []
                    }
            
            # 生成数据预览
            try:
                preview_data = []
                for _, row in df.head(5).iterrows():
                    row_dict = {}
                    for col, val in row.items():
                        try:
                            if pd.isna(val):
                                row_dict[str(col)] = None
                            elif isinstance(val, (bool, np.bool_)):
                                row_dict[str(col)] = bool(val)
                            elif isinstance(val, (pd.Timestamp, pd.Timedelta)):
                                row_dict[str(col)] = str(val)
                            elif isinstance(val, (np.integer, np.floating)):
                                row_dict[str(col)] = float(val)
                            else:
                                row_dict[str(col)] = str(val)
                        except:
                            row_dict[str(col)] = str(val)
                    preview_data.append(row_dict)
            except Exception as e:
                preview_data = []
            
            sheets_info[sheet_name] = {
                'columns': columns_info,
                'row_count': int(len(df)),
                'preview': preview_data
            }
        
        return sheets_info
    
    except Exception as e:
        raise Exception(f"读取Excel文件失败: {str(e)}")

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 读取并分析Excel文件
            sheets_data = read_excel_file(filepath)
            
            return jsonify({
                'status': 'success',
                'filename': filename,
                'sheets_data': sheets_data,
                'message': f'文件上传成功，共发现 {len(sheets_data)} 个工作表'
            })
        else:
            return jsonify({'error': '不支持的文件格式，仅支持 .xlsx 和 .xls'}), 400
    
    except Exception as e:
        return jsonify({'error': f'文件上传失败: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """智能数据分析接口 - 使用场景匹配和智能提示词"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '没有接收到数据'}), 400
        
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        selected_columns = data.get('selected_columns', [])
        custom_requirements = data.get('custom_requirements', '')
        
        if not all([filename, sheet_name]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 读取Excel文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        if df.empty:
            return jsonify({'error': '数据为空'}), 400
        
        # 如果指定了列，则只分析这些列
        if selected_columns:
            missing_columns = [col for col in selected_columns if col not in df.columns]
            if missing_columns:
                return jsonify({'error': f'指定的列不存在: {missing_columns}'}), 400
            df = df[selected_columns]
        
        # 调用增强分析系统
        result = enhanced_analyze_data(df, custom_requirements)
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"分析失败详细错误: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': 'Excel智能分析系统运行正常',
        'version': '2.0'
    })

if __name__ == '__main__':
    print("启动Excel智能分析系统...")
    print("服务地址: http://localhost:8000")
    app.run(debug=True, port=8000)