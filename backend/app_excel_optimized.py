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
# 直接调用 Google Gemini API（需设置环境变量 GEMINI_API_KEY）
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        field_type = key_fields.get('字段类型', {}).get(col, 'unknown')
        
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
                "std": round(col_data.std(), 2) if not col_data.empty else None
            })
        elif field_type == 'categorical':
            stats.update({
                "unique_count": col_data.nunique(),
                "most_frequent": col_data.mode().iloc[0] if not col_data.mode().empty else None,
                "most_frequent_count": col_data.value_counts().iloc[0] if not col_data.value_counts().empty else 0
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
    unique_ratio = len(non_null_series.unique()) / len(non_null_series)
    if unique_ratio < 0.5 and len(non_null_series.unique()) < 20:
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
        
        if file and allowed_file(file.filename):
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
            col_data = df[col]
            data_type = detect_data_type(col_data)
            columns_info[str(col)] = {
                'type': data_type,
                'non_null_count': int(col_data.count()),
                'total_count': len(col_data)
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

        # 热力图：数值字段相关性矩阵 + 散点：最强相关对
        try:
            numeric_cols = [c for c in key_fields.get("数值字段", [])][:6]
            if len(numeric_cols) >= 2:
                corr_df = df[numeric_cols].dropna()
                if len(corr_df) > 1:
                    corr = corr_df.corr()
                    heatmap_data = []
                    for i, f1 in enumerate(numeric_cols):
                        for j, f2 in enumerate(numeric_cols):
                            val = corr.loc[f1, f2]
                            if pd.isna(val):
                                continue
                            heatmap_data.append({
                                "x": i,
                                "y": j,
                                "value": round(float(val), 3),
                                "field1": f1,
                                "field2": f2
                            })
                    charts.append({
                        "type": "heatmap",
                        "title": "变量相关性热力图",
                        "data": heatmap_data
                    })

                    # 找到最强（非对角线）相关对并绘制散点
                    strongest = None
                    strongest_pair = (None, None)
                    for i in range(len(numeric_cols)):
                        for j in range(i+1, len(numeric_cols)):
                            v = corr.loc[numeric_cols[i], numeric_cols[j]]
                            if pd.isna(v):
                                continue
                            if strongest is None or abs(v) > abs(strongest):
                                strongest = v
                                strongest_pair = (numeric_cols[i], numeric_cols[j])
                    if strongest_pair[0] and strongest_pair[1]:
                        pair_df = df[[strongest_pair[0], strongest_pair[1]]].dropna()
                        if len(pair_df) > 1:
                            # 气泡大小用第二个变量的相对幅度，简单缩放
                            x_vals = pair_df[strongest_pair[0]].astype(float)
                            y_vals = pair_df[strongest_pair[1]].astype(float)
                            size_base = max(y_vals.max() - y_vals.min(), 1.0)
                            scatter_data = []
                            for xv, yv in zip(x_vals.tolist(), y_vals.tolist()):
                                scatter_data.append([
                                    float(xv),
                                    float(yv),
                                    max((float(yv) - float(y_vals.min())) / size_base * 100.0, 8.0),
                                    f"{strongest_pair[0]}·{strongest_pair[1]}"
                                ])
                            charts.append({
                                "type": "scatter",
                                "title": f"最强相关散点（{strongest_pair[0]} vs {strongest_pair[1]}，r={strongest:.2f})",
                                "data": scatter_data
                            })
        except Exception as _e:
            pass

        # 箱线图：数值字段分布与异常值
        try:
            numeric_cols_for_box = [c for c in key_fields.get("数值字段", [])][:4]
            box_data = []
            for col in numeric_cols_for_box:
                series = pd.to_numeric(df[col], errors='coerce').dropna()
                if len(series) == 0:
                    continue
                q1, median, q3 = series.quantile([0.25, 0.5, 0.75])
                iqr = q3 - q1
                lower = float(q1 - 1.5 * iqr)
                upper = float(q3 + 1.5 * iqr)
                outliers = series[(series < lower) | (series > upper)].tolist()
                box_data.append({
                    "name": col,
                    "min": float(series.min()),
                    "q1": float(q1),
                    "median": float(median),
                    "q3": float(q3),
                    "max": float(series.max()),
                    "outliers": [float(x) for x in outliers[:20]]
                })
            if box_data:
                charts.append({
                    "type": "boxplot",
                    "title": "数值字段分布箱线图",
                    "data": box_data
                })
        except Exception as _e:
            pass
        
        # 生成基础统计概览（由浅入深的第一步）
        basic_stats_overview = generate_basic_stats_overview(df, key_fields, business_scenario)
        
        # 尝试调用Gemini获取AI洞察/结构化结果（直连Google API）
        ai_insights = ""
        ai_result_full = None
        ai_called = False
        ai_error = None
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise Exception("缺少 GEMINI_API_KEY 环境变量")

            prompt_header = (
                "你是一位拥有10年经验的资深商业数据分析师，需对任意Excel数据进行由浅入深的专业分析。"
                "基于提供的基础统计、多维分析结果，输出结构化中文报告，严格按以下层次递进：\n\n"
                "## 第一部分：基础数据概览\n"
                "1) 数据规模：总行数、列数、关键字段识别\n"
                "2) 基础统计：各字段的基本统计量（均值、中位数、最值、缺失值等）\n"
                "3) 简单聚合：如品牌数量、销量TOP、价格分布等Excel基础函数结果\n\n"
                "## 第二部分：多维度深度分析\n"
                "4) 维度对比分析：TOP-N排名、集中度分析、帕累托80/20法则\n"
                "5) 价格带分析：如有价格字段，分析价格区间分布与热销段\n"
                "6) 相关性分析：重要指标间的相关关系与强度\n"
                "7) 异常值检测：识别异常数据点及其可能原因\n\n"
                "## 第三部分：商业洞察与建议\n"
                "8) 关键发现：3-5个最重要的业务洞察\n"
                "9) 归因诊断：对异常现象的可能原因分析\n"
                "10) 行动建议：3-6条可执行的优化建议，按优先级排序\n\n"
                "要求：\n"
                "- 语言专业、逻辑清晰、由浅入深\n"
                "- 每个分析点都要有具体数据支撑\n"
                "- 避免空洞陈述，给出具体数值和比例\n"
                "- 如发现数据质量问题（如品牌名称不统一），要明确指出并给出清洗建议\n"
                "- 分析要贴合实际业务场景，给出可操作的改进建议"
            )
            # 为模型提供更充分的结构化上下文（避免空话）：
            # 包含字段类型、基础统计、排行榜Top/N、分组Top/N、趋势存在性等
            top_rank_key = None
            top_rank_sample = {}
            if "排行榜" in basic_analysis and basic_analysis["排行榜"]:
                top_rank_key = list(basic_analysis["排行榜"].keys())[0]
                top_rank_sample = dict(list(basic_analysis["排行榜"][top_rank_key].items())[:8])

            group_key = None
            group_sample = {}
            if "分组统计" in basic_analysis and basic_analysis["分组统计"]:
                group_key = list(basic_analysis["分组统计"].keys())[0]
                group_sample = dict(list(basic_analysis["分组统计"][group_key].items())[:8])

            payload_text = {
                "basic_stats_overview": basic_stats_overview,
                "columns": list(df.columns),
                "data_sample": df.head(3).to_dict('records') if len(df) > 0 else [],
                "columns_info": columns_info,
                "key_fields": key_fields,
                "basic_analysis": basic_analysis,
                "dimensional_analysis": dimensional_analysis,
                "top_rank_title": top_rank_key,
                "top_rank_sample": top_rank_sample,
                "group_title": group_key,
                "group_sample": group_sample,
                "business_scenario": business_scenario,
                "analysis_level": analysis_level,
                "custom_requirements": custom_requirements
            }

            # 预先序列化为纯JSON友好格式
            payload_json = json.dumps(sanitize_for_json(payload_text), ensure_ascii=False)

            body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt_header},
                            {"text": payload_json}
                        ]
                    }
                ]
            }

            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": api_key
            }

            response = requests.post(GEMINI_API_URL, headers=headers, json=body, timeout=60)
            response.raise_for_status()
            result = response.json()
            # 提取文本
            ai_text = ""
            try:
                ai_text = result["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                ai_text = ""
            ai_insights = ai_text or ""
            ai_result_full = {"analysis_report": ai_insights}
            ai_called = True
            
        except Exception as e:
            print(f"调用Gemini失败: {e}")
            ai_error = str(e)
            ai_insights = "AI分析服务暂时不可用，已为您提供基础分析结果。"

        # 结果整合策略：
        # - gemini_only: 若有AI结果，则优先输出AI结构化结果；无则报错提示不可用
        # - hybrid(default): 若AI有结构化 charts/primary/secondary，则覆盖本地对应部分；否则保留本地
        # - local_only: 忽略AI，仅返回本地

        if ai_mode == 'gemini_only':
            if ai_result_full:
                return jsonify(sanitize_for_json({
                    "status": "success",
                    "analysis_type": ai_result_full.get("analysis_type", f"excel_analysis_{analysis_level}"),
                    "business_scenario": business_scenario,
                    "data_overview": {
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "key_fields": key_fields,
                        "missing_data": {col: df[col].isnull().sum() for col in df.columns if df[col].isnull().sum() > 0}
                    },
                    "basic_analysis": ai_result_full.get("basic_analysis", basic_analysis),
                    "dimensional_analysis": ai_result_full.get("dimensional_analysis", dimensional_analysis),
                    "practical_insights": ai_result_full.get("practical_insights", practical_insights),
                    "ai_insights": ai_insights,
                    "charts": ai_result_full.get("charts", charts),
                    "primary_analysis": ai_result_full.get("primary_analysis"),
                    "secondary_analysis": ai_result_full.get("secondary_analysis"),
                    "recommendations": ai_result_full.get("recommendations", []),
                    "ai_called": ai_called,
                    "ai_error": ai_error
                }))
            else:
                return jsonify({"error": "AI分析服务不可用，gemini_only 模式下无法完成分析"}), 503

        if ai_mode == 'hybrid' and ai_result_full:
            charts = ai_result_full.get("charts", charts) or charts
            primary_analysis = ai_result_full.get("primary_analysis")
            secondary_analysis = ai_result_full.get("secondary_analysis")
        else:
            primary_analysis = None
            secondary_analysis = None

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
            "primary_analysis": primary_analysis,
            "secondary_analysis": secondary_analysis,
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

@app.route('/api/attribution', methods=['POST'])
def attribution_analysis():
    """归因分析接口"""
    try:
        data = request.get_json()
        
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        target_metric = data.get('target_metric')
        available_columns = data.get('available_columns', [])
        
        if not all([filename, target_metric]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 读取文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_excel(filepath, sheet_name=sheet_name or 0)
        
        if target_metric not in df.columns:
            return jsonify({'error': f'目标指标 {target_metric} 不存在'}), 400
        
        # 生成列信息
        columns_info = {}
        for col in df.columns:
            columns_info[col] = {'type': detect_data_type(df[col])}
        
        # 使用Excel分析引擎
        key_fields = identify_key_fields(df, columns_info)
        
        # 执行深度分析
        deep_analysis = perform_multi_dimensional_analysis(df, key_fields, "深度")
        
        # 计算简单的相关性分析
        correlation_insights = []
        if key_fields["数值字段"] and target_metric in key_fields["数值字段"]:
            numeric_cols = [col for col in key_fields["数值字段"] if col != target_metric]
            if numeric_cols:
                target_data = df[target_metric].dropna()
                for col in numeric_cols[:3]:  # 最多分析3个相关字段
                    try:
                        other_data = df[col].dropna()
                        if len(target_data) > 1 and len(other_data) > 1:
                            # 找到两个字段都有数据的行
                            common_df = df[[target_metric, col]].dropna()
                            if len(common_df) > 1:
                                corr = common_df[target_metric].corr(common_df[col])
                                if not pd.isna(corr) and abs(corr) > 0.3:
                                    strength = "强" if abs(corr) > 0.6 else "中等"
                                    direction = "正相关" if corr > 0 else "负相关"
                                    correlation_insights.append(f"📊 {col} 与 {target_metric} 呈{strength}{direction} (相关系数: {corr:.3f})")
                    except:
                        continue
        
        # 分类字段影响分析
        category_insights = []
        if key_fields["分类字段"] and target_metric in df.columns:
            for cat_field in key_fields["分类字段"][:2]:
                try:
                    df_clean = df[[cat_field, target_metric]].dropna()
                    if len(df_clean) > 0:
                        grouped = df_clean.groupby(cat_field)[target_metric].mean().sort_values(ascending=False)
                        if len(grouped) > 1:
                            best_category = grouped.index[0]
                            worst_category = grouped.index[-1]
                            best_value = grouped.iloc[0]
                            worst_value = grouped.iloc[-1]
                            
                            if best_value > worst_value:
                                diff_ratio = ((best_value - worst_value) / worst_value) * 100
                                category_insights.append(f"🎯 {cat_field}中，{best_category}的{target_metric}比{worst_category}高{diff_ratio:.1f}%")
                except:
                    continue
        
        # 尝试调用Gemini获取AI归因分析（直连Google API）
        ai_attribution = ""
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise Exception("缺少 GEMINI_API_KEY 环境变量")

            prompt_header = (
                f"你是一位资深数据分析师。请围绕目标指标『{target_metric}』做归因诊断，"
                "输出结构化中文内容：1) 指标概览(均值/方差/分布形态)；2) 可能驱动因素(按强弱排序，标注正/负影响)；"
                "3) 关键分类维度差异(TOP-N与长尾)；4) 异常与波动原因(数据/业务/外部)与验证思路；"
                "5) 可执行改进建议(优先级与预期影响)，并给出需持续监控的指标清单。"
            )
            payload_text = {
                "columns": list(df.columns),
                "numeric_preview": df.select_dtypes(include=['number']).head(3).to_dict('records'),
                "target_metric": target_metric,
                "key_fields": key_fields,
                "deep_analysis": deep_analysis
            }

            body = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt_header},
                            {"text": json.dumps(payload_text, ensure_ascii=False)}
                        ]
                    }
                ]
            }

            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": api_key
            }

            resp = requests.post(GEMINI_API_URL, headers=headers, json=body, timeout=60)
            resp.raise_for_status()
            res_json = resp.json()
            try:
                ai_attribution = res_json["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                ai_attribution = ""
        except Exception as e:
            print(f"调用Gemini归因分析失败: {e}")
            ai_attribution = "AI归因分析服务暂时不可用。"
        
        # 组合所有洞察
        all_insights = correlation_insights + category_insights
        if not all_insights:
            all_insights = [f"📋 已完成{target_metric}的影响因素分析"]
        
        return jsonify({
            "status": "success",
            "target_metric": target_metric,
            "attribution_analysis": ai_attribution,
            "key_drivers": all_insights,
            "recommendations": [
                "🔍 重点关注相关性较强的影响因素",
                "📊 建议按不同维度深入分析差异原因", 
                "💡 制定针对性的改进措施",
                "📈 建立关键指标的监控体系"
            ],
            "deep_analysis": deep_analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'归因分析失败: {str(e)}'}), 500

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
