#!/usr/bin/env python3
"""
测试 Gemini API 连接和功能
"""
import requests
import json

def test_gemini_api():
    """测试 Gemini API"""
    API_KEY = "AIzaSyBQkCLkovABnjZeOVRV-FoxkFPkayvNXVQ"
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": API_KEY
    }
    
    # 测试简单请求
    body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": "你好，请简单介绍一下你自己"}]
        }]
    }
    
    try:
        print("测试 Gemini API 连接...")
        response = requests.post(API_URL, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        print("✅ API 连接成功！")
        print("响应:", result["candidates"][0]["content"]["parts"][0]["text"])
        return True
        
    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        return False

def test_excel_analysis():
    """测试 Excel 分析功能"""
    try:
        print("\n测试 Excel 分析接口...")
        
        test_data = {
            "columns": ["日期", "销售额", "产品类别", "客户数量"],
            "data_sample": "示例数据",
            "analysis_type": "comprehensive"
        }
        
        response = requests.post(
            "http://localhost:8000/analyze_excel",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Excel 分析接口测试成功！")
            print("分析结果预览:", result.get("analysis", "")[:200] + "...")
            return True
        else:
            print(f"❌ Excel 分析接口测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Excel 分析接口测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试 Gemini 集成...")
    
    # 测试 API 连接
    api_ok = test_gemini_api()
    
    if api_ok:
        print("\n启动本地服务器进行完整测试...")
        print("请运行: uvicorn server_gemini:app --host 0.0.0.0 --port 8000")
        print("然后运行: python test_gemini.py")
    else:
        print("\n请检查 API Key 和网络连接")