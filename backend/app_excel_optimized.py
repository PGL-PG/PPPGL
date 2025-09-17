from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import requests

# 导入我们的Excel分析引擎
from excel_analysis_engine import (
    safe_convert_value, detect_business_scenario, identify_key_fields,
    perform_excel_basic_analysis, perform_multi_dimensional_analysis,
    generate_practical_insights
)

# 导入增强版分析API
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
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
# 简化的 Gemini API 调用
API_KEY = "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ"  # 直接设置API Key
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = None  # 移除文件大小限制
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def generate_intelligent_charts(df, basic_stats_overview, ai_insights, data_summary):
    """基于数据特征直接生成有意义的可视化图表"""
    charts = []
    
    try:
        # 基于数据特征智能生成图表
        charts = create_charts_from_data_analysis(df, basic_stats_overview, data_summary)
                
    except Exception as e:
        print(f"智能图表生成失败: {e}")
        # 备用方案：使用简化图表生成
        charts = generate_fallback_charts(df, basic_stats_overview)
    
    return charts

def create_charts_from_data_analysis(df, basic_stats_overview, data_summary):
    """直接基于数据分析创建有价值的图表"""
    charts = []
    
    # 1. 分析数据结构，识别有意义的维度
    field_analysis = analyze_field_characteristics(df)
    
    # 2. 按优先级生成图表
    
    # 优先级1：排行榜类图表（分类字段 x 数值字段）
    if field_analysis['categorical_fields'] and field_analysis['numeric_fields']:
        for cat_field in field_analysis['categorical_fields'][:2]:  # 最多2个分类字段
            for num_field in field_analysis['numeric_fields'][:1]:  # 主要数值字段
                chart = create_ranking_chart(df, cat_field, num_field)
                if chart:
                    charts.append(chart)
                    break
            if charts:  # 每个分类字段只生成一个图表
                break
    
    # 优先级2：分布类图表（占比分析）
    if field_analysis['categorical_fields'] and len(charts) < 3:
        for cat_field in field_analysis['categorical_fields'][:2]:
            chart = create_distribution_chart(df, cat_field)
            if chart:
                charts.append(chart)
                break
    
    # 优先级3：相关性分析（数值字段间）
    if len(field_analysis['numeric_fields']) >= 2 and len(charts) < 3:
        chart = create_correlation_chart(df, field_analysis['numeric_fields'][:2])
        if chart:
            charts.append(chart)
    
    # 优先级4：时间趋势分析
    if field_analysis['time_fields'] and field_analysis['numeric_fields'] and len(charts) < 4:
        chart = create_trend_chart(df, field_analysis['time_fields'][0], field_analysis['numeric_fields'][0])
        if chart:
            charts.append(chart)
    
    return charts[:4]  # 最多返回4个图表

def analyze_field_characteristics(df):
    """分析字段特征，识别不同类型的字段"""
    analysis = {
        'numeric_fields': [],
        'categorical_fields': [],
        'time_fields': [],
        'text_fields': []
    }
    
    for col in df.columns:
        col_data = pd.Series(df[col]).dropna()
        if len(col_data) == 0:
            continue
            
        # 数值字段
        if pd.api.types.is_numeric_dtype(col_data):
            analysis['numeric_fields'].append(col)
            
        # 时间字段
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            analysis['time_fields'].append(col)
            
        # 分类字段（低基数比）
        else:
            unique_ratio = len(col_data.unique()) / len(col_data)
            unique_count = len(col_data.unique())
            
            if unique_ratio < 0.5 and unique_count < 30:  # 适合做分类的数据
                analysis['categorical_fields'].append(col)
            else:
                analysis['text_fields'].append(col)
    
    return analysis

def create_ranking_chart(df, cat_field, num_field):
    """创建排行榜图表"""
    try:
        # 按分类字段分组，计算数值字段的总和
        grouped = df.groupby(cat_field)[num_field].sum().sort_values(ascending=False)
        
        if len(grouped) < 2:  # 数据太少，不适合做图表
            return None
            
        # 取前10名
        top_data = grouped.head(10)
        chart_data = [{'name': str(name), 'value': float(value)} for name, value in top_data.items()]
        
        return {
            'type': 'bar',
            'title': f'{cat_field} {num_field} 排行榜',
            'data': chart_data,
            'subtitle': f'展示 {cat_field} 在 {num_field} 上的表现排名，{top_data.index[0]} 排名第一'
        }
    except Exception as e:
        return None

