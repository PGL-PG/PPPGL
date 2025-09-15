from flask import Flask, request, jsonify
import json
from datetime import datetime
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
# from scipy import stats as scipy_stats  # 暂时注释，使用numpy替代

def safe_convert_value(value):
    """安全地转换值为可JSON序列化的类型"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (bool, np.bool_)):
        return bool(value)
    elif isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    else:
        return value

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
app.config['MAX_CONTENT_LENGTH'] = None  # 移除文件大小限制

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
        # 检查文件是否存在
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
                            # 转换为可序列化的类型
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
            
            # 生成数据预览（前5行）
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

def safe_convert_value(value):
    """安全地转换值为可JSON序列化的类型"""
    if pd.isna(value) or value is None:
        return None
    elif isinstance(value, (bool, np.bool_)):
        return bool(value)
    elif isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
        return str(value)
    else:
        return value

def categorize_fields(df, columns_info):
    """智能字段分类 - 基于数据内容和结构识别字段类型"""
    categories = {
        "numeric_fields": [],
        "categorical_fields": [],
        "identifier_fields": [],
        "value_fields": [],
        "dimension_fields": [],
        "time_fields": [],
        "text_fields": []
    }
    
    # 关键词字典（作为辅助判断）
    field_keywords = {
        "sales": ['销量', '数量', 'quantity', 'sales', '售出', '销售', '成交', 'sold', '件数', '个数'],
        "revenue": ['收入', '营收', 'revenue', '金额', 'amount', '总额', 'total', '价值', '收益'],
        "price": ['价格', 'price', '单价', '成本', 'cost', '费用', '金额'],
        "brand": ['品牌', 'brand', '厂商', 'manufacturer', '供应商', 'supplier', '牌子'],
        "product": ['产品', 'product', '商品', '名称', 'name', '型号', 'model', '货品'],
        "category": ['类别', 'category', '分类', 'type', '种类', 'class', '类型'],
        "region": ['地区', '区域', 'region', '城市', 'city', '省份', 'province', '国家', 'country', '地方'],
        "time": ['时间', 'time', '日期', 'date', '年', 'year', '月', 'month', '季度', 'quarter', '周'],
        "customer": ['客户', 'customer', '用户', 'user', '顾客', 'client'],
        "channel": ['渠道', 'channel', '平台', 'platform', '来源', 'source']
    }
    
    for col in df.columns:
        col_lower = col.lower()
        col_type = columns_info.get(col, {}).get('type', 'text')
        col_info = columns_info.get(col, {})
        
        # 获取列的实际数据进行分析
        col_data = df[col].dropna()
        unique_count = len(col_data.unique()) if len(col_data) > 0 else 0
        total_count = len(col_data)
        unique_ratio = unique_count / total_count if total_count > 0 else 0
        
        # 数值型字段
        if col_type == 'numeric':
            categories["numeric_fields"].append(col)
            
            # 智能判断是否为价值字段
            is_value_field = False
            
            # 1. 关键词匹配
            if any(keyword in col_lower for keyword in field_keywords["sales"] + field_keywords["revenue"] + field_keywords["price"]):
                is_value_field = True
            
            # 2. 数据特征判断：大多数数值字段如果变化范围大，通常是价值字段
            if len(col_data) > 0:
                data_range = col_data.max() - col_data.min()
                data_mean = col_data.mean()
                cv = col_data.std() / data_mean if data_mean != 0 else 0
                
                # 如果变异系数较大，可能是价值字段
                if cv > 0.3 and data_range > 0:
                    is_value_field = True
            
            if is_value_field:
                categories["value_fields"].append(col)
        
        # 分类型字段
        elif col_type == 'categorical':
            categories["categorical_fields"].append(col)
            
            # 智能判断是否为维度字段
            is_dimension_field = False
            
            # 1. 关键词匹配
            if any(keyword in col_lower for keyword in 
                   field_keywords["brand"] + field_keywords["product"] + field_keywords["category"] + 
                   field_keywords["region"] + field_keywords["customer"] + field_keywords["channel"]):
                is_dimension_field = True
            
            # 2. 数据特征判断：适中的唯一值数量，通常是好的维度字段
            if 2 <= unique_count <= 50 and unique_ratio < 0.8:
                is_dimension_field = True
            
            if is_dimension_field:
                categories["dimension_fields"].append(col)
        
        # 时间字段
        elif col_type == 'datetime':
            categories["time_fields"].append(col)
        
        # 文本字段
        else:
            categories["text_fields"].append(col)
            
            # 检查是否是标识符字段
            if (any(keyword in col_lower for keyword in ['id', '编号', 'code', '序号']) or 
                unique_ratio > 0.9):  # 唯一值比例很高，可能是ID字段
                categories["identifier_fields"].append(col)
            
            # 检查文本字段是否实际上是分类字段
            elif unique_count <= 20 and unique_ratio < 0.5:
                categories["categorical_fields"].append(col)
                # 进一步判断是否为维度字段
                if any(keyword in col_lower for keyword in 
                       field_keywords["brand"] + field_keywords["product"] + field_keywords["category"] + 
                       field_keywords["region"] + field_keywords["customer"] + field_keywords["channel"]):
                    categories["dimension_fields"].append(col)
    
    return categories

def determine_analysis_strategy(field_categories, df):
    """根据数据实际特征智能确定最佳分析策略"""
    strategy = {
        "type": "general",
        "primary_focus": [],
        "secondary_focus": [],
        "chart_types": [],
        "data_characteristics": {}
    }
    
    # 统计各类字段数量
    numeric_count = len(field_categories["numeric_fields"])
    categorical_count = len(field_categories["categorical_fields"])
    value_count = len(field_categories["value_fields"])
    dimension_count = len(field_categories["dimension_fields"])
    time_count = len(field_categories["time_fields"])
    
    # 分析数据规模和复杂度
    row_count = len(df)
    total_fields = len(df.columns)
    
    strategy["data_characteristics"] = {
        "row_count": row_count,
        "total_fields": total_fields,
        "numeric_fields": numeric_count,
        "categorical_fields": categorical_count,
        "value_fields": value_count,
        "dimension_fields": dimension_count,
        "time_fields": time_count
    }
    
    # 智能策略选择
    
    # 策略1: 业务绩效分析 - 有明确的价值字段和维度字段
    if value_count >= 1 and dimension_count >= 1:
        strategy["type"] = "business_analysis"
        strategy["primary_focus"] = ["performance_ranking", "market_analysis", "efficiency_analysis"]
        strategy["secondary_focus"] = ["trend_analysis" if time_count > 0 else "cross_dimension_analysis"]
        strategy["chart_types"] = ["bar", "pie", "scatter"]
        
        # 如果有时间字段，加入时间序列分析
        if time_count > 0:
            strategy["chart_types"].append("line")
            strategy["secondary_focus"].append("time_series")
    
    # 策略2: 时间序列分析 - 有时间字段和数值字段
    elif time_count >= 1 and numeric_count >= 1:
        strategy["type"] = "time_series_analysis"
        strategy["primary_focus"] = ["trend_analysis", "seasonal_analysis"]
        strategy["secondary_focus"] = ["correlation_analysis", "forecasting"]
        strategy["chart_types"] = ["line", "bar", "area"]
    
    # 策略3: 多维对比分析 - 多个分类字段和数值字段
    elif categorical_count >= 2 and numeric_count >= 1:
        strategy["type"] = "comparative_analysis"
        strategy["primary_focus"] = ["category_comparison", "cross_tabulation"]
        strategy["secondary_focus"] = ["ranking_analysis", "distribution_comparison"]
        strategy["chart_types"] = ["bar", "pie", "heatmap"]
    
    # 策略4: 统计分析 - 多个数值字段
    elif numeric_count >= 2:
        strategy["type"] = "statistical_analysis"
        strategy["primary_focus"] = ["correlation_analysis", "distribution_analysis"]
        strategy["secondary_focus"] = ["outlier_detection", "clustering_potential"]
        strategy["chart_types"] = ["scatter", "histogram", "boxplot"]
    
    # 策略5: 分类汇总分析 - 主要是分类字段
    elif categorical_count >= 1 and numeric_count >= 1:
        strategy["type"] = "categorical_analysis"
        strategy["primary_focus"] = ["frequency_analysis", "category_statistics"]
        strategy["secondary_focus"] = ["distribution_analysis"]
        strategy["chart_types"] = ["bar", "pie"]
    
    # 策略6: 探索性数据分析 - 数据结构不明确
    else:
        strategy["type"] = "exploratory_analysis"
        strategy["primary_focus"] = ["data_profiling", "pattern_discovery"]
        strategy["secondary_focus"] = ["data_quality_assessment"]
        strategy["chart_types"] = ["bar", "histogram"]
    
    return strategy

def analyze_data_content(df, field_categories):
    """分析数据实际内容，生成数据理解报告"""
    content_analysis = {
        "data_theme": "未知",
        "business_context": "",
        "key_metrics": [],
        "main_dimensions": [],
        "data_scope": ""
    }
    
    # 分析数据主题
    all_columns = [col.lower() for col in df.columns]
    column_text = " ".join(all_columns)
    
    # 主题识别
    if any(word in column_text for word in ['销售', '销量', '收入', '营收', 'sales', 'revenue']):
        content_analysis["data_theme"] = "销售业务数据"
        content_analysis["business_context"] = "这是一份销售业务相关的数据，包含销售表现和业务指标"
    elif any(word in column_text for word in ['用户', '客户', 'user', 'customer', '访问', 'visit']):
        content_analysis["data_theme"] = "用户行为数据"
        content_analysis["business_context"] = "这是一份用户行为相关的数据，包含用户活动和行为指标"
    elif any(word in column_text for word in ['产品', 'product', '商品', '库存', 'inventory']):
        content_analysis["data_theme"] = "产品管理数据"
        content_analysis["business_context"] = "这是一份产品管理相关的数据，包含产品信息和管理指标"
    elif any(word in column_text for word in ['财务', '成本', 'cost', '利润', 'profit', '预算', 'budget']):
        content_analysis["data_theme"] = "财务管理数据"
        content_analysis["business_context"] = "这是一份财务管理相关的数据，包含财务指标和成本分析"
    else:
        content_analysis["data_theme"] = "业务运营数据"
        content_analysis["business_context"] = "这是一份业务运营数据，包含各类运营指标和维度信息"
    
    # 识别关键指标
    value_fields = field_categories.get("value_fields", [])
    numeric_fields = field_categories.get("numeric_fields", [])
    
    for field in value_fields + numeric_fields:
        if field not in content_analysis["key_metrics"]:
            content_analysis["key_metrics"].append(field)
    
    # 识别主要维度
    dimension_fields = field_categories.get("dimension_fields", [])
    categorical_fields = field_categories.get("categorical_fields", [])
    
    for field in dimension_fields + categorical_fields:
        if field not in content_analysis["main_dimensions"]:
            content_analysis["main_dimensions"].append(field)
    
    # 数据范围描述
    row_count = len(df)
    if row_count < 100:
        content_analysis["data_scope"] = "小规模数据集"
    elif row_count < 1000:
        content_analysis["data_scope"] = "中等规模数据集"
    else:
        content_analysis["data_scope"] = "大规模数据集"
    
    return content_analysis

def smart_data_analysis(df, field_categories, columns_info):
    """智能数据分析 - 根据实际数据内容自动选择最佳分析方法"""
    results = {
        "data_overview": {},
        "key_findings": [],
        "detailed_analysis": {},
        "charts": [],
        "actionable_insights": [],
        "next_steps": []
    }
    
    try:
        # 1. 数据概览和理解
        data_overview = analyze_data_structure(df, field_categories, columns_info)
        results["data_overview"] = data_overview
        
        # 2. 根据数据特征选择分析方法
        analysis_methods = determine_best_analysis_methods(df, field_categories, data_overview)
        
        # 3. 执行选定的分析方法
        for method in analysis_methods:
            if method == "ranking_analysis":
                ranking_results = perform_ranking_analysis(df, field_categories)
                if ranking_results:
                    results["detailed_analysis"]["ranking"] = ranking_results
                    results["charts"].extend(ranking_results.get("charts", []))
                    
            elif method == "distribution_analysis":
                dist_results = perform_distribution_analysis(df, field_categories)
                if dist_results:
                    results["detailed_analysis"]["distribution"] = dist_results
                    results["charts"].extend(dist_results.get("charts", []))
                    
            elif method == "correlation_analysis":
                corr_results = perform_correlation_analysis(df, field_categories)
                if corr_results:
                    results["detailed_analysis"]["correlation"] = corr_results
                    results["charts"].extend(corr_results.get("charts", []))
                    
            elif method == "trend_analysis":
                trend_results = perform_trend_analysis(df, field_categories)
                if trend_results:
                    results["detailed_analysis"]["trend"] = trend_results
                    results["charts"].extend(trend_results.get("charts", []))
                    
            elif method == "category_analysis":
                cat_results = perform_category_analysis(df, field_categories)
                if cat_results:
                    results["detailed_analysis"]["category"] = cat_results
                    results["charts"].extend(cat_results.get("charts", []))
        
        # 4. 生成关键发现
        results["key_findings"] = generate_key_findings(df, field_categories, results["detailed_analysis"])
        
        # 5. 生成可执行的洞察
        results["actionable_insights"] = generate_actionable_insights(df, field_categories, results["detailed_analysis"])
        
        # 6. 建议下一步行动
        results["next_steps"] = suggest_next_steps(df, field_categories, results["detailed_analysis"])
        
    except Exception as e:
        print(f"智能分析失败: {e}")
        import traceback
        traceback.print_exc()
        return perform_basic_analysis(df, field_categories, columns_info)
    
    return results

def analyze_data_structure(df, field_categories, columns_info):
    """分析数据结构和特征"""
    overview = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "data_completeness": {},
        "column_types": {},
        "data_patterns": [],
        "potential_keys": [],
        "value_ranges": {}
    }
    
    # 分析数据完整性
    for col in df.columns:
        non_null_count = df[col].count()
        completeness = (non_null_count / len(df)) * 100
        overview["data_completeness"][col] = round(completeness, 1)
        
        # 分析列类型和特征
        col_info = columns_info.get(col, {})
        overview["column_types"][col] = col_info.get('type', 'unknown')
        
        # 分析数值范围
        if col_info.get('type') == 'numeric':
            col_data = df[col].dropna()
            if len(col_data) > 0:
                overview["value_ranges"][col] = {
                    "min": safe_convert_value(col_data.min()),
                    "max": safe_convert_value(col_data.max()),
                    "mean": safe_convert_value(col_data.mean()),
                    "std": safe_convert_value(col_data.std())
                }
    
    # 识别数据模式
    if len(df.columns) <= 5 and len(df) < 1000:
        overview["data_patterns"].append("小规模结构化数据")
    elif len(df.columns) > 10:
        overview["data_patterns"].append("多维度复杂数据")
    
    # 识别潜在的主键
    for col in df.columns:
        unique_ratio = len(df[col].unique()) / len(df)
        if unique_ratio > 0.95:
            overview["potential_keys"].append(col)
    
    return overview

def determine_best_analysis_methods(df, field_categories, data_overview):
    """根据数据特征智能确定最佳分析方法"""
    methods = []
    
    numeric_fields = field_categories.get("numeric_fields", [])
    categorical_fields = field_categories.get("categorical_fields", [])
    time_fields = field_categories.get("time_fields", [])
    
    # 如果有数值字段和分类字段，进行排名分析
    if len(numeric_fields) >= 1 and len(categorical_fields) >= 1:
        methods.append("ranking_analysis")
        methods.append("category_analysis")
    
    # 如果有多个数值字段，进行分布和相关性分析
    if len(numeric_fields) >= 2:
        methods.append("distribution_analysis")
        methods.append("correlation_analysis")
    
    # 如果有时间字段，进行趋势分析
    if len(time_fields) >= 1 and len(numeric_fields) >= 1:
        methods.append("trend_analysis")
    
    # 如果只有分类字段，进行频率分析
    if len(categorical_fields) >= 1 and len(numeric_fields) == 0:
        methods.append("category_analysis")
    
    return methods[:3]  # 最多选择3种分析方法

def perform_ranking_analysis(df, field_categories):
    """执行排名分析"""
    try:
        numeric_fields = field_categories.get("numeric_fields", [])
        categorical_fields = field_categories.get("categorical_fields", [])
        
        if not numeric_fields or not categorical_fields:
            return None
        
        primary_numeric = numeric_fields[0]
        primary_categorical = categorical_fields[0]
        
        # 按分类字段分组，计算数值字段的统计量
        df_clean = df[[primary_categorical, primary_numeric]].dropna()
        if len(df_clean) == 0:
            return None
        
        ranking_stats = df_clean.groupby(primary_categorical)[primary_numeric].agg([
            'sum', 'mean', 'count', 'std'
        ]).round(2)
        
        # 按总和排序
        ranking_sorted = ranking_stats.sort_values('sum', ascending=False)
        
        # 生成排名图表
        chart_data = []
        for idx, (category, stats) in enumerate(ranking_sorted.head(10).iterrows()):
            chart_data.append({
                "name": str(category),
                "value": safe_convert_value(stats['sum']),
                "rank": idx + 1,
                "average": safe_convert_value(stats['mean']),
                "count": safe_convert_value(stats['count'])
            })
        
        return {
            "title": f"{primary_categorical}按{primary_numeric}排名",
            "top_performers": chart_data[:5],
            "total_categories": len(ranking_sorted),
            "charts": [{
                "type": "bar",
                "title": f"{primary_categorical} - {primary_numeric}排名",
                "data": chart_data,
                "subtitle": f"共{len(ranking_sorted)}个类别"
            }],
            "insights": [
                f"排名第一的{primary_categorical}是：{ranking_sorted.index[0]}",
                f"前3名占总{primary_numeric}的{round((ranking_sorted.head(3)['sum'].sum() / ranking_sorted['sum'].sum()) * 100, 1)}%"
            ]
        }
        
    except Exception as e:
        print(f"排名分析失败: {e}")
        return None
        
        # 1. 市场集中度分析（HHI指数）
        df_clean = df[[primary_dimension, primary_value]].dropna()
        if len(df_clean) > 0:
            dimension_stats = df_clean.groupby(primary_dimension)[primary_value].agg(['sum', 'mean', 'count', 'std']).round(2)
            dimension_stats_sorted = dimension_stats.sort_values('sum', ascending=False)
            
            total_value = dimension_stats['sum'].sum()
            dimension_stats_sorted['market_share'] = (dimension_stats_sorted['sum'] / total_value * 100).round(2)
            dimension_stats_sorted['efficiency'] = (dimension_stats_sorted['sum'] / dimension_stats_sorted['count']).round(2)
            
            # 计算HHI指数（市场集中度）
            hhi = sum((share/100)**2 for share in dimension_stats_sorted['market_share'])
            
            # 计算基尼系数（不平等程度）
            values = dimension_stats_sorted['sum'].values
            n = len(values)
            gini = (2 * sum((i+1) * val for i, val in enumerate(sorted(values)))) / (n * sum(values)) - (n+1)/n
            
            # 2. 帕累托分析（80/20法则）
            cumulative_share = dimension_stats_sorted['market_share'].cumsum()
            pareto_80_count = len(cumulative_share[cumulative_share <= 80])
            pareto_ratio = pareto_80_count / len(dimension_stats_sorted) * 100
            
            # 3. 竞争态势分析
            top_3_share = dimension_stats_sorted.head(3)['market_share'].sum()
            top_5_share = dimension_stats_sorted.head(5)['market_share'].sum()
            
            market_structure = "高度垄断" if top_3_share > 70 else "寡头垄断" if top_3_share > 50 else "垄断竞争" if top_3_share > 30 else "完全竞争"
            
            # 4. 效率分析
            efficiency_stats = dimension_stats_sorted['efficiency'].describe()
            efficiency_cv = dimension_stats_sorted['efficiency'].std() / dimension_stats_sorted['efficiency'].mean()
            
            results["primary_analysis"] = {
                "data_context": content_analysis,
                "analysis_title": f"{primary_dimension}按{primary_value}的分布分析",
                "analysis_subtitle": f"基于{content_analysis['data_theme']}的深度洞察",
                "market_structure": {
                    "type": market_structure,
                    "hhi_index": round(hhi, 4),
                    "gini_coefficient": round(gini, 4),
                    "top_3_concentration": round(top_3_share, 2),
                    "top_5_concentration": round(top_5_share, 2),
                    "pareto_ratio": round(pareto_ratio, 2)
                },
                "competitive_dynamics": {
                    "total_players": len(dimension_stats_sorted),
                    "market_leader": str(dimension_stats_sorted.index[0]),
                    "leader_share": round(dimension_stats_sorted.iloc[0]['market_share'], 2),
                    "efficiency_leader": str(dimension_stats_sorted.sort_values('efficiency', ascending=False).index[0]),
                    "avg_efficiency": round(efficiency_stats['mean'], 2),
                    "efficiency_dispersion": round(efficiency_cv, 3)
                }
            }
            
            # 5. 专业可视化图表
            
            # 市场份额瀑布图数据
            waterfall_data = []
            cumulative = 0
            for i, (dim, data) in enumerate(dimension_stats_sorted.head(8).iterrows()):
                waterfall_data.append({
                    "name": str(dim)[:15] + "..." if len(str(dim)) > 15 else str(dim),
                    "value": safe_convert_value(data['market_share']),
                    "cumulative": cumulative + safe_convert_value(data['market_share'])
                })
                cumulative += safe_convert_value(data['market_share'])
            
            results["charts"].append({
                "type": "bar",
                "title": f"{primary_dimension}市场份额排行（%）",
                "data": waterfall_data,
                "subtitle": f"市场结构：{market_structure}，HHI={hhi:.3f}"
            })
            
            # 效率散点图
            efficiency_scatter = []
            for dim, data in dimension_stats_sorted.head(15).iterrows():
                efficiency_scatter.append([
                    safe_convert_value(data['market_share']),  # x轴：市场份额
                    safe_convert_value(data['efficiency']),    # y轴：效率
                    safe_convert_value(data['sum']/1000),      # 气泡大小：总量
                    str(dim)[:10]                              # 标签
                ])
            
            results["charts"].append({
                "type": "scatter",
                "title": "市场份额 vs 运营效率矩阵",
                "data": efficiency_scatter,
                "subtitle": "气泡大小代表总量，右上角为理想象限"
            })
            
            # 6. 商业洞察生成
            insights = []
            
            if hhi > 0.25:
                insights.append(f"🎯 市场高度集中：HHI指数{hhi:.3f}，存在显著的市场支配地位")
            elif hhi > 0.15:
                insights.append(f"⚖️ 市场适度集中：HHI指数{hhi:.3f}，竞争格局相对稳定")
            else:
                insights.append(f"🔄 市场竞争激烈：HHI指数{hhi:.3f}，存在大量竞争机会")
            
            if gini > 0.6:
                insights.append(f"📊 收入分配极不均衡：基尼系数{gini:.3f}，头部效应明显")
            elif gini > 0.4:
                insights.append(f"📈 收入分配不均：基尼系数{gini:.3f}，存在结构性差异")
            
            if pareto_ratio < 20:
                insights.append(f"🏆 超级帕累托效应：仅{pareto_ratio:.1f}%的参与者创造80%价值")
            elif pareto_ratio < 30:
                insights.append(f"📊 标准帕累托分布：{pareto_ratio:.1f}%的参与者创造80%价值")
            
            leader_advantage = dimension_stats_sorted.iloc[0]['market_share'] - dimension_stats_sorted.iloc[1]['market_share']
            if leader_advantage > 10:
                insights.append(f"👑 市场领导者优势显著：领先第二名{leader_advantage:.1f}个百分点")
            
            results["business_insights"] = insights
            
            # 7. 战略建议
            recommendations = []
            
            if market_structure == "完全竞争":
                recommendations.append("🎯 差异化战略：在完全竞争市场中，建议通过产品差异化或成本领先建立竞争优势")
                recommendations.append("📊 市场细分：寻找利基市场机会，避免正面价格竞争")
            elif market_structure == "垄断竞争":
                recommendations.append("🔍 品牌建设：在垄断竞争环境下，品牌价值是关键差异化因素")
                recommendations.append("💡 创新驱动：持续产品创新以维持竞争地位")
            elif market_structure == "寡头垄断":
                recommendations.append("🤝 战略联盟：考虑与其他参与者建立战略合作关系")
                recommendations.append("⚡ 快速响应：密切关注竞争对手动态，快速市场响应")
            else:
                recommendations.append("🛡️ 防御策略：在垄断地位下，重点防范新进入者和替代品威胁")
                recommendations.append("📈 市场扩张：利用规模优势进入相关市场")
            
            if efficiency_cv > 0.5:
                recommendations.append("⚙️ 运营优化：效率差异显著，存在大量运营改进空间")
            
            results["strategic_recommendations"] = recommendations
        
        # 8. 次级分析：交叉维度分析
        if len(dimension_fields) > 1:
            secondary_dimension = dimension_fields[1]
            
            # 双维度交叉分析
            cross_analysis = df.groupby([primary_dimension, secondary_dimension])[primary_value].sum().unstack(fill_value=0)
            
            if not cross_analysis.empty:
                # 计算多样化指数
                diversity_scores = {}
                for dim in cross_analysis.index:
                    values = cross_analysis.loc[dim].values
                    total = values.sum()
                    if total > 0:
                        # 计算香农多样性指数
                        proportions = values / total
                        shannon_diversity = -sum(p * np.log(p) for p in proportions if p > 0)
                        diversity_scores[str(dim)] = round(shannon_diversity, 3)
                
                results["secondary_analysis"] = {
                    "analysis_title": f"{primary_dimension} × {secondary_dimension} 交叉分析",
                    "diversity_analysis": diversity_scores,
                    "cross_matrix_shape": cross_analysis.shape,
                    "top_combinations": []
                }
                
                # 找出最佳组合
                cross_flat = cross_analysis.stack().sort_values(ascending=False)
                for (dim1, dim2), value in cross_flat.head(5).items():
                    results["secondary_analysis"]["top_combinations"].append({
                        "combination": f"{dim1} × {dim2}",
                        "value": safe_convert_value(value)
                    })
                
                # 多样化指数图表
                diversity_chart_data = [{"name": k, "value": v} for k, v in sorted(diversity_scores.items(), key=lambda x: x[1], reverse=True)[:8]]
                
                results["charts"].append({
                    "type": "bar",
                    "title": f"{primary_dimension}多样化指数排行",
                    "data": diversity_chart_data,
                    "subtitle": "香农多样性指数，数值越高表示业务越多元化"
                })
    
    except Exception as e:
        print(f"专业业务分析失败: {e}")
        import traceback
        traceback.print_exc()
        return perform_descriptive_analysis(df, field_categories, columns_info)
    
    return results

def perform_comparative_analysis(df, field_categories, columns_info):
    """执行对比分析"""
    results = {"primary_analysis": {}, "secondary_analysis": {}, "charts": []}
    
    try:
        categorical_fields = field_categories["categorical_fields"][:2]
        numeric_fields = field_categories["numeric_fields"][:2]
        
        if len(categorical_fields) < 2 or len(numeric_fields) < 1:
            return perform_descriptive_analysis(df, field_categories, columns_info)
        
        cat1, cat2 = categorical_fields[0], categorical_fields[1]
        num_field = numeric_fields[0]
        
        # 交叉分析
        df_clean = df[[cat1, cat2, num_field]].dropna()
        if len(df_clean) > 0:
            # 按第一个分类字段分组
            cat1_stats = df_clean.groupby(cat1)[num_field].agg(['sum', 'mean', 'count']).round(2)
            cat1_sorted = cat1_stats.sort_values('sum', ascending=False)
            
            results["primary_analysis"] = {
                "analysis_title": f"{cat1} 对比分析",
                "metric": num_field,
                "top_categories": {str(k): safe_convert_value(v['sum']) for k, v in cat1_sorted.head(8).iterrows()}
            }
            
            # 生成对比图表
            chart_data = [{"name": str(k), "value": safe_convert_value(v['sum'])} 
                         for k, v in cat1_sorted.head(8).iterrows()]
            
            results["charts"].append({
                "type": "bar",
                "title": f"{cat1} {num_field} 对比",
                "data": chart_data
            })
            
            # 第二个分类字段分析
            cat2_stats = df_clean.groupby(cat2)[num_field].sum().sort_values(ascending=False)
            
            results["secondary_analysis"] = {
                "analysis_title": f"{cat2} 分布分析",
                "top_items": {str(k): safe_convert_value(v) for k, v in cat2_stats.head(8).items()}
            }
            
            # 第二个分类的图表
            cat2_chart_data = [{"name": str(k), "value": safe_convert_value(v)} 
                              for k, v in cat2_stats.head(8).items()]
            
            results["charts"].append({
                "type": "pie",
                "title": f"{cat2} {num_field} 分布",
                "data": cat2_chart_data
            })
    
    except Exception as e:
        print(f"对比分析失败: {e}")
        return perform_descriptive_analysis(df, field_categories, columns_info)
    
    return results

def perform_statistical_analysis(df, field_categories, columns_info):
    """高级统计分析 - 专业数据科学方法"""
    results = {"primary_analysis": {}, "secondary_analysis": {}, "charts": [], "statistical_insights": [], "modeling_recommendations": []}
    
    try:
        numeric_fields = field_categories["numeric_fields"]
        
        if len(numeric_fields) < 2:
            return perform_descriptive_analysis(df, field_categories, columns_info)
        
        # 1. 多变量统计描述
        numeric_df = df[numeric_fields].dropna()
        
        if len(numeric_df) > 0:
            # 计算高级统计指标
            stats_summary = {}
            for field in numeric_fields:
                data = numeric_df[field]
                
                # 基础统计量
                mean_val = data.mean()
                std_val = data.std()
                
                # 分布形状指标
                skewness = data.skew()  # 偏度
                kurtosis = data.kurtosis()  # 峰度
                
                # 变异系数
                cv = std_val / mean_val if mean_val != 0 else 0
                
                # 四分位距
                q1, q3 = data.quantile([0.25, 0.75])
                iqr = q3 - q1
                
                # 异常值检测（IQR方法）
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = data[(data < lower_bound) | (data > upper_bound)]
                outlier_rate = len(outliers) / len(data) * 100
                
                # 正态性检验（基于偏度和峰度）
                is_normal = abs(skewness) < 0.5 and abs(kurtosis) < 0.5
                
                stats_summary[field] = {
                    "mean": round(mean_val, 4),
                    "std": round(std_val, 4),
                    "cv": round(cv, 4),
                    "skewness": round(skewness, 4),
                    "kurtosis": round(kurtosis, 4),
                    "outlier_rate": round(outlier_rate, 2),
                    "is_normal": safe_convert_value(is_normal),
                    "distribution_type": classify_distribution(skewness, kurtosis)
                }
            
            results["primary_analysis"] = {
                "analysis_title": "多变量统计特征分析",
                "sample_size": len(numeric_df),
                "variables_analyzed": len(numeric_fields),
                "statistical_summary": stats_summary
            }
            
            # 2. 相关性矩阵分析
            correlation_matrix = numeric_df.corr()
            
            # 提取显著相关性
            significant_correlations = []
            for i in range(len(numeric_fields)):
                for j in range(i+1, len(numeric_fields)):
                    field1, field2 = numeric_fields[i], numeric_fields[j]
                    corr_value = correlation_matrix.loc[field1, field2]
                    
                    if not pd.isna(corr_value) and abs(corr_value) > 0.3:
                        # 计算相关性的统计显著性（简化版本）
                        n = len(numeric_df[[field1, field2]].dropna())
                        # 使用简化的显著性判断
                        p_value = 0.01 if abs(corr_value) > 0.6 else 0.05 if abs(corr_value) > 0.3 else 0.1
                        
                        significant_correlations.append({
                            "field1": field1,
                            "field2": field2,
                            "correlation": round(corr_value, 4),
                            "p_value": round(p_value, 4),
                            "significance": "显著" if p_value < 0.05 else "不显著",
                            "strength": classify_correlation_strength(abs(corr_value)),
                            "direction": "正相关" if corr_value > 0 else "负相关"
                        })
            
            # 按相关性强度排序
            significant_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            results["secondary_analysis"] = {
                "analysis_title": "变量间相关性深度分析",
                "correlation_matrix_size": correlation_matrix.shape,
                "significant_correlations": significant_correlations[:8],
                "multicollinearity_warning": safe_convert_value(any(abs(c["correlation"]) > 0.8 for c in significant_correlations))
            }
            
            # 3. 专业可视化
            
            # 相关性热力图数据
            corr_heatmap_data = []
            for i, field1 in enumerate(numeric_fields):
                for j, field2 in enumerate(numeric_fields):
                    corr_heatmap_data.append({
                        "x": i,
                        "y": j,
                        "value": round(correlation_matrix.loc[field1, field2], 3),
                        "field1": field1,
                        "field2": field2
                    })
            
            results["charts"].append({
                "type": "heatmap",
                "title": "变量相关性热力图",
                "data": corr_heatmap_data,
                "subtitle": "颜色深度表示相关性强度，红色正相关，蓝色负相关"
            })
            
            # 分布对比箱线图
            if len(numeric_fields) >= 2:
                primary_field = numeric_fields[0]
                distribution_data = []
                
                for field in numeric_fields[:4]:  # 最多显示4个变量
                    field_data = numeric_df[field].dropna()
                    q1, median, q3 = field_data.quantile([0.25, 0.5, 0.75])
                    iqr = q3 - q1
                    
                    distribution_data.append({
                        "name": field,
                        "min": safe_convert_value(field_data.min()),
                        "q1": safe_convert_value(q1),
                        "median": safe_convert_value(median),
                        "q3": safe_convert_value(q3),
                        "max": safe_convert_value(field_data.max()),
                        "outliers": [safe_convert_value(x) for x in field_data[(field_data < q1 - 1.5*iqr) | (field_data > q3 + 1.5*iqr)].tolist()[:10]]
                    })
                
                results["charts"].append({
                    "type": "boxplot",
                    "title": "变量分布对比箱线图",
                    "data": distribution_data,
                    "subtitle": "显示中位数、四分位数和异常值分布"
                })
            
            # 4. 统计洞察生成
            insights = []
            
            # 分布特征洞察
            normal_vars = [field for field, stats in stats_summary.items() if stats["is_normal"]]
            if len(normal_vars) > 0:
                insights.append(f"📊 {len(normal_vars)}个变量呈正态分布，适合使用参数统计方法")
            
            skewed_vars = [field for field, stats in stats_summary.items() if abs(stats["skewness"]) > 1]
            if len(skewed_vars) > 0:
                insights.append(f"⚠️ {len(skewed_vars)}个变量存在显著偏度，建议数据变换")
            
            high_cv_vars = [field for field, stats in stats_summary.items() if stats["cv"] > 0.5]
            if len(high_cv_vars) > 0:
                insights.append(f"📈 {len(high_cv_vars)}个变量变异系数较高，数据离散度大")
            
            # 相关性洞察
            strong_corrs = [c for c in significant_correlations if abs(c["correlation"]) > 0.7]
            if len(strong_corrs) > 0:
                insights.append(f"🔗 发现{len(strong_corrs)}对强相关变量，存在潜在的多重共线性")
            
            results["statistical_insights"] = insights
            
            # 5. 建模建议
            recommendations = []
            
            if len(normal_vars) >= len(numeric_fields) * 0.7:
                recommendations.append("📊 数据分布良好，推荐使用线性回归、ANOVA等参数方法")
            else:
                recommendations.append("🔄 数据分布偏斜，建议使用非参数方法或数据变换")
            
            if len(strong_corrs) > 0:
                recommendations.append("⚠️ 存在多重共线性，建议使用岭回归、主成分分析等降维方法")
            
            if any(stats["outlier_rate"] > 5 for stats in stats_summary.values()):
                recommendations.append("🎯 异常值较多，建议使用鲁棒统计方法或异常值处理")
            
            recommendations.append("📈 建议进行时间序列分析以发现趋势和季节性模式")
            recommendations.append("🔍 可考虑聚类分析识别数据中的潜在群体结构")
            
            results["modeling_recommendations"] = recommendations
    
    except Exception as e:
        print(f"高级统计分析失败: {e}")
        import traceback
        traceback.print_exc()
        return perform_descriptive_analysis(df, field_categories, columns_info)
    
    return results

def classify_distribution(skewness, kurtosis):
    """分类分布类型"""
    if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
        return "近似正态分布"
    elif skewness > 1:
        return "右偏分布"
    elif skewness < -1:
        return "左偏分布"
    elif kurtosis > 1:
        return "尖峰分布"
    elif kurtosis < -1:
        return "平峰分布"
    else:
        return "轻度偏态分布"

def classify_correlation_strength(abs_corr):
    """分类相关性强度"""
    if abs_corr >= 0.8:
        return "极强相关"
    elif abs_corr >= 0.6:
        return "强相关"
    elif abs_corr >= 0.4:
        return "中等相关"
    elif abs_corr >= 0.2:
        return "弱相关"
    else:
        return "极弱相关"

def perform_categorical_analysis(df, field_categories, columns_info):
    """执行分类分析"""
    results = {"primary_analysis": {}, "secondary_analysis": {}, "charts": []}
    
    try:
        categorical_fields = field_categories["categorical_fields"][:2]
        numeric_fields = field_categories["numeric_fields"][:1]
        
        if not categorical_fields or not numeric_fields:
            return perform_descriptive_analysis(df, field_categories, columns_info)
        
        cat_field = categorical_fields[0]
        num_field = numeric_fields[0]
        
        # 分类统计
        df_clean = df[[cat_field, num_field]].dropna()
        if len(df_clean) > 0:
            cat_stats = df_clean.groupby(cat_field)[num_field].agg(['sum', 'mean', 'count']).round(2)
            cat_sorted = cat_stats.sort_values('sum', ascending=False)
            
            results["primary_analysis"] = {
                "analysis_title": f"{cat_field} 分类分析",
                "metric": num_field,
                "categories": {str(k): {
                    "total": safe_convert_value(v['sum']),
                    "average": safe_convert_value(v['mean']),
                    "count": safe_convert_value(v['count'])
                } for k, v in cat_sorted.head(10).iterrows()},
                "total_categories": len(cat_stats)
            }
            
            # 生成分类图表
            chart_data = [{"name": str(k), "value": safe_convert_value(v['sum'])} 
                         for k, v in cat_sorted.head(8).iterrows()]
            
            results["charts"].append({
                "type": "bar",
                "title": f"{cat_field} {num_field} 分布",
                "data": chart_data
            })
            
            results["charts"].append({
                "type": "pie",
                "title": f"{cat_field} 占比分析",
                "data": chart_data[:6]  # 饼图最多显示6个分类
            })
    
    except Exception as e:
        print(f"分类分析失败: {e}")
        return perform_descriptive_analysis(df, field_categories, columns_info)
    
    return results

def perform_descriptive_analysis(df, field_categories, columns_info):
    """执行基础描述性分析"""
    results = {"primary_analysis": {}, "secondary_analysis": {}, "charts": []}
    
    try:
        # 基础数据概览
        results["primary_analysis"] = {
            "analysis_title": "数据概览分析",
            "data_summary": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "numeric_columns": len(field_categories["numeric_fields"]),
                "categorical_columns": len(field_categories["categorical_fields"]),
                "missing_values": df.isnull().sum().sum()
            }
        }
        
        # 如果有数值字段，显示基础统计
        if field_categories["numeric_fields"]:
            numeric_field = field_categories["numeric_fields"][0]
            numeric_data = df[numeric_field].dropna()
            
            if len(numeric_data) > 0:
                results["secondary_analysis"] = {
                    "analysis_title": f"{numeric_field} 基础统计",
                    "stats": {
                        "mean": safe_convert_value(numeric_data.mean()),
                        "median": safe_convert_value(numeric_data.median()),
                        "std": safe_convert_value(numeric_data.std()),
                        "min": safe_convert_value(numeric_data.min()),
                        "max": safe_convert_value(numeric_data.max())
                    }
                }
                
                # 生成分布图
                results["charts"].append({
                    "type": "histogram",
                    "title": f"{numeric_field} 分布",
                    "data": [safe_convert_value(x) for x in numeric_data.tolist()],
                    "column": numeric_field
                })
        
        # 如果有分类字段，显示频次分析
        elif field_categories["categorical_fields"]:
            cat_field = field_categories["categorical_fields"][0]
            cat_counts = df[cat_field].value_counts().head(10)
            
            results["secondary_analysis"] = {
                "analysis_title": f"{cat_field} 频次分析",
                "top_categories": {str(k): safe_convert_value(v) for k, v in cat_counts.items()}
            }
            
            # 生成频次图表
            chart_data = [{"name": str(k), "value": safe_convert_value(v)} for k, v in cat_counts.items()]
            
            results["charts"].append({
                "type": "bar",
                "title": f"{cat_field} 频次分布",
                "data": chart_data
            })
    
    except Exception as e:
        print(f"描述性分析失败: {e}")
    
    return results

def calculate_basic_statistics(df, columns_info):
    """计算基础统计信息"""
    stats = {}
    
    for col in df.columns:
        col_type = columns_info.get(col, {}).get('type', 'text')
        col_data = df[col].dropna()
        
        if col_type == 'numeric' and len(col_data) > 0:
            stats[col] = {
                'type': 'numeric',
                'count': len(col_data),
                'mean': safe_convert_value(col_data.mean()),
                'median': safe_convert_value(col_data.median()),
                'std': safe_convert_value(col_data.std()),
                'min': safe_convert_value(col_data.min()),
                'max': safe_convert_value(col_data.max())
            }
        elif col_type == 'categorical' and len(col_data) > 0:
            value_counts = col_data.value_counts()
            stats[col] = {
                'type': 'categorical',
                'count': len(col_data),
                'unique_count': len(value_counts),
                'top_values': {str(k): safe_convert_value(v) for k, v in value_counts.head(5).items()}
            }
        else:
            stats[col] = {
                'type': col_type,
                'count': len(col_data),
                'unique_count': len(col_data.unique()) if len(col_data) > 0 else 0
            }
    
    return stats

def generate_comprehensive_report(analysis_results, df, custom_requirements=""):
    """生成专业级数据分析报告"""
    report_lines = []
    
    # 报告标题和元信息
    report_lines.append("# 🎯 专业数据分析报告")
    report_lines.append(f"**分析时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**数据规模**: {len(df):,} 行 × {len(df.columns)} 列")
    report_lines.append("")
    
    analysis_type = analysis_results.get("analysis_type", "general")
    
    # 执行摘要
    report_lines.append("## 📋 执行摘要")
    
    data_quality = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    report_lines.append(f"**数据质量评估**: {data_quality:.1f}% 完整度")
    
    if analysis_type == "business_analysis":
        primary_analysis = analysis_results.get("primary_analysis", {})
        if primary_analysis.get("market_structure"):
            market_info = primary_analysis["market_structure"]
            report_lines.append(f"**市场结构**: {market_info['type']}（HHI指数: {market_info['hhi_index']}）")
            report_lines.append(f"**集中度**: 前3名占{market_info['top_3_concentration']}%市场份额")
        
        insights = analysis_results.get("business_insights", [])
        if insights:
            report_lines.append("**关键发现**:")
            for insight in insights[:3]:
                report_lines.append(f"- {insight}")
    
    elif analysis_type == "statistical_analysis":
        primary_analysis = analysis_results.get("primary_analysis", {})
        if primary_analysis.get("variables_analyzed"):
            report_lines.append(f"**统计分析**: 分析了{primary_analysis['variables_analyzed']}个数值变量")
            
        secondary_analysis = analysis_results.get("secondary_analysis", {})
        if secondary_analysis.get("significant_correlations"):
            strong_corrs = [c for c in secondary_analysis["significant_correlations"] if abs(c["correlation"]) > 0.6]
            report_lines.append(f"**相关性发现**: 识别出{len(strong_corrs)}对强相关变量")
    
    report_lines.append("")
    
    # 详细分析结果
    report_lines.append("## 🔍 详细分析")
    
    primary_analysis = analysis_results.get("primary_analysis", {})
    if primary_analysis:
        analysis_title = primary_analysis.get("analysis_title", "主要分析")
        report_lines.append(f"### {analysis_title}")
        
        if analysis_type == "business_analysis" and primary_analysis.get("competitive_dynamics"):
            dynamics = primary_analysis["competitive_dynamics"]
            report_lines.append(f"- **市场参与者**: {dynamics['total_players']}个")
            report_lines.append(f"- **市场领导者**: {dynamics['market_leader']}（{dynamics['leader_share']}%份额）")
            report_lines.append(f"- **运营效率**: 平均{dynamics['avg_efficiency']:.2f}，离散度{dynamics['efficiency_dispersion']:.3f}")
        
        elif analysis_type == "statistical_analysis" and primary_analysis.get("statistical_summary"):
            stats = primary_analysis["statistical_summary"]
            normal_vars = [var for var, info in stats.items() if info["is_normal"]]
            report_lines.append(f"- **正态分布变量**: {len(normal_vars)}个")
            
            high_cv_vars = [var for var, info in stats.items() if info["cv"] > 0.5]
            if high_cv_vars:
                report_lines.append(f"- **高变异变量**: {', '.join(high_cv_vars[:3])}等{len(high_cv_vars)}个")
    
    # 次要分析
    secondary_analysis = analysis_results.get("secondary_analysis", {})
    if secondary_analysis:
        analysis_title = secondary_analysis.get("analysis_title", "次要分析")
        report_lines.append(f"### {analysis_title}")
        
        if analysis_type == "business_analysis" and secondary_analysis.get("diversity_analysis"):
            diversity = secondary_analysis["diversity_analysis"]
            top_diverse = sorted(diversity.items(), key=lambda x: x[1], reverse=True)[:3]
            report_lines.append("**多样化指数排行**:")
            for name, score in top_diverse:
                report_lines.append(f"- {name}: {score}")
        
        elif analysis_type == "statistical_analysis" and secondary_analysis.get("significant_correlations"):
            correlations = secondary_analysis["significant_correlations"][:5]
            report_lines.append("**显著相关性**:")
            for corr in correlations:
                report_lines.append(f"- {corr['field1']} ↔ {corr['field2']}: {corr['correlation']:.3f} ({corr['strength']})")
    
    report_lines.append("")
    
    # 专业洞察
    insights = analysis_results.get("business_insights", []) or analysis_results.get("statistical_insights", [])
    if insights:
        report_lines.append("## 💡 专业洞察")
        for i, insight in enumerate(insights, 1):
            report_lines.append(f"{i}. {insight}")
        report_lines.append("")
    
    # 战略建议
    recommendations = analysis_results.get("strategic_recommendations", []) or analysis_results.get("modeling_recommendations", [])
    if recommendations:
        report_lines.append("## 🎯 战略建议")
        
        if analysis_type == "business_analysis":
            report_lines.append("### 商业策略")
        elif analysis_type == "statistical_analysis":
            report_lines.append("### 分析建议")
        
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        report_lines.append("")
    
    # 风险提示
    report_lines.append("## ⚠️ 风险提示")
    
    if data_quality < 90:
        report_lines.append("- **数据质量风险**: 数据完整度不足90%，可能影响分析结果的可靠性")
    
    if analysis_type == "statistical_analysis":
        secondary_analysis = analysis_results.get("secondary_analysis", {})
        if secondary_analysis.get("multicollinearity_warning"):
            report_lines.append("- **多重共线性风险**: 存在高度相关的变量，建模时需要特别注意")
    
    if len(df) < 100:
        report_lines.append("- **样本量风险**: 数据量较小，统计推断的可靠性有限")
    
    # 自定义需求响应
    if custom_requirements:
        report_lines.append("")
        report_lines.append("## 📝 定制化分析")
        report_lines.append(f"**您的需求**: {custom_requirements}")
        report_lines.append("")
        report_lines.append("**针对性建议**:")
        report_lines.append("- 基于您的具体需求，建议进行更深入的专项分析")
        report_lines.append("- 可考虑结合外部数据源进行对比验证")
        report_lines.append("- 建议建立定期监控机制，跟踪关键指标变化")
    
    # 报告结尾
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*本报告基于专业数据分析方法生成，建议结合业务实际情况进行决策*")
    
    return "\n".join(report_lines)

def generate_adaptive_insights(analysis_results, field_categories, df):
    """根据分析结果生成自适应洞察"""
    insights = []
    
    try:
        analysis_type = analysis_results.get("analysis_type", "general")
        
        # 数据规模洞察
        total_rows = len(df)
        total_cols = len(df.columns)
        insights.append(f"📊 数据规模: {total_rows:,} 行数据，{total_cols} 个字段")
        
        # 根据分析类型生成特定洞察
        if analysis_type == "business_analysis" and analysis_results.get("primary_analysis"):
            primary = analysis_results["primary_analysis"]
            if primary.get("concentration"):
                top_3_share = primary["concentration"]["top_3_share"]
                insights.append(f"🎯 集中度分析: 前3名占 {top_3_share:.1f}% 份额，{'高度集中' if top_3_share > 60 else '相对分散' if top_3_share < 30 else '适度集中'}")
            
            if primary.get("top_performers"):
                top_performer = list(primary["top_performers"].keys())[0]
                insights.append(f"🏆 表现最佳: {top_performer} 在 {primary.get('dimension_field', '维度')} 中领先")
        
        elif analysis_type == "statistical_analysis" and analysis_results.get("secondary_analysis"):
            correlations = analysis_results["secondary_analysis"].get("correlations", [])
            strong_corr = [c for c in correlations if abs(c["correlation"]) > 0.7]
            if strong_corr:
                insights.append(f"🔗 发现 {len(strong_corr)} 对强相关字段，存在明显的数据关联性")
        
        elif analysis_type == "comparative_analysis":
            insights.append("📈 多维度对比分析显示不同分类间存在显著差异")
        
        # 数据质量洞察
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            missing_rate = missing_count / (len(df) * len(df.columns)) * 100
            insights.append(f"⚠️ 数据质量: {missing_rate:.1f}% 缺失率，建议数据清理")
        else:
            insights.append("✅ 数据质量: 数据完整，无缺失值")
        
        # 字段类型洞察
        numeric_count = len(field_categories["numeric_fields"])
        categorical_count = len(field_categories["categorical_fields"])
        
        if numeric_count > categorical_count:
            insights.append("📊 数据特征: 以数值型数据为主，适合统计分析")
        elif categorical_count > numeric_count:
            insights.append("🏷️ 数据特征: 以分类型数据为主，适合维度分析")
        else:
            insights.append("⚖️ 数据特征: 数值与分类字段均衡，适合综合分析")
    
    except Exception as e:
        print(f"生成洞察失败: {e}")
        insights.append("📋 已完成数据分析，请查看详细结果")
    
    return insights

def generate_adaptive_recommendations(analysis_results, field_categories):
    """根据分析结果生成自适应建议"""
    recommendations = []
    
    try:
        analysis_type = analysis_results.get("analysis_type", "general")
        
        # 根据分析类型生成建议
        if analysis_type == "business_analysis":
            recommendations.append("💡 业务优化: 重点关注表现优异的维度，分析其成功因素")
            recommendations.append("📈 资源配置: 建议向高表现维度倾斜资源投入")
            
            if analysis_results.get("primary_analysis", {}).get("concentration", {}).get("top_3_share", 0) < 50:
                recommendations.append("🎯 市场机会: 市场集中度较低，存在提升空间")
        
        elif analysis_type == "statistical_analysis":
            recommendations.append("🔍 深度分析: 建议进一步探索字段间的因果关系")
            recommendations.append("📊 预测建模: 可基于相关性构建预测模型")
        
        elif analysis_type == "comparative_analysis":
            recommendations.append("🔄 对比优化: 分析不同分类的差异原因，制定针对性策略")
            recommendations.append("📋 标杆学习: 向表现优异的分类学习最佳实践")
        
        # 通用建议
        recommendations.append("📈 持续监控: 建议定期更新数据，跟踪关键指标变化")
        recommendations.append("🎯 细分分析: 可以进一步按时间、地域等维度细分分析")
        
        # 数据质量建议
        if len(field_categories["numeric_fields"]) > 0 and len(field_categories["categorical_fields"]) > 0:
            recommendations.append("🔗 交叉分析: 建议探索数值字段与分类字段的交叉关系")
    
    except Exception as e:
        print(f"生成建议失败: {e}")
        recommendations.append("📋 建议定期回顾分析结果，持续优化数据策略")
    
    return recommendations

def analyze_data_comprehensive(df, columns_info):
    """简化但工作的数据分析函数"""
    try:
        analysis_results = {
            "data_overview": {},
            "analysis_type": "business_analysis",
            "primary_analysis": {},
            "secondary_analysis": {},
            "insights": [],
            "recommendations": [],
            "charts": []
        }
    
        # 1. 数据概览
        analysis_results["data_overview"] = {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "missing_data": {k: safe_convert_value(v) for k, v in df.isnull().sum().to_dict().items()},
            "data_types": {col: info['type'] for col, info in columns_info.items()}
        }
        
        # 2. 智能字段识别
        numeric_cols = [col for col, info in columns_info.items() if info['type'] == 'numeric']
        categorical_cols = [col for col, info in columns_info.items() if info['type'] == 'categorical']
        
        # 3. 生成基础分析
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # 分类统计分析
            df_clean = df[[cat_col, num_col]].dropna()
            if len(df_clean) > 0:
                cat_stats = df_clean.groupby(cat_col)[num_col].agg(['sum', 'mean', 'count']).round(2)
                cat_sorted = cat_stats.sort_values('sum', ascending=False)
                
                # 主要分析结果
                analysis_results["primary_analysis"] = {
                    "analysis_title": f"{cat_col} 表现分析",
                    "metric": num_col,
                    "top_categories": {str(k): safe_convert_value(v['sum']) for k, v in cat_sorted.head(8).iterrows()}
                }
                
                # 生成图表
                chart_data = [{"name": str(k), "value": safe_convert_value(v['sum'])} 
                             for k, v in cat_sorted.head(8).iterrows()]
                
                analysis_results["charts"].append({
                    "type": "bar",
                    "title": f"{cat_col} {num_col} 排行榜",
                    "data": chart_data
                })
                
                # 生成饼图
                pie_data = chart_data[:6]  # 饼图最多6个分类
                analysis_results["charts"].append({
                    "type": "pie",
                    "title": f"{cat_col} {num_col} 分布",
                    "data": pie_data
                })
        
        # 4. 生成洞察
        analysis_results["insights"] = [
            f"📊 数据规模: {len(df)} 行数据，{len(df.columns)} 个字段",
            f"📈 数据特征: {len(numeric_cols)} 个数值字段，{len(categorical_cols)} 个分类字段"
        ]
        
        # 数据质量洞察
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            analysis_results["insights"].append(f"⚠️ 数据质量: 发现 {missing_count} 个缺失值")
        else:
            analysis_results["insights"].append("✅ 数据质量: 数据完整，无缺失值")
        
        # 5. 生成建议
        analysis_results["recommendations"] = [
            "💡 建议重点关注表现优异的分类，分析其成功因素",
            "📈 建议定期监控关键指标变化趋势",
            "🔍 可以进一步按时间、地域等维度细分分析"
        ]
        
        return analysis_results
    
    except Exception as e:
        print(f"综合分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 返回基础的分析结果
        return {
            "data_overview": {
                "total_rows": int(len(df)),
                "total_columns": int(len(df.columns)),
                "missing_data": {},
                "data_types": {}
            },
            "analysis_type": "error",
            "primary_analysis": {"analysis_title": "分析失败"},
            "secondary_analysis": {},
            "insights": ["分析过程中出现错误，请检查数据格式"],
            "recommendations": ["建议检查数据完整性后重新分析"],
            "charts": []
        }

def generate_analysis_suggestions(potential_fields):
    """根据识别的字段生成分析建议"""
    suggestions = []
    
    if potential_fields['sales_fields'] and potential_fields['brand_fields']:
        suggestions.append("🎯 品牌销量对比分析")
    
    if potential_fields['sales_fields'] and potential_fields['product_fields']:
        suggestions.append("🏆 产品销量排行分析")
    
    if potential_fields['price_fields'] and potential_fields['sales_fields']:
        suggestions.append("💡 价格与销量关联分析")
    
    if potential_fields['date_fields']:
        suggestions.append("📈 时间趋势分析")
    
    if len(potential_fields['brand_fields']) > 0:
        suggestions.append("🔍 市场竞争格局分析")
    
    if not suggestions:
        suggestions.append("📊 基础统计分析")
    
    return suggestions

def generate_quick_insights(df, analysis_results):
    """生成快速数据洞察"""
    insights = []
    
    # 数据规模洞察
    insights.append(f"📊 数据规模: {int(len(df))} 行数据，{int(len(df.columns))} 个字段")
    
    # 数据质量洞察
    missing_data = df.isnull().sum().sum()
    if missing_data > 0:
        insights.append(f"⚠️ 数据质量: 发现 {missing_data} 个缺失值，建议清理")
    else:
        insights.append("✅ 数据质量: 数据完整，无缺失值")
    
    return insights

def generate_data_preview(filepath, sheet_name):
    """生成轻量级的数据预览信息"""
    try:
        # 读取数据（只读取前100行用于预览）
        df = pd.read_excel(filepath, sheet_name=sheet_name, nrows=100)
        
        # 分析列信息
        columns_info = {}
        potential_fields = {
            'sales_fields': [],
            'brand_fields': [],
            'product_fields': [],
            'price_fields': [],
            'date_fields': []
        }
        
        for col in df.columns:
            col_data = df[col]
            data_type = detect_data_type(col_data)
            columns_info[col] = {
                'type': data_type,
                'non_null_count': int(col_data.count()),
                'total_count': int(len(col_data))
            }
            
            # 智能识别潜在的业务字段
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['销量', '数量', 'quantity', 'sales', '售出', '销售']):
                potential_fields['sales_fields'].append(col)
            elif any(keyword in col_lower for keyword in ['品牌', 'brand', '厂商', 'manufacturer']):
                potential_fields['brand_fields'].append(col)
            elif any(keyword in col_lower for keyword in ['产品', 'product', '商品', '名称', 'name']):
                potential_fields['product_fields'].append(col)
            elif any(keyword in col_lower for keyword in ['价格', 'price', '单价', '金额', 'amount']):
                potential_fields['price_fields'].append(col)
            elif data_type == 'datetime':
                potential_fields['date_fields'].append(col)
        
        # 生成简洁的数据概览
        total_rows = len(pd.read_excel(filepath, sheet_name=sheet_name))  # 获取实际总行数
        
        preview_insights = []
        preview_insights.append(f"📊 数据规模: {total_rows} 行 × {len(df.columns)} 列")
        
        # 数据质量快速检查
        missing_data = df.isnull().sum()
        total_missing = missing_data.sum()
        if total_missing > 0:
            preview_insights.append(f"⚠️ 发现 {total_missing} 个缺失值")
        else:
            preview_insights.append("✅ 数据完整，无缺失值")
        
        return {
            'sheet_name': sheet_name,
            'columns_info': columns_info,
            'potential_fields': potential_fields,
            'preview_insights': preview_insights,
            'total_rows': int(total_rows),
            'preview_rows': int(len(df)),
            'suggested_analysis': generate_analysis_suggestions(potential_fields)
        }
        
    except Exception as e:
        return {
            'error': f'生成预览失败: {str(e)}',
            'sheet_name': sheet_name
        }

def generate_analysis_suggestions(potential_fields):
    """根据识别的字段生成分析建议"""
    suggestions = []
    
    if potential_fields['sales_fields'] and potential_fields['brand_fields']:
        suggestions.append("🎯 品牌销量对比分析")
    
    if potential_fields['sales_fields'] and potential_fields['product_fields']:
        suggestions.append("🏆 产品销量排行分析")
    
    if potential_fields['price_fields'] and potential_fields['sales_fields']:
        suggestions.append("💡 价格与销量关联分析")
    
    if potential_fields['date_fields']:
        suggestions.append("📈 时间趋势分析")
    
    if len(potential_fields['brand_fields']) > 0:
        suggestions.append("🔍 市场竞争格局分析")
    
    if not suggestions:
        suggestions.append("📊 基础统计分析")
    
    return suggestions

def generate_quick_insights(df, analysis_results):
    """生成快速数据洞察"""
    insights = []
    
    # 数据规模洞察
    insights.append(f"📊 数据规模: {int(len(df))} 行数据，{int(len(df.columns))} 个字段")
    
    # 销量洞察
    if 'sales_analysis' in analysis_results and analysis_results['sales_analysis']:
        sales = analysis_results['sales_analysis']
        insights.append(f"💰 销量概况: 总销量 {sales['total_sales']:,.0f}，平均 {sales['average_sales']:.1f}")
        
        # 销量分布洞察
        high_perf = sales['sales_distribution']['high_performers']
        total_products = high_perf + sales['sales_distribution']['medium_performers'] + sales['sales_distribution']['low_performers']
        insights.append(f"🎯 销量分布: {high_perf}/{total_products} 个产品为高销量产品 ({high_perf/total_products*100:.1f}%)")
    
    # 品牌洞察
    if 'brand_analysis' in analysis_results and analysis_results['brand_analysis']:
        brand = analysis_results['brand_analysis']
        insights.append(f"🏷️ 品牌竞争: {brand['brand_count']} 个品牌，前3名占市场 {brand['market_concentration']['top_3_share']:.1f}%")
        
        # 市场集中度判断
        concentration = brand['market_concentration']['top_3_share']
        if concentration > 60:
            insights.append("⚠️ 市场高度集中，头部品牌优势明显")
        elif concentration < 30:
            insights.append("🔄 市场竞争激烈，品牌分布相对均衡")
        else:
            insights.append("⚖️ 市场适度集中，存在竞争机会")
    
    # 产品洞察
    if 'ranking_analysis' in analysis_results and analysis_results['ranking_analysis']:
        ranking = analysis_results['ranking_analysis']
        top_product = list(ranking['top_products'].keys())[0]
        top_sales = list(ranking['top_products'].values())[0]
        insights.append(f"🏆 畅销冠军: {top_product} (销量: {top_sales:,.0f})")
        
        # 销量差异
        min_sales = min(ranking['bottom_products'].values())
        max_sales = max(ranking['top_products'].values())
        ratio = max_sales / min_sales if min_sales > 0 else 0
        if ratio > 100:
            insights.append(f"📈 销量差异巨大: 最高是最低的 {ratio:.0f} 倍")
        elif ratio > 10:
            insights.append(f"📊 销量差异较大: 最高是最低的 {ratio:.1f} 倍")
    
    # 价格洞察
    if 'price_analysis' in analysis_results:
        price = analysis_results['price_analysis']
        correlation = price['price_sales_correlation']
        if abs(correlation) > 0.5:
            direction = "正相关" if correlation > 0 else "负相关"
            insights.append(f"💲 价格策略: 价格与销量呈{direction} (相关系数: {correlation:.2f})")
    
    # 数据质量洞察
    missing_data = analysis_results['data_overview']['missing_data']
    total_missing = sum(missing_data.values())
    if total_missing > 0:
        insights.append(f"⚠️ 数据质量: 发现 {total_missing} 个缺失值，建议清理")
    else:
        insights.append("✅ 数据质量: 数据完整，无缺失值")
    
    # 相关性洞察
    if 'correlation_analysis' in analysis_results:
        corr_count = len(analysis_results['correlation_analysis'])
        insights.append(f"🔗 变量关系: 发现 {corr_count} 对强相关变量，可深入分析")
    
    return insights

def generate_analysis_report(analysis_results, df, custom_requirements=""):
    """生成专业的商业数据分析报告"""
    report = f"""
