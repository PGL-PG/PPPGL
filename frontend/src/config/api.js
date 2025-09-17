// API 配置文件
export const API_CONFIG = {
  // 优化版后端 (推荐)
  OPTIMIZED_BACKEND: 'http://localhost:5001',
  
  // 原版后端
  ORIGINAL_BACKEND: 'http://localhost:5000',
  
  // Gemini 服务
  GEMINI_SERVICE: 'http://localhost:8000',
  
  // 使用哪个后端 (true=优化版, false=原版)
  USE_OPTIMIZED: false
};

// 获取当前使用的API基础URL
export const getApiBaseUrl = () => {
  return API_CONFIG.USE_OPTIMIZED 
    ? API_CONFIG.OPTIMIZED_BACKEND 
    : API_CONFIG.ORIGINAL_BACKEND;
};

// API 端点
export const API_ENDPOINTS = {
  UPLOAD: '/api/upload',
  ANALYZE: '/api/analyze', 
  ATTRIBUTION: '/api/attribution',
  HEALTH: '/api/health'
};

// 完整的API URL
export const getApiUrl = (endpoint) => {
  return `${getApiBaseUrl()}${endpoint}`;
};
