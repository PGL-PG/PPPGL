#!/usr/bin/env python3
"""
检查 Gemini API Key 是否配置正确
"""
import os
import requests

def check_gemini_api_key():
    """检查 Gemini API Key 配置"""
    print("🔍 检查 Gemini API Key 配置...")
    
    # 从环境变量或文件中读取 API Key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("❌ API Key 未配置!")
        print("请通过以下方式之一配置 API Key:")
        print("1. 设置环境变量: set GEMINI_API_KEY=your_api_key")
        print("2. 修改 server_gemini.py 文件中的 API_KEY 变量")
        print("3. 创建 .env 文件 (参考 .env.example)")
        print("\n📝 获取 API Key: https://aistudio.google.com/app/apikey")
        return False
    
    # 测试 API 连接
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    
    test_body = {
        "contents": [{
            "role": "user",
            "parts": [{"text": "Hello"}]
        }]
    }
    
    try:
        print("🌐 测试 API 连接...")
        response = requests.post(api_url, headers=headers, json=test_body, timeout=10)
        
        if response.status_code == 200:
            print("✅ API Key 配置正确，连接成功！")
            return True
        elif response.status_code == 400:
            print("❌ API Key 无效或格式错误")
            return False
        elif response.status_code == 403:
            print("❌ API Key 权限不足或已被禁用")
            return False
        else:
            print(f"❌ API 连接失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ API 连接超时，请检查网络连接")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络连接失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Excel 数据分析助手 - API Key 检查工具")
    print("=" * 50)
    
    if check_gemini_api_key():
        print("\n✅ 系统配置正确，可以使用 start_excel_optimized.bat 启动系统")
    else:
        print("\n❌ 请先配置 API Key 后再启动系统")
    
    print("=" * 50)
    input("按任意键退出...")
