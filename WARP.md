# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 项目概述

这是一个基于 **Flask + React + Gemini AI** 的专业 Excel 数据分析平台，提供智能数据分析、可视化图表生成和业务洞察功能。

### 核心功能
- 🤖 **AI 驱动分析**: 集成 Google Gemini 2.0 Flash 模型进行深度数据洞察
- 📊 **智能数据分析**: 自动识别销量、品牌、产品等业务字段，提供专业级分析
- 📈 **可视化图表**: 自动生成柱状图、饼图、散点图等多种图表类型
- 🔍 **归因分析**: 深度分析影响关键指标的驱动因素
- 🎯 **商业洞察**: 提供市场集中度、竞争格局等业务建议

## 开发环境要求

- **Python**: 3.7+ (后端 Flask 应用)
- **Node.js**: 14+ (前端 React 应用)
- **Gemini API Key**: 需要有效的 Google AI Studio API 密钥

## 常用开发命令

### 快速启动（推荐）
```bash
# 安装所有依赖
install.bat

# 启动Excel助手优化版（推荐！专注实用分析）
start_excel_optimized.bat

# 启动完整系统（包含 Gemini 服务）
start_gemini_system.bat

# 或者启动基础版本
start.bat
```

### 手动启动服务

#### 启动 Gemini AI 服务
```bash
# 需要安装 FastAPI 和 uvicorn
pip install fastapi uvicorn
uvicorn server_gemini:app --host 0.0.0.0 --port 8000
```

#### 启动后端服务
```bash
cd backend
pip install -r requirements.txt
python app.py  # 基础版本
# 或者
python app_gemini_proxy.py  # Gemini 代理版本
```

#### 启动前端服务
```bash
cd frontend
npm install
npm start
```

### 测试命令
```bash
# 测试 Gemini API 连接
python test_gemini.py

# 测试完整系统功能
python test_full_system.py
```

### 依赖管理
```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖  
cd frontend
npm install
```

## 项目架构

### 后端架构 (Python/Flask)

#### 核心文件结构
- **`server_gemini.py`**: FastAPI 服务，处理 Gemini AI 调用
- **`backend/app_excel_optimized.py`**: 🌟Excel助手优化版后端，专注实用分析
- **`backend/excel_analysis_engine.py`**: 🌟Excel分析引擎，实现业务级分析逻辑
- **`backend/app.py`**: 原始版本后端，包含复杂统计分析
- **`backend/app_gemini_proxy.py`**: Flask 代理服务，转发请求到 Gemini 服务
- **`backend/requirements.txt`**: Python 依赖包

#### 分析引擎架构
项目包含两套并行的分析系统：

1. **本地分析引擎** (`app.py`)
   - 智能字段识别和分类
   - 专业级统计分析（HHI指数、基尼系数、帕累托分析）
   - 多维度交叉分析
   - 市场竞争格局分析

2. **AI 增强分析** (`server_gemini.py`)
   - 基于 Gemini 2.0 Flash 的智能洞察
   - 自然语言生成的分析报告
   - 自动化图表建议
   - 深度归因分析

#### 关键分析功能
- **智能字段分类**: 自动识别销量、品牌、产品、价格等业务字段
- **分析策略选择**: 根据数据特征智能选择最佳分析方法
- **专业指标计算**: 市场集中度(HHI)、多样化指数、效率分析
- **可视化建议**: 智能推荐图表类型和维度组合

### 前端架构 (React/JavaScript)

#### 核心组件
- **`frontend/src/App.js`**: 主应用组件
- **`frontend/src/components/FileUpload.js`**: 文件上传组件
- **`frontend/src/components/DataAnalysis.js`**: 数据分析展示组件
- **`frontend/src/components/AttributionAnalysis.js`**: 归因分析组件
- **`frontend/src/components/ChartDisplay.js`**: 图表展示组件

#### UI 框架
- **Ant Design**: 主要 UI 组件库
- **ECharts**: 图表可视化库
- **Axios**: HTTP 请求处理

### 服务通信架构

```
Frontend (React:3000) 
    ↓ HTTP requests
Backend Proxy (Flask:5000)
    ↓ Forward requests  
Gemini Service (FastAPI:8000)
    ↓ API calls
Google Gemini API
```

