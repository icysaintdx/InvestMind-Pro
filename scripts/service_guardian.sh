#!/bin/bash
# EMA交易监控守护脚本 - 确保服务稳定运行
#  Created: 2026-02-28

PROJECT_DIR="/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro"
LOG_FILE="/tmp/investmind_guardian.log"
PID_FILE="/tmp/investmind_server.pid"
HEALTH_URL="http://localhost:8000/api/health"
MAX_RETRIES=3
RETRY_INTERVAL=10

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

check_health() {
    curl -s $HEALTH_URL > /dev/null 2>&1
    return $?
}

start_server() {
    log "🚀 启动后端服务..."
    cd $PROJECT_DIR
    source venv_linux/bin/activate
    
    # 使用nohup启动，并重定向日志
    nohup python3 backend/server.py >> /tmp/investmind_server.log 2>&1 &
    echo $! > $PID_FILE
    
    log "✅ 服务已启动，PID: $!"
    
    # 等待服务就绪
    sleep 5
    
    if check_health; then
        log "✅ 健康检查通过"
        return 0
    else
        log "❌ 健康检查失败"
        return 1
    fi
}

stop_server() {
    if [ -f $PID_FILE ]; then
        PID=$(cat $PID_FILE)
        if kill -0 $PID 2>/dev/null; then
            log "🛑 停止现有服务 (PID: $PID)..."
            kill $PID
            sleep 2
        fi
        rm -f $PID_FILE
    fi
    
    # 清理残留进程
    pkill -f "backend/server.py" 2>/dev/null
}

restart_server() {
    log "🔄 重启服务..."
    stop_server
    sleep 2
    start_server
}

# 主循环
case "$1" in
    start)
        if check_health; then
            log "✅ 服务已在运行"
            exit 0
        fi
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    check)
        if check_health; then
            log "✅ 服务运行正常"
            exit 0
        else
            log "❌ 服务未运行，尝试重启..."
            restart_server
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|check}"
        exit 1
        ;;
esac
