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
# 简化的 Gemini API 调用
API_KEY = "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ"  # 直接设置API Key
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}

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
