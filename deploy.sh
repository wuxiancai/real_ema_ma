#!/bin/bash

# 真实交易系统一键部署脚本
# 支持 macOS、Linux 和 Ubuntu Server systemd 自动启动

set -e  # 遇到错误立即退出

echo "=========================================="
echo "真实交易系统 - EMA/MA交叉策略"
echo "一键部署脚本"
echo "=========================================="

# 全局变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="real-ema-ma"
SERVICE_USER="${USER}"
VENV_NAME="venv"
PYTHON_EXEC=""
PROJECT_DIR="${SCRIPT_DIR}"

# 日志函数
log_info() {
    echo "[INFO] $1"
}

log_warn() {
    echo "[WARN] $1"
}

log_error() {
    echo "[ERROR] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

# 检测操作系统
detect_os() {
    echo "检测操作系统..."
    OS_TYPE=""
    DISTRO=""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        log_info "检测到操作系统: macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS_TYPE="linux"
        
        # 检测Linux发行版
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO="$ID"
            log_info "检测到操作系统: Linux ($NAME)"
            
            if [[ "$DISTRO" == "ubuntu" ]]; then
                log_info "检测到Ubuntu系统，将配置systemd服务"
            fi
        else
            log_warn "无法检测Linux发行版，使用通用配置"
        fi
    else
        log_warn "未识别的操作系统类型: $OSTYPE"
        log_warn "将使用默认配置继续运行..."
        OS_TYPE="unknown"
    fi
}

# 检查系统权限
check_permissions() {
    if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
        log_info "检查系统权限..."
        if [[ $EUID -eq 0 ]]; then
            log_warn "检测到以root用户运行"
            log_warn "建议使用普通用户运行，systemd服务将以当前用户身份运行"
        fi
        
        # 检查sudo权限（用于systemd服务安装）
        if ! sudo -n true 2>/dev/null; then
            log_warn "需要sudo权限来安装systemd服务"
            log_warn "请确保当前用户有sudo权限"
        fi
    fi
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    # 检查Python3
    if command -v python3 &> /dev/null; then
        PYTHON_EXEC="python3"
        log_info "找到Python3: $(python3 --version)"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1)
        if [[ "$PYTHON_VERSION" == *"Python 3"* ]]; then
            PYTHON_EXEC="python"
            log_info "找到Python: $PYTHON_VERSION"
        else
            log_error "需要Python 3.x版本"
            exit 1
        fi
    else
        log_error "未找到Python3"
        log_error "请先安装Python 3.x"
        exit 1
    fi
}

# 设置虚拟环境
setup_venv() {
    log_info "设置Python虚拟环境..."
    
    cd "$PROJECT_DIR"
    
    # 检查虚拟环境是否存在
    if [ ! -d "$VENV_NAME" ]; then
        log_info "创建虚拟环境: $VENV_NAME"
        $PYTHON_EXEC -m venv $VENV_NAME
        log_success "虚拟环境创建成功"
    else
        log_info "虚拟环境已存在: $VENV_NAME"
    fi
    
    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source $VENV_NAME/bin/activate
    
    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip
    
    # 安装依赖
    log_info "安装Python依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "依赖包安装完成"
    else
        log_error "未找到requirements.txt文件"
        exit 1
    fi
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f "$PROJECT_DIR/config.py" ]; then
        log_error "未找到配置文件 config.py"
        exit 1
    fi
    
    # 检查配置文件中的关键配置
    if grep -q "TEST_MODE = True" "$PROJECT_DIR/config.py"; then
        log_info "配置为测试模式"
    else
        log_warn "配置为真实交易模式"
    fi
    
    log_success "配置文件检查通过"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/logs/json_snapshots"
    
    log_success "目录创建完成"
}

# 创建启动脚本
create_startup_script() {
    log_info "创建启动脚本..."
    
    local startup_script="${PROJECT_DIR}/start_services.sh"
    
    cat > "$startup_script" << 'EOF'
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
EOF

    log_success "启动脚本创建完成"
}

# 设置启动脚本权限
setup_startup_script() {
    log_info "设置启动脚本权限..."
    
    local startup_script="${PROJECT_DIR}/start_services.sh"
    
    if [ -f "$startup_script" ]; then
        chmod +x "$startup_script"
        log_success "启动脚本权限设置完成"
    else
        log_error "未找到启动脚本: $startup_script"
        exit 1
    fi
}

# 创建systemd服务文件
create_systemd_service() {
    if [[ "$OS_TYPE" != "linux" ]] || [[ "$DISTRO" != "ubuntu" ]]; then
        log_info "非Ubuntu系统，跳过systemd服务创建"
        return 0
    fi
    
    log_info "创建systemd服务文件..."
    
    local service_file="/etc/systemd/system/${SERVICE_NAME}.service"
    local venv_python="${PROJECT_DIR}/${VENV_NAME}/bin/python"
    local main_script="${PROJECT_DIR}/main.py"
    
    # 创建服务文件内容
    cat << EOF | sudo tee "$service_file" > /dev/null
[Unit]
Description=Real Trading System - EMA/MA Cross Strategy with Web Monitor
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
Environment=PATH=${PROJECT_DIR}/${VENV_NAME}/bin
ExecStart=${PROJECT_DIR}/start_services.sh
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=${PROJECT_DIR}
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF

    log_success "systemd服务文件已创建: $service_file"
}

