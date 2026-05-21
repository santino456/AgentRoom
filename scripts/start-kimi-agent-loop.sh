#!/bin/bash
# ============================================================
# Kimi-Agent 循环监听器 (WebSocket 版)
# 监听器退出后自动重启，实现持续监听
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOM_ID="${1:-1}"
TIMEOUT="${2:-}"
PID_FILE="/tmp/kimi-agent-${ROOM_ID}.pid"

echo "🔄 Kimi-Agent WebSocket 循环监听器启动"
echo "   房间: $ROOM_ID, 超时: ${TIMEOUT:-无}"
echo "   PID 文件: $PID_FILE"
echo "   按 Ctrl+C 停止"
echo ""

# 写入 PID 文件
echo $$ > "$PID_FILE"

# 清理函数
cleanup() {
    rm -f "$PID_FILE"
    echo ""
    echo "🛑 循环监听器已停止"
    exit 0
}
trap cleanup EXIT INT TERM

while true; do
    echo "[$(date '+%H:%M:%S')] 启动监听器..."
    
    # 运行监听器，捕获退出码
    if bash "$SCRIPT_DIR/start-kimi-agent.sh" "$ROOM_ID" "$TIMEOUT"; then
        echo "[$(date '+%H:%M:%S')] 监听器正常退出（可能被@提及唤醒）"
        echo "   Kimi 正在处理消息，3秒后重启监听器..."
    else
        echo "[$(date '+%H:%M:%S')] 监听器异常退出，3秒后重启..."
    fi
    
    sleep 3
done
