from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
import numpy as np
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# CORS处理
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
GEMINI_SERVER_URL = "http://localhost:8001"  # Gemini 服务地址

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """文件上传接口 - 转发给 Gemini 服务"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 将文件转发给 Gemini 服务
            files = {'file': (file.filename, file.stream, file.content_type)}
            
            response = requests.post(
                f"{GEMINI_SERVER_URL}/upload",
                files=files,
                timeout=60
            )
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': f'Gemini 服务错误: {response.text}'}), 500
        else:
            return jsonify({'error': '不支持的文件格式'}), 400
            
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """数据分析接口 - 转发给 Gemini 服务"""
    try:
        data = request.get_json()
        
        # 转发给 Gemini 分析服务
        response = requests.post(
            f"{GEMINI_SERVER_URL}/analyze",
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Gemini 分析服务错误: {response.text}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

@app.route('/api/attribution', methods=['POST'])
def attribution_analysis():
    """归因分析接口 - 转发给 Gemini 服务"""
    try:
        data = request.get_json()
        
        # 构建归因分析请求
        attribution_request = {
            "columns": data.get("available_columns", []),
            "target_metric": data.get("target_metric"),
            "analysis_type": "attribution_analysis",
            "custom_requirements": f"请对{data.get('target_metric')}进行归因分析，识别关键驱动因素"
        }
        
        response = requests.post(
            f"{GEMINI_SERVER_URL}/analyze",
            json=attribution_request,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            # 转换为前端期望的格式
            return jsonify({
                "status": "success",
                "attribution_analysis": result.get("analysis_report", ""),
                "key_drivers": [
                    "基于 Gemini 的智能归因分析",
                    "识别关键驱动因素",
                    "提供优化建议"
                ],
                "recommendations": [
                    "根据分析结果优化关键指标",
                    "关注主要驱动因素的变化",
                    "建立监控和预警机制"
                ]
            })
        else:
            return jsonify({'error': f'归因分析失败: {response.text}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'归因分析失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 检查 Gemini 服务状态
        response = requests.get(f"{GEMINI_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            return jsonify({
                "status": "healthy",
                "backend": "Flask Proxy",
                "gemini_service": "connected"
            })
        else:
            return jsonify({
                "status": "degraded",
                "backend": "Flask Proxy",
                "gemini_service": "disconnected"
            }), 503
    except:
        return jsonify({
            "status": "error",
            "backend": "Flask Proxy",
            "gemini_service": "unreachable"
        }), 503

if __name__ == '__main__':
    app.run(debug=True, port=5000)