def create_distribution_chart(df, cat_field):
    """创建分布图表"""
    try:
        # 计算各类别的数量和占比
        value_counts = df[cat_field].value_counts()
        
        if len(value_counts) < 2:  # 数据太少
            return None
            
        # 取前8个类别
        top_values = value_counts.head(8)
        total = top_values.sum()
        
        chart_data = []
        for name, count in top_values.items():
            percentage = (count / total * 100) if total > 0 else 0
            chart_data.append({'name': str(name), 'value': round(percentage, 1)})
        
        return {
            'type': 'pie',
            'title': f'{cat_field} 分布情况',
            'data': chart_data,
            'subtitle': f'{cat_field} 的分布情况，{top_values.index[0]} 占比最高 ({chart_data[0]["value"]}%)'
        }
    except Exception as e:
        return None

def create_correlation_chart(df, numeric_fields):
    """创建相关性散点图"""
    try:
        field1, field2 = numeric_fields[0], numeric_fields[1]
        
        # 获取清洁数据
        clean_data = df[[field1, field2]].dropna()
        
        if len(clean_data) < 10:  # 数据太少
            return None
            
        # 限制数据点数量避免性能问题
        sample_data = clean_data.sample(min(100, len(clean_data)))
        
        chart_data = [[float(row[field1]), float(row[field2])] for _, row in sample_data.iterrows()]
        
        # 计算相关性
        correlation = clean_data[field1].corr(clean_data[field2])
        
        return {
            'type': 'scatter',
            'title': f'{field1} vs {field2} 相关性',
            'data': chart_data,
            'subtitle': f'{field1} 和 {field2} 的相关性为 {correlation:.3f}，显示了两者间的关联性'
        }
    except Exception as e:
        return None

def create_trend_chart(df, time_field, num_field):
    """创建时间趋势图"""
    try:
        # 处理时间数据
        time_data = df[[time_field, num_field]].copy()
        time_data[time_field] = pd.to_datetime(time_data[time_field], errors='coerce')
        time_data = time_data.dropna()
        
        if len(time_data) < 3:  # 数据太少
            return None
            
        # 按时间排序并聚合
        time_data = time_data.sort_values(time_field)
        
        # 按天或月聚合（根据数据量决定）
        if len(time_data) > 50:
            # 数据较多，按月聚合
            grouped = time_data.groupby(time_data[time_field].dt.to_period('M'))[num_field].sum()
        else:
            # 数据较少，按天聚合
            grouped = time_data.groupby(time_data[time_field].dt.date)[num_field].sum()
        
        chart_data = [float(value) for value in grouped.values]
        
        return {
            'type': 'line',
            'title': f'{num_field} 时间趋势',
            'data': chart_data,
            'subtitle': f'{num_field} 随时间的变化趋势，共 {len(chart_data)} 个时间点'
        }
    except Exception as e:
        return None

def extract_chart_recommendations_from_ai(ai_insights, columns):
    """从 AI 分析结果中提取可视化推荐"""
    recommendations = []
    
    if not ai_insights or not isinstance(ai_insights, str):
        return recommendations
    
    # 尝试从 AI 回复中解析可视化推荐
    lines = ai_insights.split('\n')
    current_recommendation = {}
    in_chart_section = False
    
    for line in lines:
        line = line.strip()
        
        # 检测可视化推荐区域
        if '智能可视化推荐' in line or '推荐图表' in line:
            in_chart_section = True
            continue
            
        if not in_chart_section:
            continue
            
        # 检测新的推荐项
        if '推荐图表' in line and '：' in line:
            if current_recommendation:
                recommendations.append(current_recommendation)
            current_recommendation = {
                'type': extract_chart_type_from_line(line),
                'title': line.split('：')[1].strip() if '：' in line else ''
            }
        
        # 提取字段信息
        elif '维度字段' in line and current_recommendation:
            current_recommendation['dimension_field'] = extract_field_from_line(line, columns)
        elif '度量字段' in line and current_recommendation:
            current_recommendation['measure_field'] = extract_field_from_line(line, columns)
        elif '推荐理由' in line and current_recommendation:
            current_recommendation['reason'] = line.split('：')[1].strip() if '：' in line else ''
        elif '预期洞察' in line and current_recommendation:
            current_recommendation['insight'] = line.split('：')[1].strip() if '：' in line else ''
    
    # 添加最后一个推荐
    if current_recommendation:
        recommendations.append(current_recommendation)
    
    return recommendations

