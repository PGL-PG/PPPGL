@echo off
echo 启动 Excel 数据分析平台...
echo.

echo 检查Python依赖...
python -c "import pandas, openpyxl, numpy, flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo 缺少必要的Python包，请先运行 install_packages.bat
    pause
    exit /b 1
)

echo 1. 启动后端服务...
start "Backend" cmd /k "cd backend && python app.py"

echo 2. 等待后端启动...
timeout /t 3 /nobreak > nul

echo 3. 安装前端依赖并启动...
start "Frontend" cmd /k "cd frontend && npm install && npm start"

echo.
echo 平台启动中...
echo 后端地址: http://localhost:5000
echo 前端地址: http://localhost:3000
echo 请上传您的Excel文件进行分析
echo.
pause