## 数据分析能力

### 支持的文件格式
- Excel (.xlsx, .xls)
- CSV (.csv)

### 智能分析类型
- **业务绩效分析**: 销量排行、市场份额、品牌竞争
- **统计分析**: 相关性、分布分析、异常值检测
- **时间序列分析**: 趋势分析、季节性模式
- **归因分析**: 关键驱动因素识别、敏感性分析

### 专业指标
- HHI 市场集中度指数
- 基尼系数（不平等程度）
- 香农多样性指数
- 帕累托分析（80/20法则）
- 效率分析和竞争态势

## API 接口

### Gemini 服务接口 (端口 8000)
- `POST /upload`: 文件上传和预览分析
- `POST /analyze`: 完整数据分析
- `POST /attribution`: 归因分析
- `GET /health`: 服务健康检查

### Flask 代理接口 (端口 5000)  
- `POST /api/upload`: 文件上传代理
- `POST /api/analyze`: 数据分析代理
- `POST /api/attribution`: 归因分析代理

### Excel助手优化版接口 (端口 5001) 🌟推荐
- `POST /api/upload`: 智能文件上传和业务场景识别
- `POST /api/analyze`: Excel级别实用数据分析
- `POST /api/attribution`: 简化的影响因素分析
- `GET /api/health`: 服务状态检查

## 开发注意事项

### Gemini API 配置
- API Key 当前硬编码在 `server_gemini.py` 中
- 生产环境应使用环境变量管理密钥
- API 调用有超时设置（60-120秒）

### 数据处理
- 支持大文件处理（分块读取）
- 自动数据类型检测和转换
- 智能缺失值处理
- JSON 序列化安全处理

### 错误处理
- 完善的异常处理机制
- API 调用失败时的降级策略
- 用户友好的错误信息

### 性能优化
- 数据预览限制（前100行）
- 图表数据限制（避免前端渲染过载）
- 异步处理长时间分析任务

## 服务地址

开发环境默认端口：
- **前端**: http://localhost:3000
- **后端代理**: http://localhost:5000  
- **Gemini 服务**: http://localhost:8000

## 调试建议

### 常见问题排查
1. **Gemini API 连接失败**: 运行 `python test_gemini.py` 测试
2. **前端无法连接后端**: 检查 CORS 配置和端口冲突
3. **文件上传失败**: 检查文件格式和大小限制
4. **分析结果为空**: 检查数据格式和字段名称

### 日志查看
- 后端日志在对应的命令行窗口中显示
- 前端开发者工具中查看网络请求
- Gemini 服务日志包含详细的 API 调用信息

## 项目特色

### 🌟 Excel数据分析助手（核心特色）
该项目专注于**Excel用户的实际需求**，提供贴近业务场景的实用分析：

#### Excel级别的分析能力
- **智能业务场景识别**: 自动识别销售、产品、财务、人员等业务数据类型
- **实用统计分析**: 求和、平均、排序、分组等Excel用户熟悉的分析方法
- **排行榜生成**: 自动生成有意义的排名分析（销量排行、品牌对比等）
- **多维度对比**: 支持不同颗粒度的数据分析（概览→细分→深度）

#### 业务导向的洞察
- **实用图表建议**: 推荐柱状图、饼图、折线图等常用图表组合
- **业务场景定制**: 针对销售、产品、财务等场景提供专门的分析模板
- **简单直白的结论**: 避免复杂的统计术语，提供可执行的业务建议

### 技术创新点
- **三层架构**: Excel分析引擎 + 本地统计 + AI增强分析
- **智能字段识别**: 自动识别金额、数量、分类、时间等业务字段类型
- **业务场景适配**: 根据数据特征自动选择最合适的分析策略
- **渐进式分析**: 从概览到深度的多层次分析框架

### 💡 与传统方案的区别
- ❌ **避免过度复杂**: 不使用HHI指数、基尼系数等专业统计指标
- ✅ **专注实用价值**: 像Excel透视表一样简单直观的分析结果
- ✅ **业务导向**: 每个分析结果都对应具体的业务问题和改进建议
- ✅ **渐进式深入**: 用户可以选择分析深度，从快速概览到详细剖析