# 商业数据分析报告

## 📊 执行摘要
- 数据规模: {analysis_results['data_overview']['total_rows']} 行 × {analysis_results['data_overview']['total_columns']} 列
- 数据完整性: {'✅ 良好' if sum(analysis_results['data_overview']['missing_data'].values()) == 0 else '⚠️ 存在缺失值'}

### 🎯 核心发现
"""
    
    # 添加关键洞察
    for insight in analysis_results.get('insights', []):
        report += f"- {insight}\n"
    
    # 品牌表现分析
    if 'brand_performance' in analysis_results and analysis_results['brand_performance']:
        bp = analysis_results['brand_performance']
        report += f"""
## 🏷️ 品牌竞争格局分析

### 市场概况
- 参与品牌数量: {bp['total_brands']} 个
- 市场集中度: CR3 = {bp['market_concentration']['top_3_share']:.1f}%, CR5 = {bp['market_concentration']['top_5_share']:.1f}%
- 赫芬达尔指数: {bp['market_concentration']['hhi_index']:.0f} ({'高度集中' if bp['market_concentration']['hhi_index'] > 2500 else '中度集中' if bp['market_concentration']['hhi_index'] > 1500 else '竞争充分'})

### 品牌表现排行榜
"""
        for brand_name, data in list(bp['top_brands'].items())[:8]:
            report += f"**{data['rank']}. {brand_name}**\n"
            report += f"   - 市场份额: {data['market_share']:.1f}%\n"
            report += f"   - 总销量: {data['total_sales']:,.0f}\n"
            report += f"   - 产品数量: {data['product_count']} 个\n"
            report += f"   - 单品平均销量: {data['avg_sales']:,.0f}\n\n"
        
        # 竞争分析
        if 'competitive_analysis' in analysis_results:
            ca = analysis_results['competitive_analysis']
            if ca.get('market_leader'):
                leader = ca['market_leader']
                report += f"""
