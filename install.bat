@echo off
echo 安装 Excel 数据分析平台依赖...
echo.

echo 1. 安装后端依赖...
cd backend
pip install -r requirements.txt
cd ..

echo.
echo 2. 安装前端依赖...
cd frontend
npm install
cd ..

echo.
echo 安装完成！
echo 运行 start.bat 启动平台
pause