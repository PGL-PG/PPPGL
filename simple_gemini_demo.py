#!/usr/bin/env python3
"""
简化的Gemini调用示例 - 直接调用，无需复杂架构
基于您提供的示例代码
"""

import requests
import pandas as pd
import json

# 直接配置，简单高效
API_KEY = "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}

def analyze_excel(columns, data_sample=None):
    """
    调用 Gemini 模型，基于 Excel 字段做多维度分析 & 可视化思路
    """
    columns_str = ', '.join(columns)
    prompt = f"""
    我上传了一份Excel，字段如下：{columns_str}。
    
    {f"数据样例：{data_sample}" if data_sample else ""}
    
    请帮我：
    1. 根据字段类型（时间、数值、分类等）自动选择合适的分析方法（趋势、对比、分布、相关性）。
    2. 输出可视化分析思路和结论（自然语言）。
    3. 如果字段包含指标类数据（如金额、数量），请尝试做归因诊断（拆解指标、计算贡献度、提出优化建议）。
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

def simple_excel_analysis(file_path):
    """
    简单的Excel分析流程
    """
    print("🚀 开始分析Excel文件...")
    
    # 1. 读取Excel
    try:
        df = pd.read_excel(file_path)
        print(f"✅ 成功读取文件，共 {len(df)} 行，{len(df.columns)} 列")
    except Exception as e:
        print(f"❌ 文件读取失败：{e}")
        return
    
    # 2. 获取字段信息
    columns = list(df.columns)
    print(f"📋 字段列表：{columns}")
    
    # 3. 生成数据样例
    data_sample = df.head(3).to_dict('records')
    sample_str = json.dumps(data_sample, ensure_ascii=False, indent=2)[:500]
    
    # 4. 调用Gemini分析
    print("🤖 正在调用Gemini进行分析...")
    analysis_result = analyze_excel(columns, sample_str)
    
    # 5. 输出结果
    print("\n" + "="*50)
    print("📊 AI分析结果")
    print("="*50)
    print(analysis_result)
    print("="*50)

if __name__ == "__main__":
    print("🎯 Excel数据分析助手 - 简化版")
    print("📁 请将Excel文件放在当前目录下")
    
    # 示例用法
    file_path = input("请输入Excel文件名（如：data.xlsx）：")
    
    if file_path:
        simple_excel_analysis(file_path)
    else:
        print("👋 再见！")