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
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ")  # 请设置环境变量或更换为您的API Key
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
        "preview": df.head().to_dict('records'),
        "summary_stats": {}
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
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
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
                    "📈 建议分析数值字段的分布和趋势",
                    "🔍 建议进行相关性分析",
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
            
        elif file.filename.endswith('.csv'):
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
                    "📈 建议分析数值字段的分布和趋势", 
                    "🔍 建议进行相关性分析"
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
        # 构建专业的分析提示词
        columns_str = ", ".join(request.columns)
        
        prompt = f"""我是一个Excel数据分析助手，用户上传了包含以下字段的Excel文件：

数据字段：{columns_str}

{f"用户的具体需求：{request.custom_requirements}" if request.custom_requirements else ""}

{f"数据样例：{request.data_sample}" if request.data_sample else ""}

请像Excel分析师一样，提供实用的数据分析：

## 📊 数据快速解读
- 这是什么类型的业务数据？（销售、产品、财务、人员等）
- 数据的基本情况和质量如何？
- 哪些字段最重要，为什么？

## 🎯 核心业务发现
- 从数据中能看出哪些关键信息？
- 有什么值得关注的数字或趋势？
- 哪些方面表现突出，哪些需要改进？

## 📈 实用排行榜分析
- 可以做哪些有意义的排名（如销量排行、品牌对比等）？
- 前几名和后几名有什么特点？
- 如何用Excel函数实现这些排名？

## 📊 推荐图表组合
- 推荐3个最有价值的图表类型
- 每个图表用什么字段组合最合适？
- 这些图表能回答什么业务问题？

## 💡 业务建议和行动
- 基于数据分析，有什么具体的改进建议？
- 哪些指标需要持续关注？
- 下一步应该收集什么额外数据？

## 🔍 进一步分析方向
- 如果要深入分析，建议从哪些维度切入？
- 可以做哪些有趣的交叉对比？
- 什么样的细分分析最有价值？

请用简单易懂的语言，像和Excel用户对话一样，提供实用的分析结果。"""

        # 调用 Gemini 进行分析
        analysis_result = call_gemini(prompt)
        
        # 生成图表建议
        chart_prompt = f"""基于字段 {columns_str}，请推荐5个最有价值的可视化图表：

请为每个图表提供：
1. 图表类型（柱状图/折线图/饼图/散点图/热力图等）
2. 使用的字段组合
3. 分析目的
4. 预期洞察

格式：图表类型 | 字段组合 | 分析目的 | 预期洞察"""
        
        chart_suggestions = call_gemini(chart_prompt)
        
        return {
            "status": "success",
            "analysis_report": analysis_result,
            "chart_suggestions": chart_suggestions,
            "analysis_type": "comprehensive_gemini_analysis",
            "primary_analysis": {
                "analysis_title": "基于 Gemini 的专业数据分析"
            },
            "business_insights": [
                "✨ 基于 Google Gemini 2.0 Flash 的深度分析",
                "📊 专业数据分析师级别的洞察",
                "💡 结合业务场景的实用建议",
                "🎯 数据驱动的决策支持"
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