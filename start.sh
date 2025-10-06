#!/bin/bash

# 真实交易系统启动脚本

echo "=========================================="
echo "真实交易系统 - EMA/MA交叉策略"
echo "=========================================="

# 检测操作系统
echo "检测操作系统..."
OS_TYPE=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    echo "检测到操作系统: macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    echo "检测到操作系统: Linux"
else
    echo "警告: 未识别的操作系统类型: $OSTYPE"
    echo "将使用默认配置继续运行..."
    OS_TYPE="unknown"
fi

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 虚拟环境名称
VENV_NAME="venv"

# 检查虚拟环境是否存在
echo "检查虚拟环境..."
if [ ! -d "$VENV_NAME" ]; then
    echo "虚拟环境不存在，正在创建虚拟环境: $VENV_NAME"
    python3 -m venv $VENV_NAME
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败"
        exit 1
    fi
    echo "虚拟环境创建成功"
fi

# 根据操作系统激活虚拟环境
echo "激活虚拟环境..."
if [[ "$OS_TYPE" == "macos" ]] || [[ "$OS_TYPE" == "linux" ]] || [[ "$OS_TYPE" == "unknown" ]]; then
    # Unix-like 系统 (macOS, Linux)
    source $VENV_NAME/bin/activate
else
    # 其他系统的处理
    source $VENV_NAME/bin/activate
fi

if [ $? -ne 0 ]; then
    echo "错误: 激活虚拟环境失败"
    exit 1
fi
echo "虚拟环境已激活: $VENV_NAME"

# 检查并安装依赖
echo "检查Python依赖..."
python -c "import pandas, numpy, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装依赖包..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 安装依赖包失败"
        exit 1
    fi
    echo "依赖包安装完成"
fi

# 检查配置文件
if [ ! -f "config.py" ]; then
    echo "错误: 未找到配置文件 config.py"
    exit 1
fi

# 创建日志目录
mkdir -p logs

echo "交易系统已部署"
