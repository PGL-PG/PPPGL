# Excel 数据分析平台

一个基于 Flask + React 的智能 Excel 数据分析平台，支持多维度数据分析、可视化图表生成和归因诊断。

## 功能特性

- 📊 Excel 文件上传解析，支持多 sheet 页和列选择
- 🤖 自动识别数据类型（数值、时间、分类等）
- 📈 交互式可视化图表（折线图、柱状图、饼图、散点图）
- 🔍 数据归因诊断和统计分析
- 🎨 简洁的用户界面设计

## 安装和启动

### 方法一：使用自动化脚本（推荐）

1. **安装依赖包**
   ```bash
   # 双击运行或在命令行执行
   install_packages.bat
   ```

2. **测试依赖是否安装成功**
   ```bash
   python test_dependencies.py
   ```

3. **启动应用**
   ```bash
   # 双击运行或在命令行执行
   start.bat
   ```

### 方法二：手动启动

1. **安装后端依赖**
   ```bash
   cd backend
   pip install pandas openpyxl numpy Flask Flask-CORS
   ```

2. **启动后端服务**
   ```bash
   cd backend
   python app.py
   ```

3. **启动前端服务**
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **访问应用**
   打开浏览器访问 http://localhost:3000

## 使用说明

1. 上传您的 Excel 文件（支持 .xlsx 和 .xls 格式）
2. 选择要分析的工作表和列
3. 查看自动生成的数据分析和可视化图表
4. 进行归因诊断分析，了解数据的关联性和异常值

## 技术栈

- 后端：Python Flask + pandas + openpyxl + numpy
- 前端：React + Ant Design + ECharts
- 数据分析：基于统计学方法的本地分析

## 注意事项

- 确保已安装 Python 3.7+ 和 Node.js 14+
- 如果网络连接有问题，可以使用国内镜像源安装依赖
- 上传的文件会临时保存在 backend/uploads 目录中