def extract_chart_type_from_line(line):
    """从文本行中提取图表类型"""
    line_lower = line.lower()
    if '柱状图' in line or 'bar' in line_lower:
        return 'bar'
    elif '饼图' in line or 'pie' in line_lower:
        return 'pie'
    elif '折线图' in line or 'line' in line_lower:
        return 'line'
    elif '散点图' in line or 'scatter' in line_lower:
        return 'scatter'
    elif '热力图' in line or 'heatmap' in line_lower:
        return 'heatmap'
    else:
        return 'bar'  # 默认类型

def extract_field_from_line(line, columns):
    """从文本行中提取字段名"""
    if '：' in line:
        field_part = line.split('：')[1].strip()
        # 查找匹配的字段名
        for col in columns:
            if col in field_part:
                return col
    return None

def generate_default_chart_recommendations(df, basic_stats_overview):
    """生成默认的图表推荐"""
    recommendations = []
    
    # 检测数值字段和分类字段
    numeric_fields = []
    categorical_fields = []
    
    for col in df.columns:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue
            
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_fields.append(col)
        else:
            unique_ratio = len(col_data.unique()) / len(col_data)
            if unique_ratio < 0.5 and len(col_data.unique()) < 20:
                categorical_fields.append(col)
    
    # 推荐 1：柱状图（分类 × 数值）
    if categorical_fields and numeric_fields:
        recommendations.append({
            'type': 'bar',
            'title': f'{categorical_fields[0]} {numeric_fields[0]} 排行榜',
            'dimension_field': categorical_fields[0],
            'measure_field': numeric_fields[0],
            'reason': '数据包含分类和数值字段，适合做排名对比',
            'insight': f'能够明确显示不同{categorical_fields[0]}在{numeric_fields[0]}上的表现差异'
        })
    
    # 推荐 2：饼图（分类字段的分布）
    if categorical_fields:
        recommendations.append({
            'type': 'pie',
            'title': f'{categorical_fields[0]} 分布占比',
            'dimension_field': categorical_fields[0],
            'measure_field': None,
            'reason': f'{categorical_fields[0]} 字段分类明确，适合显示占比分布',
            'insight': f'可以直观显示各{categorical_fields[0]}的市场份额或分布情况'
        })
    
    # 推荐 3：散点图（数值字段间的相关性）
    if len(numeric_fields) >= 2:
        recommendations.append({
            'type': 'scatter',
            'title': f'{numeric_fields[0]} vs {numeric_fields[1]} 相关性',
            'dimension_field': numeric_fields[0],
            'measure_field': numeric_fields[1],
            'reason': '多个数值字段间可能存在相关关系',
            'insight': f'能够发现{numeric_fields[0]}和{numeric_fields[1]}之间的潜在关联性'
        })
    
    return recommendations

def create_chart_from_recommendation(df, recommendation):
    """根据推荐创建实际图表数据"""
    try:
        chart_type = recommendation.get('type', 'bar')
        dimension_field = recommendation.get('dimension_field')
        measure_field = recommendation.get('measure_field')
        title = recommendation.get('title', '数据图表')
        
        if chart_type == 'bar' and dimension_field and measure_field:
            # 柱状图：按维度字段分组，求和度量字段
            grouped = df.groupby(dimension_field)[measure_field].sum().sort_values(ascending=False)
            chart_data = [{'name': str(name), 'value': float(value)} for name, value in grouped.head(10).items()]
            
        elif chart_type == 'pie' and dimension_field:
            # 饼图：显示维度字段的分布
            if measure_field:
                grouped = df.groupby(dimension_field)[measure_field].sum().sort_values(ascending=False)
            else:
                grouped = df[dimension_field].value_counts()
            
            total = grouped.sum()
            chart_data = []
            for name, value in grouped.head(8).items():
                percentage = (value / total * 100) if total > 0 else 0
                chart_data.append({'name': str(name), 'value': round(percentage, 1)})
                
        elif chart_type == 'scatter' and dimension_field and measure_field:
            # 散点图：两个数值字段的相关性
            clean_data = df[[dimension_field, measure_field]].dropna()
            chart_data = [[float(row[dimension_field]), float(row[measure_field])] 
                         for _, row in clean_data.head(100).iterrows()]
                         
        elif chart_type == 'line' and dimension_field and measure_field:
            # 折线图：时间趋势或有序列数据
            grouped = df.groupby(dimension_field)[measure_field].sum().sort_index()
            chart_data = [float(value) for value in grouped.values]
            
        else:
            return None
        
        return {
            'type': chart_type,
            'title': title,
            'data': chart_data,
            'subtitle': recommendation.get('insight', f'{title} 提供了重要的数据洞察'),
            'dimension_field': dimension_field,
            'measure_field': measure_field
        }
        
    except Exception as e:
        print(f"创建图表失败: {e}")
        return None

