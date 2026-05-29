@echo off
chcp 65001 >nul
echo ========================================
echo   NewsAgg - 实时新闻聚合 AI智能评级
echo ========================================
echo.

cd /d "%~dp0"

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未检测到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

:: 检查依赖
if not exist "venv" (
    echo [INFO] 首次运行，创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: 确保目录存在
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo [INFO] 启动服务...
echo [INFO] 浏览器访问: http://localhost:5000
echo [INFO] 按 Ctrl+C 停止服务
echo.

python app.py
pause
