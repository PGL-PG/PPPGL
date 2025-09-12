@echo off
echo 启动 Excel 数据分析平台...
echo.

echo 1. 启动后端服务...
start "Backend" cmd /k "cd backend && python app.py"

echo 2. 等待后端启动...
timeout /t 3 /nobreak > nul

echo 3. 启动前端服务...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo 平台启动中...
echo 后端地址: http://localhost:5000
echo 前端地址: http://localhost:3000
echo.
echo 请在浏览器中访问 http://localhost:3000
pause