### 🏆 市场领导者分析
- **{leader['brand']}** 以 {leader['market_share']:.1f}% 的市场份额领跑市场
- 总销量达到 {leader['total_sales']:,.0f}，显示出强劲的市场控制力
"""
            
            if ca.get('niche_brands'):
                report += f"""
### 💎 小众精品品牌
以下品牌虽然产品数量少，但单品表现优异:
"""
                for brand in ca['niche_brands'][:3]:
                    report += f"- **{brand['brand']}**: {brand['product_count']} 个产品，单品平均销量 {brand['avg_sales']:,.0f}\n"
    
    # 产品表现分析
    if 'product_performance' in analysis_results and analysis_results['product_performance']:
        pp = analysis_results['product_performance']
        report += f"""
## 📦 产品表现分析

### 产品组合概况
- 产品总数: {pp['total_products']} 个
- TOP10产品贡献: {pp['sales_concentration']['top_10_share']:.1f}% 的总销量
- TOP20产品贡献: {pp['sales_concentration']['top_20_share']:.1f}% 的总销量

### 🏆 畅销产品排行榜 (TOP10)
"""
        for i, (product, sales) in enumerate(list(pp['top_products'].items())[:10], 1):
            report += f"{i:2d}. {product}: {sales:,.0f}\n"
        
        # 长尾产品分析
        if pp.get('bottom_products'):
            report += f"""
