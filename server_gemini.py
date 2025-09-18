from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import io
import re

import os

# Gemini API 配置
API_KEY = "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ"  # 直接设置API Key
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}

app = FastAPI(title="AI Excel 分析服务 - Gemini版")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExcelAnalysisRequest(BaseModel):
    columns: List[str]
    data_sample: Optional[str] = None
    analysis_type: Optional[str] = "comprehensive"
    filename: Optional[str] = None
    sheet_name: Optional[str] = None
    selected_columns: Optional[List[str]] = None
    custom_requirements: Optional[str] = None

class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 200
    temperature: float = 0.7

class FileUploadResponse(BaseModel):
    filename: str
    sheets_data: Dict[str, Any]
    data_preview: Dict[str, Any]

def call_gemini(prompt: str) -> str:
    """调用 Gemini API"""
    body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Gemini API 调用失败: {str(e)}")
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Gemini API 响应格式错误: {str(e)}")

def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """分析 DataFrame 并提取基本信息"""
    analysis = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": {},
        "preview": df.head(5).to_dict('records'),  # 修改为显示前5行
        "summary_stats": {},
        "data_preview_table": {
            "columns": list(df.columns),
            "data": df.head(5).values.tolist()  # 新增：前5行数据表格形式
        }
    }
    
    for col in df.columns:
        col_data = df[col].dropna()
        col_info = {
            "type": "text",
            "null_count": df[col].isnull().sum(),
            "unique_count": df[col].nunique()
        }
        
        # 判断数据类型
        if pd.api.types.is_numeric_dtype(col_data):
            col_info["type"] = "numeric"
            col_info["stats"] = {
                "mean": float(col_data.mean()) if not col_data.empty else 0,
                "std": float(col_data.std()) if not col_data.empty else 0,
                "min": float(col_data.min()) if not col_data.empty else 0,
                "max": float(col_data.max()) if not col_data.empty else 0
            }
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            col_info["type"] = "datetime"
        elif col_info["unique_count"] < len(col_data) * 0.5:
            col_info["type"] = "categorical"
            col_info["top_values"] = col_data.value_counts().head().to_dict()
        
        analysis["columns"][col] = col_info
    
    return analysis

