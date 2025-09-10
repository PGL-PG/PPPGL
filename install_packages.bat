@echo off
echo 正在安装Python依赖包...

echo 尝试使用默认源安装...
pip install pandas
if %errorlevel% neq 0 (
    echo 默认源失败，尝试使用清华镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas
)

pip install openpyxl
if %errorlevel% neq 0 (
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openpyxl
)

pip install numpy
if %errorlevel% neq 0 (
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy
)

pip install Flask-CORS
if %errorlevel% neq 0 (
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple Flask-CORS
)

echo 安装完成！
pause