def generate_fallback_charts(df, basic_stats_overview):
    """备用图表生成方案"""
    charts = []
    
    # 简化的图表生成（基于实际数据特点）
    for field, ranking in basic_stats_overview.get('top_rankings', {}).items():
        if ranking and len(ranking['top_5']) > 1:
            chart_data = [{'name': name, 'value': count} for name, count in list(ranking['top_5'].items())[:8]]
            charts.append({
                'type': 'bar', 
                'title': f'{field} 分布', 
                'data': chart_data,
                'subtitle': f'{field} 的分布情况一目了然'
            })
            break  # 只生成一个最有代表性的图表
    
    return charts

def sanitize_for_json(obj):
    """递归将对象中的numpy/pandas类型转为原生Python，确保可JSON序列化"""
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    try:
        return safe_convert_value(obj)
    except Exception:
        try:
            return json.loads(json.dumps(obj, default=str))
        except Exception:
            return str(obj)

def generate_basic_stats_overview(df, key_fields, business_scenario):
    """生成基础统计概览，由浅入深的第一步"""
    overview = {
        "data_scale": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "business_scenario": business_scenario
        },
        "field_summary": {},
        "basic_aggregations": {},
        "top_rankings": {},
        "data_quality": {}
    }
    
    # 字段基础统计
    for col in df.columns:
        col_data = df[col]
        field_type = detect_data_type(col_data)  # 直接检测字段类型
        
        stats = {
            "type": field_type,
            "non_null_count": col_data.count(),
            "null_count": col_data.isnull().sum(),
            "null_percentage": round(col_data.isnull().sum() / len(df) * 100, 2)
        }
        
        if field_type == 'numeric':
            stats.update({
                "mean": round(col_data.mean(), 2) if not col_data.empty else None,
                "median": round(col_data.median(), 2) if not col_data.empty else None,
                "min": col_data.min() if not col_data.empty else None,
                "max": col_data.max() if not col_data.empty else None,
                "std": round(col_data.std(), 2) if not col_data.empty else None,
                "unique_count": col_data.nunique()
            })
        elif field_type in ['categorical', 'text']:
            stats.update({
                "unique_count": col_data.nunique(),
                "most_frequent": col_data.mode().iloc[0] if not col_data.mode().empty else None,
                "most_frequent_count": col_data.value_counts().iloc[0] if not col_data.value_counts().empty else 0
            })
        else:
            stats.update({
                "unique_count": col_data.nunique()
            })
        
        overview["field_summary"][col] = stats
    
    # 基础聚合统计（Excel常用函数）
    numeric_fields = [col for col, info in overview["field_summary"].items() if info["type"] == "numeric"]
    categorical_fields = [col for col, info in overview["field_summary"].items() if info["type"] == "categorical"]
    
    # 数值字段聚合
    for col in numeric_fields:
        col_data = df[col].dropna()
        if not col_data.empty:
            overview["basic_aggregations"][f"{col}_sum"] = round(col_data.sum(), 2)
            overview["basic_aggregations"][f"{col}_avg"] = round(col_data.mean(), 2)
            overview["basic_aggregations"][f"{col}_max"] = col_data.max()
            overview["basic_aggregations"][f"{col}_min"] = col_data.min()
    
    # 分类字段TOP排名
    for col in categorical_fields:
        col_data = df[col].dropna()
        if not col_data.empty:
            value_counts = col_data.value_counts()
            overview["top_rankings"][col] = {
                "top_5": value_counts.head(5).to_dict(),
                "total_unique": col_data.nunique(),
                "most_common": value_counts.index[0] if len(value_counts) > 0 else None,
                "most_common_count": value_counts.iloc[0] if len(value_counts) > 0 else 0
            }
    
    # 数据质量检查
    overview["data_quality"] = {
        "missing_data_fields": [col for col, info in overview["field_summary"].items() if info["null_count"] > 0],
        "duplicate_rows": len(df) - len(df.drop_duplicates()),
        "potential_issues": []
    }
    
    # 检查潜在问题
    for col in categorical_fields:
        col_data = df[col].dropna()
        if not col_data.empty:
            # 检查是否有相似但不完全相同的值（如"联想"和"联想(Lenovo)"）
            unique_values = col_data.unique()
            similar_groups = []
            for val in unique_values:
                if isinstance(val, str):
                    # 简单的相似性检查
                    similar = [v for v in unique_values if isinstance(v, str) and 
                             (val in v or v in val) and val != v]
                    if similar:
                        similar_groups.append({"base": val, "similar": similar})
            
            if similar_groups:
                overview["data_quality"]["potential_issues"].append({
                    "field": col,
                    "issue": "可能存在重复或相似的值",
                    "examples": similar_groups[:3]  # 只显示前3个例子
                })
    
    return overview

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
    if len(non_null_series) > 0:
        unique_ratio = len(non_null_series.unique()) / len(non_null_series)
        unique_count = len(non_null_series.unique())
        
        # 如果唯一值比例低且类别数不多，认为是分类数据
        if unique_ratio < 0.5 and unique_count < 20:
            return 'categorical'
    
    return 'text'

