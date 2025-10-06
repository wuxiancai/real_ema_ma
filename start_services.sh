#!/bin/bash

# 真实交易系统服务启动脚本
# 用于systemd服务，同时启动交易系统和Web监控

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志函数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1"
}

# 创建必要目录
mkdir -p logs

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    log_info "虚拟环境已激活"
else
    log_error "未找到虚拟环境目录 venv"
    exit 1
fi

# 检查必要文件
if [ ! -f "main.py" ]; then
    log_error "未找到 main.py 文件"
    exit 1
fi

if [ ! -f "web_monitor.py" ]; then
    log_error "未找到 web_monitor.py 文件"
    exit 1
fi

if [ ! -f "config.py" ]; then
    log_error "未找到 config.py 文件"
    exit 1
fi

# PID文件
TRADING_PID_FILE="$SCRIPT_DIR/.trading_pid"
WEB_PID_FILE="$SCRIPT_DIR/.web_pid"

# 清理函数
cleanup() {
    log_info "正在停止服务..."
    
    # 停止交易系统
    if [ -f "$TRADING_PID_FILE" ]; then
        TRADING_PID=$(cat "$TRADING_PID_FILE")
        if kill -0 "$TRADING_PID" 2>/dev/null; then
            log_info "停止交易系统 (PID: $TRADING_PID)"
            kill "$TRADING_PID"
            # 等待进程结束
            for i in {1..10}; do
                if ! kill -0 "$TRADING_PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # 强制终止
            if kill -0 "$TRADING_PID" 2>/dev/null; then
                log_warn "强制终止交易系统进程"
                kill -9 "$TRADING_PID" 2>/dev/null || true
            fi
        fi
        rm -f "$TRADING_PID_FILE"
    fi
    
    # 停止Web监控
    if [ -f "$WEB_PID_FILE" ]; then
        WEB_PID=$(cat "$WEB_PID_FILE")
        if kill -0 "$WEB_PID" 2>/dev/null; then
            log_info "停止Web监控 (PID: $WEB_PID)"
            kill "$WEB_PID"
            # 等待进程结束
            for i in {1..10}; do
                if ! kill -0 "$WEB_PID" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            # 强制终止
            if kill -0 "$WEB_PID" 2>/dev/null; then
                log_warn "强制终止Web监控进程"
                kill -9 "$WEB_PID" 2>/dev/null || true
            fi
        fi
        rm -f "$WEB_PID_FILE"
    fi
    
    log_info "服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT

# 启动交易系统主程序
log_info "启动交易系统主程序..."
python main.py > logs/trading_system.log 2>&1 &
TRADING_PID=$!
echo "$TRADING_PID" > "$TRADING_PID_FILE"

# 等待交易系统启动
sleep 3

# 检查交易系统是否启动成功
if ! kill -0 "$TRADING_PID" 2>/dev/null; then
    log_error "交易系统启动失败"
    exit 1
fi

log_info "交易系统启动成功 (PID: $TRADING_PID)"

# 启动Web监控程序
log_info "启动Web监控程序..."
python web_monitor.py > logs/web_monitor.log 2>&1 &
WEB_PID=$!
echo "$WEB_PID" > "$WEB_PID_FILE"

# 等待Web监控启动
sleep 3

# 检查Web监控是否启动成功
if ! kill -0 "$WEB_PID" 2>/dev/null; then
    log_error "Web监控启动失败"
    # 停止交易系统
    if kill -0 "$TRADING_PID" 2>/dev/null; then
        kill "$TRADING_PID"
    fi
    rm -f "$TRADING_PID_FILE"
    exit 1
fi

log_info "Web监控启动成功 (PID: $WEB_PID)"
log_info "Web监控地址: http://localhost:8888"

log_info "所有服务启动完成"
log_info "交易系统 PID: $TRADING_PID"
log_info "Web监控 PID: $WEB_PID"

# 监控进程状态
while true; do
    # 检查交易系统进程
    if ! kill -0 "$TRADING_PID" 2>/dev/null; then
        log_error "交易系统进程异常退出"
        cleanup
    fi
    
    # 检查Web监控进程
    if ! kill -0 "$WEB_PID" 2>/dev/null; then
        log_error "Web监控进程异常退出"
        cleanup
    fi
    
    # 每30秒检查一次
    sleep 30
done