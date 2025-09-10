from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename

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

# 移除了测试用的API配置，现在使用本地分析

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_data_type(series):
    """检测数据类型"""
    if series.empty or series.isna().all():
        return 'empty'
    
    # 去除空值
    non_null_series = series.dropna()
    
    # 检测数值类型
    if pd.api.types.is_numeric_dtype(series):
        return 'numeric'
    
    # 检测日期时间类型
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'datetime'
    
    # 尝试转换为日期时间
    try:
        pd.to_datetime(non_null_series.head(10))
        return 'datetime'
    except:
        pass
    
    # 检测分类数据
    unique_ratio = len(non_null_series.unique()) / len(non_null_series)
    if unique_ratio < 0.5 and len(non_null_series.unique()) < 20:
        return 'categorical'
    
    return 'text'

def read_excel_file(filepath):
    """读取Excel文件并返回所有工作表信息"""
    try:
        print(f"开始读取Excel文件: {filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            raise Exception(f"文件不存在: {filepath}")
        
        # 读取所有工作表名称
        print("创建ExcelFile对象")
        excel_file = pd.ExcelFile(filepath)
        print(f"发现工作表: {excel_file.sheet_names}")
        
        sheets_info = {}
        
        for sheet_name in excel_file.sheet_names:
            print(f"处理工作表: {sheet_name}")
            
            # 读取工作表数据
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            print(f"工作表 {sheet_name} 数据形状: {df.shape}")
            
            # 分析每列的信息
            columns_info = {}
            for col in df.columns:
                try:
                    col_data = df[col]
                    data_type = detect_data_type(col_data)
                    
                    # 获取样本值，处理可能的序列化问题
                    sample_values = []
                    for val in col_data.dropna().head(5):
                        try:
                            # 转换为可序列化的类型
                            if pd.isna(val):
                                sample_values.append(None)
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
                    print(f"处理列 {col} 时出错: {str(e)}")
                    columns_info[str(col)] = {
                        'type': 'error',
                        'non_null_count': 0,
                        'total_count': len(df),
                        'sample_values': []
                    }
            
            # 生成数据预览（前5行）
            try:
                preview_data = []
                for _, row in df.head(5).iterrows():
                    row_dict = {}
                    for col, val in row.items():
                        try:
                            if pd.isna(val):
                                row_dict[str(col)] = None
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
                print(f"生成预览数据时出错: {str(e)}")
                preview_data = []
            
            sheets_info[sheet_name] = {
                'columns': columns_info,
                'row_count': len(df),
                'preview': preview_data
            }
            
            print(f"工作表 {sheet_name} 处理完成")
        
        print("Excel文件读取完成")
        return sheets_info
    
    except Exception as e:
        print(f"读取Excel文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"读取Excel文件失败: {str(e)}")

def analyze_data_simple(columns_info):
    """简单的数据分析（不依赖外部API）"""
    analysis_methods = []
    insights = []
    
    # 分析数据类型
    numeric_cols = [col for col, info in columns_info.items() if info['type'] == 'numeric']
    categorical_cols = [col for col, info in columns_info.items() if info['type'] == 'categorical']
    datetime_cols = [col for col, info in columns_info.items() if info['type'] == 'datetime']
    
    if numeric_cols:
        analysis_methods.append("数值分析")
        insights.append(f"发现 {len(numeric_cols)} 个数值型字段：{', '.join(numeric_cols)}")
    
    if categorical_cols:
        analysis_methods.append("分类分析")
        insights.append(f"发现 {len(categorical_cols)} 个分类字段：{', '.join(categorical_cols)}")
    
    if datetime_cols:
        analysis_methods.append("时间序列分析")
        insights.append(f"发现 {len(datetime_cols)} 个时间字段：{', '.join(datetime_cols)}")
    
    # 生成推荐图表
    recommended_charts = []
    if numeric_cols and categorical_cols:
        recommended_charts.append({
            "type": "bar",
            "x_axis": categorical_cols[0],
            "y_axis": numeric_cols[0],
            "title": f"{categorical_cols[0]} vs {numeric_cols[0]}"
        })
    
    if len(numeric_cols) >= 2:
        recommended_charts.append({
            "type": "scatter",
            "x_axis": numeric_cols[0],
            "y_axis": numeric_cols[1],
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]} 散点图"
        })
    
    return {
        "analysis_methods": analysis_methods,
        "recommended_charts": recommended_charts,
        "insights": "基于数据结构的自动分析：" + "; ".join(insights),
        "attribution_analysis": "建议选择数值型字段进行归因分析"
    }

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传Excel文件"""
    try:
        print("收到上传请求")
        
        if 'file' not in request.files:
            print("错误：请求中没有文件")
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        print(f"文件名: {file.filename}")
        
        if file.filename == '':
            print("错误：文件名为空")
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 使用安全的文件名
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"保存文件到: {filepath}")
            
            # 保存文件
            file.save(filepath)
            print("文件保存成功")
            
            # 检查文件是否存在
            if not os.path.exists(filepath):
                print("错误：文件保存后不存在")
                return jsonify({'error': '文件保存失败'}), 500
            
            print(f"文件大小: {os.path.getsize(filepath)} bytes")
            
            try:
                # 读取Excel文件
                print("开始读取Excel文件")
                sheets_info = read_excel_file(filepath)
                print("Excel文件读取成功")
                
                return jsonify({
                    'filename': filename,
                    'sheets': sheets_info
                })
            
            except Exception as e:
                print(f"读取Excel文件时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'读取Excel文件失败: {str(e)}'}), 500
        
        print("错误：不支持的文件格式")
        return jsonify({'error': '不支持的文件格式'}), 400
        
    except Exception as e:
        print(f"上传过程中出现未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

def generate_chart_data(df, columns_info):
    """生成图表数据"""
    chart_data = []
    
    # 为分类数据生成饼图
    categorical_cols = [col for col, info in columns_info.items() if info['type'] == 'categorical']
    for col in categorical_cols[:2]:  # 最多生成2个饼图
        value_counts = df[col].value_counts().head(10)  # 取前10个值
        pie_data = [{'name': str(name), 'value': int(count)} for name, count in value_counts.items()]
        chart_data.append({
            'type': 'pie',
            'column': col,
            'data': pie_data
        })
    
    # 为数值数据生成直方图
    numeric_cols = [col for col, info in columns_info.items() if info['type'] == 'numeric']
    for col in numeric_cols[:2]:  # 最多生成2个直方图
        numeric_data = df[col].dropna()
        if len(numeric_data) > 0:
            # 生成直方图数据
            hist_data = numeric_data.tolist()
            chart_data.append({
                'type': 'histogram',
                'column': col,
                'data': hist_data
            })
    
    return chart_data

def calculate_statistics(df, columns_info):
    """计算统计信息"""
    stats = {}
    
    numeric_cols = [col for col, info in columns_info.items() if info['type'] == 'numeric']
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            stats[col] = {
                'mean': float(col_data.mean()),
                'median': float(col_data.median()),
                'std': float(col_data.std()),
                'min': float(col_data.min()),
                'max': float(col_data.max())
            }
    
    return stats

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """分析数据"""
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet_name')
    selected_columns = data.get('selected_columns', [])
    custom_requirements = data.get('custom_requirements', '')
    
    if not filename or not sheet_name:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        # 读取Excel文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # 如果指定了列，则只分析这些列
        if selected_columns:
            df = df[selected_columns]
        
        # 分析列信息
        columns_info = {}
        for col in df.columns:
            col_data = df[col]
            data_type = detect_data_type(col_data)
            columns_info[col] = {
                'type': data_type,
                'non_null_count': col_data.count(),
                'total_count': len(col_data)
            }
        
        # 生成分析结果
        analysis_result = analyze_data_simple(columns_info)
        
        # 计算统计信息
        stats = calculate_statistics(df, columns_info)
        
        # 生成图表数据
        chart_data = generate_chart_data(df, columns_info)
        
        # 数据预览（前5行）
        data_preview = df.head(5).fillna('').to_dict('records')
        
        return jsonify({
            'analysis': analysis_result,
            'statistics': stats,
            'chart_data': chart_data,
            'data_preview': data_preview
        })
    
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

def perform_attribution_analysis(df, target_column):
    """执行归因分析"""
    target_data = df[target_column].dropna()
    
    # 计算与其他数值列的相关性
    correlations = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != target_column:
            correlation = df[col].corr(target_data)
            if not pd.isna(correlation):
                correlations[col] = round(correlation, 3)
    
    # 计算分类变量的贡献度
    contributions = {}
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        col_contributions = {}
        grouped = df.groupby(col)[target_column].mean()
        overall_mean = target_data.mean()
        
        for category, mean_value in grouped.items():
            contribution = ((mean_value - overall_mean) / overall_mean) * 100
            col_contributions[str(category)] = round(contribution, 2)
        
        if col_contributions:
            contributions[col] = col_contributions
    
    # 异常值检测
    Q1 = target_data.quantile(0.25)
    Q3 = target_data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[target_column] < lower_bound) | (df[target_column] > upper_bound)]
    outliers_data = outliers.head(10).to_dict('records')  # 最多返回10个异常值
    
    # 生成归因报告
    attribution_report = f"""归因诊断报告 - {target_column}

