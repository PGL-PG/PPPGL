@echo off
echo 启动 AI Excel 分析系统 (Gemini 版)
echo =====================================

echo.
echo 1. 启动 Gemini 分析服务...
start "Gemini Service" cmd /k "cd /d %~dp0 && .\venv\Scripts\activate.bat && python server_gemini.py"

echo.
echo 等待 Gemini 服务启动...
timeout /t 5 /nobreak > nul

echo.
echo 2. 启动后端代理服务...
start "Backend Proxy" cmd /k "cd /d %~dp0\backend && ..\venv\Scripts\activate.bat && python app_gemini_proxy.py"

echo.
echo 等待后端服务启动...
timeout /t 3 /nobreak > nul

echo.
echo 3. 启动前端服务...
start "Frontend" cmd /k "cd /d %~dp0\frontend && npm start"

echo.
echo =====================================
echo 系统启动完成！
echo.
echo 服务地址：
echo - 前端界面: http://localhost:3000
echo - 后端 API: http://localhost:5000
echo - Gemini 服务: http://localhost:8000
echo.
echo 请等待所有服务完全启动后使用
echo =====================================

pause