def generate_data_insights(data_analysis: Dict[str, Any]) -> str:
    """使用 Gemini 生成数据洞察"""
    prompt = f"""我是一个Excel数据分析助手，请帮我分析这份数据，提供实用的业务洞察：

数据基本情况：
- 数据量：{data_analysis['row_count']}行，{data_analysis['column_count']}列

字段信息：
"""
    
    # 分类字段信息
    categorical_fields = []
    numeric_fields = []
    
    for col, info in data_analysis['columns'].items():
        if info['type'] == 'numeric':
            numeric_fields.append(col)
            if 'stats' in info:
                stats = info['stats']
                prompt += f"\n📊 {col}（数值）：平均{stats['mean']:.1f}，范围{stats['min']:.1f}-{stats['max']:.1f}"
        elif info['type'] == 'categorical':
            categorical_fields.append(col)
            if 'top_values' in info:
                top_vals = list(info['top_values'].keys())[:3]
                prompt += f"\n🏷️ {col}（分类）：主要包括{', '.join(map(str, top_vals))}等{info['unique_count']}个类别"
        else:
            prompt += f"\n📝 {col}（{info['type']}）：{info['unique_count']}个不同值"
    
    prompt += f"""

数据样例：
{json.dumps(data_analysis['preview'][:2], ensure_ascii=False, indent=2)}

请像Excel分析师一样，提供以下实用分析：

1. 🎯 业务场景识别：这是什么类型的数据（销售、产品、财务等）？

2. 📊 关键发现：
   - 哪些数值最值得关注？
   - 哪些分类维度最重要？
   - 有什么明显的模式或特点？

3. 📈 排行榜建议：可以做哪些有意义的排名分析？

4. 📉 图表建议：推荐3个最有价值的图表组合

5. 💡 业务洞察：从数据中能得出什么实用的结论？

请用简单直白的语言，像Excel用户一样思考问题。"""
    
    return call_gemini(prompt)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """文件上传接口"""
    try:
        # 读取文件内容
        contents = await file.read()
        
        # 根据文件类型处理
        if file.filename and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            # 读取 Excel 文件
            excel_file = pd.ExcelFile(io.BytesIO(contents))
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
                sheets_data[sheet_name] = analyze_dataframe(df)
            
            # 选择第一个工作表进行预览分析
            first_sheet = list(sheets_data.keys())[0]
            first_sheet_data = sheets_data[first_sheet]
            
            # 使用 Gemini 生成数据洞察
            data_insights = generate_data_insights(first_sheet_data)
            
            data_preview = {
                "preview_insights": data_insights.split('\n')[:10],  # 取前10行作为预览
                "suggested_analysis": [
                    "📊 建议进行描述性统计分析",
                    "📈 建议分析数值字段的排行和分布",
                    "📅 建议制作Excel透视表分析",
                    "💡 建议根据业务场景进行深度分析"
                ],
                "potential_fields": {
                    "sales_fields": [col for col, info in first_sheet_data['columns'].items() 
                                   if '销售' in col or '金额' in col or '收入' in col],
                    "brand_fields": [col for col, info in first_sheet_data['columns'].items() 
                                   if '品牌' in col or '产品' in col or '类别' in col],
                    "product_fields": [col for col, info in first_sheet_data['columns'].items() 
                                     if '产品' in col or '商品' in col],
                    "price_fields": [col for col, info in first_sheet_data['columns'].items() 
                                   if '价格' in col or '单价' in col or '成本' in col]
                }
            }
            
            return {
                "filename": file.filename,
                "sheets_data": sheets_data,
                "data_preview": data_preview
            }
            
        elif file.filename and file.filename.endswith('.csv'):
            # 读取 CSV 文件
            df = pd.read_csv(io.BytesIO(contents))
            sheet_data = analyze_dataframe(df)
            
            # 使用 Gemini 生成数据洞察
            data_insights = generate_data_insights(sheet_data)
            
            sheets_data = {"Sheet1": sheet_data}
            data_preview = {
                "preview_insights": data_insights.split('\n')[:10],
                "suggested_analysis": [
                    "📊 建议进行描述性统计分析",
                    "📈 建议分析数值字段的排行和分布",
                    "📅 建议制作Excel透视表分析"
                ]
            }
            
            return {
                "filename": file.filename,
                "sheets_data": sheets_data,
                "data_preview": data_preview
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.post("/analyze")
def analyze_data(request: ExcelAnalysisRequest):
    """完整数据分析接口"""
    try:
        columns_str = ", ".join(request.columns)
        
        # 如果用户有自定义需求，只分析自定义内容
        if request.custom_requirements and request.custom_requirements.strip():
            prompt = f"""我是Excel数据分析助手，用户有具体的分析需求。

数据字段：{columns_str}

数据样例：{request.data_sample if request.data_sample else ""}

用户的分析需求：{request.custom_requirements}

请专门针对用户的需求进行分析，不要分析其他额外内容。分析要基于实际数据，提供具体、量化的结果。

## 📊 可视化建议
基于分析需求，推荐最适合的图表类型和字段组合：
- 图表类型：（柱状图/饼图/折线图/条形图等）
- 字段组合：具体使用哪些字段
- 分析价值：这个图表能展示什么业务洞察

## 🔍 针对性分析
（专门回答用户的问题，基于实际数据给出具体结论）

请用Excel分析师的角度，给出实用的分析结果。"""
        else:
            # 默认分析，符合Excel分析定位
            prompt = f"""我是Excel数据分析助手，用户上传了包含以下字段的Excel文件：

数据字段：{columns_str}

数据样例：{request.data_sample if request.data_sample else ""}

请像Excel分析师一样，提供实用的数据分析：

## 📊 可视化分析建议
基于数据特点，推荐最有价值的Excel图表：
- 排行榜图表：适合分析各类别的数值对比（柱状图、条形图）
- 占比分析：适合分析构成情况（饼图、环形图）
- 趋势分析：如果有时间字段，适合分析变化趋势（折线图）
- 分布分析：适合分析数值分布情况（直方图）
具体推荐哪些字段组合制作图表，以及预期能发现什么业务洞察。

## 📋 数据快速解读
- 这是什么类型的业务数据？（销售、产品、财务、人员等）
- 数据的基本情况和质量如何？
- 哪些字段最重要，为什么？

## 🎯 核心业务发现
- 从数据中能看出哪些关键信息？
- 有什么值得关注的数字或趋势？
- 哪些方面表现突出，哪些需要改进？

## 📈 Excel实用分析
- 可以做哪些有意义的排名分析？
- 可以做哪些汇总统计？
- 如何用Excel透视表分析这些数据？

## 💡 实用建议
- 基于数据分析，有什么具体的改进建议？
- 哪些指标需要持续关注？
- 如何用Excel持续监控这些数据？

请用简单易懂的语言，像Excel用户熟悉的分析方式提供实用结果。"""

        # 调用 Gemini 进行分析
        analysis_result = call_gemini(prompt)
        
        # 生成Excel风格的图表建议
        chart_prompt = f"""基于字段 {columns_str}，从Excel数据分析的角度推荐最实用的图表：

重点推荐适合Excel的图表类型：
1. 柱状图/条形图：适合排行榜、对比分析
2. 饼图/环形图：适合占比、构成分析  
3. 折线图：适合趋势分析（如果有时间字段）
4. 数据透视表图表：适合多维度交叉分析

请为每个推荐图表提供：
- 图表类型
- 使用的字段组合
- Excel制作方法
- 能发现什么业务洞察

请避免推荐散点图、热力图等复杂图表，专注于Excel用户最常用的图表类型。"""
        
        chart_suggestions = call_gemini(chart_prompt)
        
        return {
            "status": "success",
            "analysis_report": analysis_result,
            "chart_suggestions": chart_suggestions,
            "analysis_type": "excel_focused_analysis",
            "primary_analysis": {
                "analysis_title": "基于 Gemini 的Excel数据分析"
            },
            "business_insights": [
                "📊 Excel风格的数据分析",
                "📈 实用的图表和透视表建议", 
                "💡 适合Excel用户的分析方法",
                "🎯 聚焦业务价值的洞察"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/generate")
def generate_text(request: GenerateRequest):
    """通用文本生成接口（兼容原有接口）"""
    try:
        result = call_gemini(request.prompt)
        return {"response": result}
    except HTTPException as e:
        return {"error": str(e.detail)}

@app.post("/attribution")
def attribution_analysis(request: ExcelAnalysisRequest):
    """归因分析接口"""
    try:
        columns_str = ", ".join(request.columns)
        target_metric = request.custom_requirements or "主要指标"
        
        prompt = f"""我需要分析影响【{target_metric}】的关键因素，数据包含以下字段：

数据字段：{columns_str}
分析目标：{target_metric}

请像Excel分析师一样，进行实用的影响因素分析：

## 🎯 影响因素识别
- 在这些字段中，哪些最可能影响{target_metric}？
- 按影响程度给这些因素排个序
- 哪些是直接影响，哪些是间接影响？

## 📊 关键发现
- 从数据角度看，{target_metric}主要受什么因素驱动？
- 有没有发现意外的影响关系？
- 哪些因素的影响最容易被忽视？

## 📈 实用的Excel分析方法
- 可以用哪些Excel函数来验证这些影响关系？
- 建议做哪些透视表分析？
- 如何制作有效的对比图表？

## 💡 改进建议
- 要提升{target_metric}，应该重点关注哪些方面？
- 哪些是"快赢"的改进点（容易实现且效果明显）？
- 哪些需要长期投入？

## 🔍 深入分析建议
- 建议按什么维度进一步细分分析？
- 什么样的数据组合最能说明问题？
- 如果要做预测，重点应该监控哪些指标？

## ⚠️ 注意事项
- 分析过程中需要注意什么陷阱？
- 哪些因素可能存在相互影响？
- 有什么潜在的风险需要关注？

请提供具体可操作的分析建议，就像Excel专家在指导具体的数据分析工作。"""

        analysis_result = call_gemini(prompt)
        
        return {
            "status": "success",
            "attribution_analysis": analysis_result,
            "key_drivers": [
                "🎯 基于 Gemini 的智能归因分析",
                "📊 多维度因素分解",
                "🔍 深度因果关系挖掘",
                "💡 数据驱动的优化建议"
            ],
            "recommendations": [
                "根据归因分析结果优化关键驱动因素",
                "建立指标监控和预警体系",
                "制定数据驱动的改进计划",
                "定期评估和调整优化策略"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/chart_suggestions")
def get_chart_suggestions(request: ExcelAnalysisRequest):
    """图表建议接口"""
    columns_str = ", ".join(request.columns)
    
    prompt = f"""作为数据可视化专家，请为以下数据字段推荐最佳的可视化方案：

数据字段：{columns_str}

请分析每个字段的特征，并推荐合适的图表类型：

## 字段分析与图表推荐

请为每种可能的字段组合推荐图表类型：

1. **单字段分析**
   - 数值字段：直方图、箱线图
   - 分类字段：柱状图、饼图
   - 时间字段：时间序列图

2. **双字段分析**
   - 数值 vs 数值：散点图、相关性图
   - 分类 vs 数值：分组柱状图、小提琴图
   - 时间 vs 数值：折线图、面积图

3. **多字段分析**
   - 热力图、雷达图、平行坐标图

请为每个推荐提供：
- 图表类型
- 使用的字段组合
- 分析目的
- 预期洞察
- 优先级评分(1-5分)

请按优先级排序，重点推荐最有价值的5个图表。"""

    try:
        suggestions = call_gemini(prompt)
        return {
            "status": "success",
            "suggestions": suggestions
        }
    except HTTPException as e:
        return {
            "status": "error",
            "error": str(e.detail)
        }

@app.get("/")
def root():
    return {
        "message": "AI Excel 分析服务正在运行", 
        "model": "Google Gemini 2.0 Flash",
        "status": "ready"
    }

@app.get("/health")
def health_check():
    """健康检查"""
    try:
        # 测试 API 连接
        test_prompt = "Hello"
        call_gemini(test_prompt)
        return {
            "status": "healthy", 
            "model": "Gemini 2.0 Flash",
            "api_status": "connected"
        }
    except:
        return {
            "status": "error", 
            "model": "Gemini 2.0 Flash",
            "api_status": "disconnected"
        }

# 启动命令：
# uvicorn server_gemini:app --host 0.0.0.0 --port 8000 --reload