1. 目标指标统计：
   - 平均值：{target_data.mean():.2f}
   - 标准差：{target_data.std():.2f}
   - 数据范围：{target_data.min():.2f} ~ {target_data.max():.2f}

2. 相关性分析："""
    
    if correlations:
        sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        for factor, corr in sorted_corr[:5]:  # 显示前5个最相关的因素
            direction = "正向" if corr > 0 else "负向"
            strength = "强" if abs(corr) > 0.7 else "中等" if abs(corr) > 0.3 else "弱"
            attribution_report += f"\n   - {factor}: {direction}相关，强度{strength}（{corr}）"
    else:
        attribution_report += "\n   - 未发现显著的数值相关性"
    
    attribution_report += "\n\n3. 分类变量贡献度："
    if contributions:
        for factor, contribs in contributions.items():
            attribution_report += f"\n   - {factor}:"
            sorted_contribs = sorted(contribs.items(), key=lambda x: abs(x[1]), reverse=True)
            for category, contrib in sorted_contribs[:3]:  # 显示前3个贡献最大的类别
                direction = "正向" if contrib > 0 else "负向"
                attribution_report += f"\n     * {category}: {direction}贡献 {contrib:.1f}%"
    else:
        attribution_report += "\n   - 未发现显著的分类变量贡献"
    
    attribution_report += f"\n\n4. 异常值分析：\n   - 检测到 {len(outliers)} 个异常值，占总数据的 {len(outliers)/len(df)*100:.1f}%"
    
    if len(outliers) > 0:
        attribution_report += "\n   - 建议进一步调查这些异常值的原因"
    
    return {
        'correlations': correlations,
        'contributions': contributions,
        'outliers_count': len(outliers),
        'outliers_data': outliers_data,
        'attribution_report': attribution_report,
        'target_stats': {
            'mean': float(target_data.mean()),
            'std': float(target_data.std()),
            'min': float(target_data.min()),
            'max': float(target_data.max())
        }
    }

@app.route('/api/attribution', methods=['POST'])
def attribution_analysis():
    """归因诊断分析"""
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet_name')
    target_column = data.get('target_column')
    
    if not all([filename, sheet_name, target_column]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        # 读取Excel文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # 检查目标列是否存在
        if target_column not in df.columns:
            return jsonify({'error': f'目标列 "{target_column}" 不存在'}), 400
        
        # 检查目标列是否为数值类型
        if not pd.api.types.is_numeric_dtype(df[target_column]):
            return jsonify({'error': f'目标列 "{target_column}" 不是数值类型'}), 400
        
        # 执行归因分析
        result = perform_attribution_analysis(df, target_column)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'归因分析失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)