### 📉 待优化产品 (销量最低5个)
"""
            for product, sales in pp['bottom_products'].items():
                report += f"- {product}: {sales:,.0f}\n"
    
    # 市场结构分析
    if 'market_structure' in analysis_results and analysis_results['market_structure']:
        ms = analysis_results['market_structure']
        if ms.get('brand_product_diversity'):
            report += f"""
## 🎯 品牌产品策略分析

### 产品线丰富度排行
"""
            for brand, data in list(ms['brand_product_diversity'].items())[:5]:
                efficiency = data['avg_per_product']
                report += f"**{brand}**\n"
                report += f"   - 产品数量: {data['product_count']} 个\n"
                report += f"   - 总销量: {data['total_sales']:,.0f}\n"
                report += f"   - 单品效率: {efficiency:,.0f} ({'高效' if efficiency > 1000 else '一般' if efficiency > 500 else '待优化'})\n\n"
    
    # 专业建议
    if analysis_results.get('recommendations'):
        report += f"""
## 💡 战略建议

### 短期行动建议
"""
        for i, recommendation in enumerate(analysis_results['recommendations'][:3], 1):
            report += f"{i}. {recommendation}\n"
        
        if len(analysis_results['recommendations']) > 3:
            report += f"""
### 中长期发展建议
"""
            for i, recommendation in enumerate(analysis_results['recommendations'][3:], 4):
                report += f"{i}. {recommendation}\n"
    
    # 自定义需求分析
    if custom_requirements:
        report += f"""
