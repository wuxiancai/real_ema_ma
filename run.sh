#!/bin/bash
# -*- coding: utf-8 -*-
#
# 交易系统启动脚本
# 同时启动交易系统主程序和Web监控界面
#

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}$1${NC}"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python3"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装，请先安装pip3"
        exit 1
    fi
    
    log_info "Python环境检查通过"
}

# 检查依赖
check_dependencies() {
    log_info "检查Python依赖..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ -d "venv" ]; then
        log_info "发现虚拟环境，激活中..."
        source venv/bin/activate
    else
        log_warn "未发现虚拟环境，使用系统Python"
    fi
    
    # 安装依赖
    pip3 install -r requirements.txt > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "依赖安装完成"
    else
        log_error "依赖安装失败"
        exit 1
    fi
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f "config.py" ]; then
        log_error "config.py 配置文件不存在"
        exit 1
    fi
    
    # 检查API密钥配置
    if grep -q "your_api_key_here" config.py || grep -q "your_secret_key_here" config.py; then
        log_error "请先在config.py中配置您的币安API密钥"
        exit 1
    fi
    
    log_info "配置文件检查通过"
}

# 启动交易系统
start_trading_system() {
    log_header "启动交易系统主程序..."
    
    # 检查是否为真实交易模式
    if grep -q "TEST_MODE = False" config.py; then
        log_warn "检测到真实交易模式！"
        echo -n "这将使用真实资金进行交易，确认启动？(yes/no): "
        read -r confirm
        if [ "$confirm" != "yes" ]; then
            log_info "用户取消启动"
            exit 0
        fi
        
        # 真实交易模式：使用screen在后台运行，避免交互问题
        screen -dmS trading_system bash -c "cd '$SCRIPT_DIR' && echo 'yes' | python3 main.py > logs/trading_system.log 2>&1"
        
        # 等待启动
        sleep 5
        
        # 检查screen会话是否存在
        if screen -list | grep -q "trading_system"; then
            log_info "交易系统主程序启动成功 (Screen会话: trading_system)"
            echo "trading_system" > .trading_session
        else
            log_error "交易系统主程序启动失败"
            exit 1
        fi
    else
        # 测试模式直接启动
        nohup python3 main.py > logs/trading_system.log 2>&1 &
        TRADING_PID=$!
        
        # 等待启动
        sleep 3
        
        # 检查进程是否启动成功
        if kill -0 $TRADING_PID 2>/dev/null; then
            log_info "交易系统主程序启动成功 (PID: $TRADING_PID)"
            echo $TRADING_PID > .trading_pid
        else
            log_error "交易系统主程序启动失败"
            exit 1
        fi
    fi
}

# 启动Web监控界面
start_web_monitor() {
    log_header "启动Web监控界面..."
    
    # 在后台启动Web监控
    nohup python3 web_monitor.py > logs/web_monitor.log 2>&1 &
    WEB_PID=$!
    
    # 等待启动
    sleep 3
    
    # 检查进程是否启动成功
    if kill -0 $WEB_PID 2>/dev/null; then
        log_info "Web监控界面启动成功 (PID: $WEB_PID)"
        echo $WEB_PID > .web_pid
        log_info "Web监控地址: http://localhost:5008"
    else
        log_error "Web监控界面启动失败"
        # 如果Web启动失败，停止交易系统
        if [ -f ".trading_pid" ]; then
            kill $(cat .trading_pid) 2>/dev/null
            rm -f .trading_pid
        fi
        exit 1
    fi
}

# 显示系统状态
show_status() {
    log_header "系统状态信息"
    echo "=================================="
    
    # 检查交易系统状态
    if [ -f ".trading_pid" ] && kill -0 $(cat .trading_pid) 2>/dev/null; then
        echo "✅ 交易系统主程序: 运行中 (PID: $(cat .trading_pid))"
    elif [ -f ".trading_session" ] && screen -list | grep -q "$(cat .trading_session)"; then
        echo "✅ 交易系统主程序: 运行中 (Screen会话: $(cat .trading_session))"
    else
        echo "❌ 交易系统主程序: 未运行"
    fi
    
    if [ -f ".web_pid" ] && kill -0 $(cat .web_pid) 2>/dev/null; then
        echo "✅ Web监控界面: 运行中 (PID: $(cat .web_pid))"
        echo "🌐 监控地址: http://localhost:5008"
    else
        echo "❌ Web监控界面: 未运行"
    fi
    
    echo "=================================="
    echo "📁 日志文件:"
    echo "   - 交易系统: logs/trading_system.log"
    echo "   - Web监控: logs/web_monitor.log"
    echo "   - 系统日志: real_trading_system.log"
    echo "=================================="
    
    # 显示Screen会话管理命令
    if [ -f ".trading_session" ]; then
        echo "📺 Screen会话管理:"
        echo "   - 查看交易系统: screen -r $(cat .trading_session)"
        echo "   - 分离会话: Ctrl+A, D"
        echo "=================================="
    fi
}

# 停止系统
stop_system() {
    log_header "停止交易系统..."
    
    # 停止交易系统
    if [ -f ".trading_pid" ]; then
        TRADING_PID=$(cat .trading_pid)
        if kill -0 $TRADING_PID 2>/dev/null; then
            kill $TRADING_PID
            log_info "交易系统主程序已停止"
        fi
        rm -f .trading_pid
    fi
    
    # 停止Screen会话
    if [ -f ".trading_session" ]; then
        TRADING_SESSION=$(cat .trading_session)
        if screen -list | grep -q "$TRADING_SESSION"; then
            screen -S "$TRADING_SESSION" -X quit
            log_info "交易系统Screen会话已停止"
        fi
        rm -f .trading_session
    fi
    
    # 停止Web监控
    if [ -f ".web_pid" ]; then
        WEB_PID=$(cat .web_pid)
        if kill -0 $WEB_PID 2>/dev/null; then
            kill $WEB_PID
            log_info "Web监控界面已停止"
        fi
        rm -f .web_pid
    fi
}

# 主函数
main() {
    log_header "EMA/MA 交易系统启动脚本"
    log_header "=================================="
    
    # 创建日志目录
    mkdir -p logs
    
    # 处理命令行参数
    case "${1:-start}" in
        "start")
            check_python
            check_dependencies
            check_config
            start_trading_system
            start_web_monitor
            show_status
            
            log_header "系统启动完成！"
            log_info "使用 './run.sh stop' 停止系统"
            log_info "使用 './run.sh status' 查看状态"
            ;;
        "stop")
            stop_system
            log_info "系统已停止"
            ;;
        "restart")
            stop_system
            sleep 2
            $0 start
            ;;
        "status")
            show_status
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status}"
            echo "  start   - 启动交易系统和Web监控"
            echo "  stop    - 停止所有服务"
            echo "  restart - 重启系统"
            echo "  status  - 查看系统状态"
            exit 1
            ;;
    esac
}

# 信号处理
trap 'stop_system; exit 0' SIGINT SIGTERM

# 执行主函数
main "$@"