# 管理systemd服务
manage_systemd_service() {
    if [[ "$OS_TYPE" != "linux" ]] || [[ "$DISTRO" != "ubuntu" ]]; then
        log_info "非Ubuntu系统，跳过systemd服务管理"
        return 0
    fi
    
    log_info "配置systemd服务..."
    
    # 重新加载systemd配置
    sudo systemctl daemon-reload
    
    # 启用服务（开机自启）
    sudo systemctl enable "${SERVICE_NAME}.service"
    log_success "服务已设置为开机自启"
    
    # 检查服务状态
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_info "服务正在运行，重启服务..."
        sudo systemctl restart "${SERVICE_NAME}.service"
    else
        log_info "启动服务..."
        sudo systemctl start "${SERVICE_NAME}.service"
    fi
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_success "服务启动成功"
        log_info "服务状态:"
        sudo systemctl status "${SERVICE_NAME}.service" --no-pager -l
    else
        log_error "服务启动失败"
        log_error "查看服务日志:"
        sudo journalctl -u "${SERVICE_NAME}.service" --no-pager -l
        exit 1
    fi
}

# 显示服务管理命令
show_service_commands() {
    if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
        echo ""
        echo "=========================================="
        echo "systemd 服务管理命令:"
        echo "=========================================="
        echo "查看服务状态:   sudo systemctl status ${SERVICE_NAME}"
        echo "启动服务:       sudo systemctl start ${SERVICE_NAME}"
        echo "停止服务:       sudo systemctl stop ${SERVICE_NAME}"
        echo "重启服务:       sudo systemctl restart ${SERVICE_NAME}"
        echo "查看日志:       sudo journalctl -u ${SERVICE_NAME} -f"
        echo "禁用开机自启:   sudo systemctl disable ${SERVICE_NAME}"
        echo "启用开机自启:   sudo systemctl enable ${SERVICE_NAME}"
        echo "=========================================="
    fi
}

# 显示部署结果
show_deployment_result() {
    echo ""
    echo "=========================================="
    echo "部署完成!"
    echo "=========================================="
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $PROJECT_DIR/$VENV_NAME"
    echo "日志目录: $PROJECT_DIR/logs"
    
    if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
        echo "systemd服务: ${SERVICE_NAME}.service"
        echo "服务用户: ${SERVICE_USER}"
    fi
    
    echo ""
    echo "手动启动命令:"
    echo "cd $PROJECT_DIR"
    echo "source $VENV_NAME/bin/activate"
    echo "python main.py &"
    echo "python web_monitor.py &"
    echo ""
    echo "或使用启动脚本:"
    echo "./start_services.sh"
    echo ""
    
    show_service_commands
}

# 清理函数
cleanup() {
    if [ $? -ne 0 ]; then
        log_error "部署过程中发生错误"
        exit 1
    fi
}

# 主函数
main() {
    # 设置错误处理
    trap cleanup EXIT
    
    # 执行部署步骤
    detect_os
    check_permissions
    check_python
    setup_venv
    check_config
    create_directories
    create_startup_script
    setup_startup_script
    
    # Ubuntu系统特定配置
    if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
        create_systemd_service
        manage_systemd_service
    fi
    
    # 显示部署结果
    show_deployment_result
    
    log_success "真实交易系统部署完成!"
}

# 检查命令行参数
case "${1:-deploy}" in
    "deploy"|"")
        main
        ;;
    "service-start")
        if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
            sudo systemctl start "${SERVICE_NAME}.service"
            log_success "服务已启动"
        else
            log_error "systemd服务仅在Ubuntu系统上可用"
        fi
        ;;
    "service-stop")
        if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
            sudo systemctl stop "${SERVICE_NAME}.service"
            log_success "服务已停止"
        else
            log_error "systemd服务仅在Ubuntu系统上可用"
        fi
        ;;
    "service-status")
        if [[ "$OS_TYPE" == "linux" ]] && [[ "$DISTRO" == "ubuntu" ]]; then
            sudo systemctl status "${SERVICE_NAME}.service"
        else
            log_error "systemd服务仅在Ubuntu系统上可用"
        fi
        ;;
    "help")
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  deploy          执行完整部署 (默认)"
        echo "  service-start   启动systemd服务 (仅Ubuntu)"
        echo "  service-stop    停止systemd服务 (仅Ubuntu)"
        echo "  service-status  查看服务状态 (仅Ubuntu)"
        echo "  help            显示此帮助信息"
        ;;
    *)
        log_error "未知选项: $1"
        echo "使用 '$0 help' 查看可用选项"
        exit 1
        ;;
esac