def read_excel_file(filepath):
    """读取Excel文件并返回所有工作表信息"""
    try:
        if not os.path.exists(filepath):
            raise Exception(f"文件不存在: {filepath}")
        
        # 读取所有工作表名称
        excel_file = pd.ExcelFile(filepath)
        sheets_info = {}
        
        for sheet_name in excel_file.sheet_names:
            # 读取工作表数据
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            
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
                            sample_values.append(safe_convert_value(val))
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
            
            # 生成数据预览（前5行）
            try:
                preview_data = []
                for _, row in df.head(5).iterrows():
                    row_dict = {}
                    for col, val in row.items():
                        row_dict[str(col)] = safe_convert_value(val)
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
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 读取并分析Excel文件
            sheets_data = read_excel_file(filepath)
            
            # 选择第一个工作表进行预览分析
            first_sheet = list(sheets_data.keys())[0] 
            first_sheet_data = sheets_data[first_sheet]
            
            # 创建DataFrame进行分析
            df = pd.read_excel(filepath, sheet_name=first_sheet)
            columns_info = first_sheet_data['columns']
            
            # 使用我们的Excel分析引擎
            business_scenario = detect_business_scenario(df, columns_info)
            key_fields = identify_key_fields(df, columns_info)
            basic_analysis = perform_excel_basic_analysis(df, key_fields)
            
            # 生成实用洞察
            practical_insights = generate_practical_insights(df, key_fields, basic_analysis, business_scenario)
            
            # 生成分析建议
            analysis_suggestions = []
            if key_fields["数值字段"] and key_fields["分类字段"]:
                analysis_suggestions.append(f"📊 {key_fields['分类字段'][0]} × {key_fields['数值字段'][0]} 排行榜分析")
            if len(key_fields["分类字段"]) >= 2:
                analysis_suggestions.append(f"🔍 {key_fields['分类字段'][0]} vs {key_fields['分类字段'][1]} 对比分析")
            if key_fields["时间字段"]:
                analysis_suggestions.append(f"📈 {key_fields['时间字段'][0]} 时间趋势分析")
            
            data_preview = {
                "business_scenario": business_scenario,
                "key_fields": key_fields,
                "preview_insights": practical_insights,
                "suggested_analysis": analysis_suggestions,
                "basic_analysis": basic_analysis
            }
            
            return jsonify(sanitize_for_json({
                "filename": filename,
                "sheets_data": sheets_data,
                "data_preview": data_preview
            }))
        else:
            return jsonify({'error': '不支持的文件格式'}), 400
            
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """数据分析接口 - 简化版本"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        selected_columns = data.get('selected_columns', [])
        analysis_level = data.get('analysis_level', '概览')
        custom_requirements = data.get('custom_requirements', '')
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 400
        
        df = pd.read_excel(filepath, sheet_name=sheet_name or 0)
        if selected_columns:
            df = df[selected_columns]
        
        # 使用原有分析引擎避免复杂性
        # 使用新的增强版分析系统
        analysis_result = enhanced_analyze_data(df, custom_requirements)
        
        return jsonify(analysis_result)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"分析失败详细错误: {error_details}")
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@app.route('/api/analyze_legacy', methods=['POST'])
def analyze_data_legacy():
    """数据分析接口"""
    try:
        data = request.get_json()
        
        # 获取分析参数
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        selected_columns = data.get('selected_columns', [])
        analysis_level = data.get('analysis_level', '概览')  # 概览/细分/深度
        ai_mode = data.get('ai_mode', 'hybrid')  # hybrid | gemini_only | local_only
        custom_requirements = data.get('custom_requirements', '')
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        # 读取文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 400
        
        # 读取指定工作表
        df = pd.read_excel(filepath, sheet_name=sheet_name or 0)
        
        # 如果指定了列，则只使用这些列
        if selected_columns:
            df = df[selected_columns]
        
        # 生成列信息
        columns_info = {}
        for col in df.columns:
            try:
                col_series = pd.Series(df[col])
                data_type = detect_data_type(col_series)
                columns_info[str(col)] = {
                    'type': data_type,
                    'non_null_count': int(col_series.count()),
                    'total_count': len(col_series)
                }
            except Exception:
                columns_info[str(col)] = {
                    'type': 'error',
                    'non_null_count': 0,
                    'total_count': len(df)
                }

        # 使用Excel分析引擎
        business_scenario = detect_business_scenario(df, columns_info)
        key_fields = identify_key_fields(df, columns_info)
        
        # 执行基础分析
        basic_analysis = perform_excel_basic_analysis(df, key_fields)
        
        # 执行多维度分析
        dimensional_analysis = perform_multi_dimensional_analysis(df, key_fields, analysis_level)
        
        # 生成实用洞察
        practical_insights = generate_practical_insights(df, key_fields, basic_analysis, business_scenario)
        
        # 生成图表数据（本地分析默认集）
        charts = []
        
        # 柱状图：排行榜数据
        if "排行榜" in basic_analysis and basic_analysis["排行榜"]:
            for rank_name, rank_data in basic_analysis["排行榜"].items():
                if rank_data:
                    chart_data = []
                    for name, info in list(rank_data.items())[:8]:  # 最多8个条目
                        chart_data.append({
                            "name": name,
                            "value": info["总计"]
                        })
                    
                    charts.append({
                        "type": "bar",
                        "title": rank_name,
                        "data": chart_data,
                        "subtitle": f"Top {len(chart_data)} 排行榜"
                    })
                break  # 只生成第一个排行榜图表
        
        # 饼图：分布数据
        if "分组统计" in basic_analysis and basic_analysis["分组统计"]:
            for group_name, group_data in basic_analysis["分组统计"].items():
                if group_data:
                    chart_data = []
                    for name, count in list(group_data.items())[:6]:  # 最多6个分类
                        chart_data.append({
                            "name": name,
                            "value": count
                        })
                    
                    charts.append({
                        "type": "pie",
                        "title": group_name.replace("分布", "占比分布"),
                        "data": chart_data,
                        "subtitle": f"共{len(group_data)}个类别"
                    })
                break  # 只生成第一个分布图表

        # 折线图：时间趋势（若存在时间字段 + 数值字段）
        try:
            if key_fields.get("时间字段") and key_fields.get("数值字段"):
                time_col = key_fields["时间字段"][0]
                num_col = key_fields["数值字段"][0]
                df_time = df[[time_col, num_col]].dropna().copy()
                # 规范为日期
                df_time[time_col] = pd.to_datetime(df_time[time_col], errors='coerce')
                df_time = df_time.dropna(subset=[time_col])
                if len(df_time) > 1:
                    # 按天聚合求和（Excel常见做法）
                    ts = df_time.groupby(df_time[time_col].dt.to_period('D'))[num_col].sum()
                    ts = ts.sort_index()
                    line_data = [float(v) for v in ts.values.tolist()]
                    charts.append({
                        "type": "line",
                        "title": f"{num_col} 时间趋势",
                        "data": line_data,
                        "column": num_col
                    })
        except Exception as _e:
            pass

        # 只保留核心业务分析图表，移除复杂的统计图表
        
        # 生成基础统计概览（由浅入深的第一步）
        basic_stats_overview = generate_basic_stats_overview(df, key_fields, business_scenario)
        
        # 简化的Gemini调用（基于您的示例）
        def analyze_excel(columns, data_sample=None):
            """
            调用 Gemini 模型，基于 Excel 字段做多维度分析 & 可视化思路
            """
            columns_str = ', '.join(columns)
            
            # 简洁的分析结果prompt，不要分析过程
            data_sample_text = f"数据样例：\n{data_sample}" if data_sample else ""
            
            prompt = f"""
            请对以下数据进行专业分析，直接给出分析结果和结论，不要描述分析过程。
            
            数据字段：{columns_str}
            {data_sample_text}
            
            要求：
            1. 直接给出关键发现，不要说"我将分析"、"首先"等过程描述
            2. 只要结果和结论，如"ThinkPad销量最高1000台"而不是"可以分析销量排行"
            3. 给出3-5个最重要的业务洞察
            4. 给出2-3个具体建议
            5. 简洁明了，避免冗长描述
            
            请按以下格式回答：
            
            ## 关键发现
            - [具体发现1]
            - [具体发现2]
            - [具体发现3]
            
            ## 业务建议
            - [具体建议1]
            - [具体建议2]
            """
            
            body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ]
            }
            
            try:
                response = requests.post(API_URL, headers=headers, json=body, timeout=30)
                response.raise_for_status()
                result = response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                return f"AI分析服务暂时不可用：{str(e)}"
        
        # 调用简化的Gemini分析
        ai_insights = ""
        ai_called = False
        ai_error = None
        
        try:
            if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
                columns_list = list(df.columns)
                data_sample = df.head(3).to_dict('records') if len(df) > 0 else None
                ai_insights = analyze_excel(columns_list, str(data_sample)[:500] if data_sample else None)
                ai_called = True
            else:
                ai_error = "未配置GEMINI_API_KEY环境变量"
        except Exception as e:
            ai_error = str(e)
            ai_insights = "AI分析服务暂时不可用。"

        # 简化的结果返回，直接返回本地分析 + AI洞察
        # 移除复杂的模式切换逻辑，符合用户直接调用的偏好
        return jsonify(sanitize_for_json({
            "status": "success",
            "analysis_type": f"excel_analysis_{analysis_level}",
            "business_scenario": business_scenario,
            "basic_stats_overview": basic_stats_overview,
            "data_overview": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "key_fields": key_fields,
                "missing_data": {col: df[col].isnull().sum() for col in df.columns if df[col].isnull().sum() > 0}
            },
            "basic_analysis": basic_analysis,
            "dimensional_analysis": dimensional_analysis,
            "practical_insights": practical_insights,
            "ai_insights": ai_insights,
            "charts": charts,
            "recommendations": [
                f"💡 这是{business_scenario}数据，建议重点关注{key_fields['数值字段'][0] if key_fields['数值字段'] else '核心指标'}",
                f"📊 可以按{key_fields['分类字段'][0] if key_fields['分类字段'] else '主要维度'}进行分组分析",
                f"🔍 建议深入分析{analysis_level}级别的数据特征"
            ],
            "ai_called": ai_called,
            "ai_error": ai_error
        }))
        
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查Gemini配置（环境变量存在即视为已配置）
        gemini_status = "configured" if os.environ.get("GEMINI_API_KEY") else "not_configured"
        
        return jsonify({
            "status": "healthy",
            "backend": "Excel优化版",
            "analysis_engine": "Excel分析引擎",
            "gemini_service": gemini_status
        })
    except:
        return jsonify({
            "status": "error",
            "backend": "Excel优化版"
        }), 503

if __name__ == '__main__':
    print("🚀 启动Excel数据分析助手（优化版）...")
    print("📊 专注于实用的Excel级别业务分析")
    print("🎯 智能识别业务场景，提供针对性洞察") 
    print("💡 多维度多颗粒度分析框架")
    print("🔗 集成Gemini AI增强分析")
    print("---" * 20)
    app.run(debug=True, port=5001)  # 使用5001端口避免冲突
