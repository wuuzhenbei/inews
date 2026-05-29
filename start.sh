#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  NewsAgg - 实时新闻聚合 AI智能评级"
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] 未检测到Python，请先安装Python 3.10+"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)

# 虚拟环境
if [ ! -d "venv" ]; then
    echo "[INFO] 首次运行，创建虚拟环境..."
    $PYTHON -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

mkdir -p data logs

echo ""
echo "[INFO] 启动服务..."
echo "[INFO] 浏览器访问: http://localhost:5000"
echo "[INFO] 按 Ctrl+C 停止服务"
echo ""

python app.py
