#!/bin/bash

# 简单的交易系统部署脚本
# 一次性搞定，不搞复杂的

set -e

echo "开始部署交易系统..."

# 基本变量
PROJECT_DIR="/home/ubuntu/real_ema_ma"
SERVICE_NAME="real-ema-ma"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "安装Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 创建启动脚本
echo "创建启动脚本..."
cat > start_services.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/real_ema_ma
source venv/bin/activate
python main.py > logs/main.log 2>&1 &
sleep 2
python web_monitor.py > logs/web.log 2>&1 &
wait
EOF

chmod +x start_services.sh

# 创建systemd服务
echo "创建systemd服务..."
sudo mkdir -p /etc/systemd/system
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Real Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/real_ema_ma
ExecStart=/home/ubuntu/real_ema_ma/start_services.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd并启用服务
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service

echo "部署完成！"
echo "启动服务: sudo systemctl start ${SERVICE_NAME}"
echo "查看状态: sudo systemctl status ${SERVICE_NAME}"
echo "查看日志: sudo journalctl -u ${SERVICE_NAME} -f"