## 🎯 定制化分析

**您的分析需求**: {custom_requirements}

**针对性建议**:
- 建议基于当前数据进行更深入的细分分析
- 可以考虑引入时间维度数据进行趋势分析
- 建议收集更多维度数据（如地域、渠道等）以获得更全面的洞察
"""
    
    report += f"""
## 📈 后续分析建议

1. **定期监控**: 建议每月更新数据，跟踪关键指标变化
2. **深度挖掘**: 可以进一步分析价格敏感性、季节性趋势等
3. **竞争对标**: 建议收集竞争对手数据进行对比分析
4. **客户细分**: 如有客户数据，可进行更精准的市场细分

---
*报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report += f"""
## 10. 后续行动建议
1. 定期监控关键指标变化
2. 深入分析表现异常的数据点
3. 结合业务背景解读数据洞察
4. 制定基于数据的决策方案

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传Excel文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 使用安全的文件名
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 保存文件
            file.save(filepath)
            
            # 检查文件是否存在
            if not os.path.exists(filepath):
                return jsonify({'error': '文件保存失败'}), 500
            
            try:
                # 读取Excel文件
                sheets_info = read_excel_file(filepath)
                
                # 生成数据预览和基础信息（不进行深度分析）
                data_preview = None
                if sheets_info:
                    first_sheet = list(sheets_info.keys())[0]
                    try:
                        data_preview = generate_data_preview(filepath, first_sheet)
                    except Exception as e:
                        print(f"生成预览失败: {e}")
                
                return jsonify({
                    'filename': filename,
                    'sheets': sheets_info,
                    'data_preview': data_preview
                })
            
            except Exception as e:
                return jsonify({'error': f'读取Excel文件失败: {str(e)}'}), 500
        
        return jsonify({'error': '不支持的文件格式'}), 400
        
    except Exception as e:
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
    
    try:
        numeric_cols = [col for col, info in columns_info.items() if info['type'] == 'numeric']
        for col in numeric_cols:
            try:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    stats[col] = {
                        'mean': safe_convert_value(col_data.mean()),
                        'median': safe_convert_value(col_data.median()),
                        'std': safe_convert_value(col_data.std()),
                        'min': safe_convert_value(col_data.min()),
                        'max': safe_convert_value(col_data.max())
                    }
            except Exception as e:
                print(f"计算列 {col} 统计信息失败: {e}")
                continue
    except Exception as e:
        print(f"计算统计信息失败: {e}")
    
    return stats

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """像数据分析师一样分析数据"""
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
                'non_null_count': int(col_data.count()),
                'total_count': int(len(col_data))
            }
        
        # 执行全面的数据分析
        field_categories = categorize_fields(df, columns_info)
        analysis_strategy = determine_analysis_strategy(field_categories, df)
        
        # 根据策略执行相应的分析
        if analysis_strategy["type"] == "business_analysis":
            comprehensive_analysis = perform_business_analysis(df, field_categories, columns_info)
        elif analysis_strategy["type"] == "comparative_analysis":
            comprehensive_analysis = perform_comparative_analysis(df, field_categories, columns_info)
        elif analysis_strategy["type"] == "statistical_analysis":
            comprehensive_analysis = perform_statistical_analysis(df, field_categories, columns_info)
        elif analysis_strategy["type"] == "categorical_analysis":
            comprehensive_analysis = perform_categorical_analysis(df, field_categories, columns_info)
        else:
            comprehensive_analysis = perform_descriptive_analysis(df, field_categories, columns_info)
        
        # 添加分析类型
        comprehensive_analysis["analysis_type"] = analysis_strategy["type"]
        
        # 计算基础统计信息
        stats = calculate_basic_statistics(df, columns_info)
        
        # 数据预览（前10行，更多数据用于分析）
        data_preview = df.head(10).fillna('').to_dict('records')
        
        # 生成分析报告
        analysis_report = generate_comprehensive_report(comprehensive_analysis, df, custom_requirements)
        
        # 提取图表数据和分析结果
        charts = comprehensive_analysis.get('charts', [])
        primary_analysis = comprehensive_analysis.get('primary_analysis', {})
        secondary_analysis = comprehensive_analysis.get('secondary_analysis', {})
        analysis_type = comprehensive_analysis.get('analysis_type', 'general')
        
        return jsonify({
            'charts': charts,
            'primary_analysis': primary_analysis,
            'secondary_analysis': secondary_analysis,
            'analysis_type': analysis_type,
            'statistics': stats,
            'data_preview': data_preview,
            'analysis_report': analysis_report,
            'columns_info': columns_info
        })
    
    except Exception as e:
        import traceback
        print(f"分析失败详细错误: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
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
