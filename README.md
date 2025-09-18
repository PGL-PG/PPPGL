# Excel 智能分析系统

一个集成 Gemini AI 的智能 Excel 数据分析工具，具备智能场景匹配和精准提示词生成能力。

## ✨ 核心功能

### 智能场景匹配
- **多维度数据指纹分析**: 基于字段特征、内容特征、统计特征和语义特征
- **相似度匹配算法**: 精确识别电商、汽车、财务等业务场景
- **场景置信度计算**: 提供匹配结果的可信度评估

### 场景化提示词引擎
- **专业化提示词模板**: 针对不同场景生成专业化的 Gemini 提示词
- **上下文感知分析**: 根据数据特征智能选择分析角度
- **数据内容优化**: 确保 Gemini 获得完整准确的数据信息

### 智能分析流程
- **场景匹配 → 精准提示词 → Gemini 主导分析**
- **可视化图表自动生成**: 排行榜、分布图、相关性分析
- **专业报告样式**: 智能高亮显示和结构化展示

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd AI_Excel

# 安装 Python 依赖
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 2. 配置 API Key
在 `backend/enhanced_analysis_api.py` 中配置您的 Gemini API Key：
```python
self.api_key = "YOUR_GEMINI_API_KEY"
```

### 3. 启动系统
```bash
# 终端 1: 启动后端服务
cd backend
python app.py

# 终端 2: 启动前端服务
cd frontend
npm start
```

### 4. 访问应用
打开浏览器访问: http://localhost:3000

## 📊 使用说明

1. **上传 Excel 文件**: 支持 .xlsx 和 .xls 格式
2. **选择工作表**: 从上传的文件中选择要分析的工作表
3. **智能分析**: 系统自动进行场景匹配和分析
4. **查看结果**: 浏览 AI 生成的分析报告和可视化图表

## 🛠️ 技术架构

### 后端模块
```
backend/
├── app.py                           # 主 Flask 应用服务器
├── enhanced_analysis_api.py         # 增强版分析 API
├── intelligent_scenario_matcher.py  # 智能场景匹配系统
└── scenario_prompt_engine.py        # 场景化提示词引擎
```

### 前端组件
```
frontend/src/components/
├── FileUpload.js      # 文件上传组件
├── DataAnalysis.js    # 数据分析主界面
└── ChartDisplay.js    # 图表显示组件
```

### 技术栈
- **后端**: Python Flask + pandas + numpy + scikit-learn
- **前端**: React + Ant Design + ECharts
- **AI 引擎**: Google Gemini 2.0 Flash API
- **数据处理**: pandas + numpy + openpyxl

## 📝 核心特性

### 智能场景识别
系统支持以下业务场景的智能识别：
- **电商数据分析**: 销量、品牌、产品、价格等
- **汽车销售分析**: 车型、销量、品牌等
- **财务业绩分析**: 收入、成本、利润等
- **市场竞争分析**: 市场份额、排名、竞争对手等

### 分析功能
- **排行榜分析**: 自动生成品牌、产品等排行榜
- **分布情况分析**: 市场份额和竞争格局分析
- **相关性分析**: 数值字段间的相关关系分析
- **智能洞察**: 基于 Gemini 的专业分析结果

### 美观展示
- **智能高亮**: 数字、品牌、关键词自动高亮
- **专业报告样式**: 结构化、有条理的分析结果展示
- **响应式设计**: 支持各种屏幕尺寸

## 📝 注意事项

1. **环境要求**: Python 3.7+ 和 Node.js 14+
2. **API Key**: 需要有效的 Gemini API Key
3. **文件支持**: 支持 .xlsx 和 .xls 格式的 Excel 文件
4. **数据安全**: 上传的文件会临时保存在 backend/uploads 目录

## 🌟 项目亮点

1. **智能化**: 基于相似度算法的智能场景匹配
2. **专业化**: 针对不同业务场景的专业化分析
3. **自动化**: 全自动的分析流程，无需手动配置
4. **可视化**: 丰富的图表展示和互动体验
5. **高质量**: 基于 Gemini 2.0 Flash 的高质量分析结果## 📝 使用说明

### 命令行版
- 当前版本专注于Web界面，命令行版本已简化

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
├── .env.example                # 环境变量模板
├── check_api_key.py            # API Key配置检查工具
├── backend/                    # 后端服务
│   ├── app.py                  # 主Flask应用服务器
│   ├── enhanced_analysis_api.py # 增强版分析API
│   ├── intelligent_scenario_matcher.py # 智能场景匹配系统
│   ├── scenario_prompt_engine.py # 场景化提示词引擎
│   └── requirements.txt        # 后端依赖
└── frontend/                   # React前端
    ├── package.json
    └── src/
        ├── App.js
        └── components/
            ├── FileUpload.js    # 文件上传组件
            ├── DataAnalysis.js  # 数据分析界面
            └── ChartDisplay.js  # 图表显示组件
```

### 架构设计
- **智能分析**: `app.py` 集成智能场景匹配和分析API
- **模块化设计**: 场景匹配、提示词引擎、分析API独立封装
- **前后端分离**: React前端 + Flask后端，通过API通信
- **专注Web界面**: 提供完整的Web分析体验

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