# AI Excel 数据分析助手

一个集成 Gemini AI 的智能 Excel 数据分析工具，支持命令行简化版和Web界面完整版两种使用方式。

## ✨ 功能特色

- **智能分析**: 基于 Gemini 2.0 Flash 模型的专业数据分析
- **直接调用**: 无复杂架构，直接调用Gemini API
- **多种使用方式**: 命令行简化版和Web界面完整版
- **自动识别**: 智能识别业务字段（销量、品牌、产品、价格等）
- **可视化图表**: 自动生成排行榜、饼图、趋势图等
- **专业洞察**: 提供具体的业务分析结果和建议
- **基础数据概览**: 采用文本形式展示，简洁清晰

## 🚀 快速开始

### 方式一：命令行简化版（推荐）

1. **配置 API Key**
   ```bash
   python check_api_key.py
   ```
   或手动设置：
   ```bash
   set GEMINI_API_KEY=您的API_KEY
   ```

2. **运行分析**
   ```bash
   python simple_gemini_demo.py
   ```
   输入Excel文件名即可开始分析。

### 方式二：Web界面完整版

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```

2. **启动服务**
   ```bash
   # 终端 1: 后端服务
   cd backend && python app_excel_optimized.py
   
   # 终端 2: 前端服务
   cd frontend && npm start
   ```

3. **访问应用**
   打开浏览器访问 http://localhost:3000## 📝 使用说明

### 命令行版
- 将Excel文件放在项目目录下
- 运行 `simple_gemini_demo.py`
- 输入文件名，等待AI分析结果

### Web界面版
- 上传Excel文件（支持.xlsx和.xls格式）
- 选择要分析的工作表和列
- 查看自动生成的数据分析和可视化图表
- 进行归因诊断分析，了解数据的关联性和异常值

## 📊 核心分析功能

### 智能字段识别
系统自动识别常见的业务字段：
- **销量字段**: 销量、数量、quantity、sales、售出、销售
- **品牌字段**: 品牌、brand、厂商、manufacturer
- **产品字段**: 产品、product、商品、名称、name
- **价格字段**: 价格、price、单价、金额、amount

### 基础数据概览
采用文本形式展示，包括：
- **数据规模**: 总行数、字段数、业务场景识别
- **字段统计**: 数值字段（均值、中位数、取值范围）
- **分类统计**: 不同值个数、最常见值及出现次数
- **数据质量**: 缺失值统计、重复值检测

### 专业分析报告
- **AI洞察**: 基于Gemini的智能分析结果
- **排行榜分析**: 自动生成品牌、产品等排行榜
- **分组统计**: 按分类字段进行数据分组统计
- **可视化图表**: 柱状图、饼图、折线图等
- **归因诊断**: 深入分析影响目标指标的关键因素

## 🛠️ 技术架构

### 技术栈
- **后端**: Python Flask + pandas + openpyxl + numpy
- **前端**: React + Ant Design + ECharts  
- **AI引擎**: Google Gemini 2.0 Flash API
- **数据处理**: pandas + numpy 本地分析

### 项目结构
```
AI_Excel/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖包
├── .env.example                # 环境变量模板
├── check_api_key.py            # API Key配置检查工具
├── simple_gemini_demo.py       # 命令行简化版
├── server_gemini.py            # Gemini AI服务（可选）
├── backend/                    # 后端服务
│   ├── app_excel_optimized.py  # 主服务文件（直接调用Gemini）
│   ├── excel_analysis_engine.py # 数据分析引擎
│   ├── app.py                  # 备用后端服务
│   └── app_gemini_proxy.py     # 代理服务
└── frontend/                   # React前端
    ├── package.json
    └── src/
        ├── App.js
        └── components/
            ├── FileUpload.js           # 文件上传组件
            ├── DataAnalysis.js         # 数据分析界面
            ├── ChartDisplay.js         # 图表显示组件
            └── AttributionAnalysis.js  # 归因分析组件
```

### 架构设计
- **直接调用**: `app_excel_optimized.py` 直接调用Gemini API，无需中间服务
- **模块化设计**: 数据分析逻辑独立封装在`excel_analysis_engine.py`
- **前后端分离**: React前端 + Flask后端，通过API通信
- **多端支持**: 支持命令行和Web界面两种使用方式

## 📝 注意事项

- 需要 Python 3.7+ 和 Node.js 14+
- 需要有效的 Gemini API Key
- 上传的文件会临时保存在 backend/uploads 目录
- 网络问题可使用国内镜像源安装依赖
- 支持 .xlsx 和 .xls 格式的Excel文件

## 🌟 特色亮点

1. **直接调用**: 无复杂的中间服务，直接调用Gemini API
2. **简洁展示**: 基础数据概览使用文本形式，简洁清晰
3. **智能识别**: 自动识别业务字段和数据类型
4. **专业分析**: 提供具体的业务分析结果，而非抽象描述
5. **多种使用方式**: 支持命令行和Web界面，满足不同需求