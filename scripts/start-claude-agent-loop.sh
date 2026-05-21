#!/bin/bash
# ============================================================
# Claude-Agent 循环监听器 (WebSocket 版)
# 监听器退出后自动重启，实现持续监听
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROOM_ID="${1:-1}"
TIMEOUT="${2:-3600}"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LISTENER="$PROJECT_DIR/adapters/claude_mention_listener.py"
PID_FILE="/tmp/claude-agent-${ROOM_ID}.pid"

echo "🔄 Claude-Agent WebSocket 循环监听器启动"
echo "   房间: $ROOM_ID, 超时: ${TIMEOUT}s"
echo "   按 Ctrl+C 停止"
echo ""

# 写入 PID 文件
echo $$ > "$PID_FILE"

while true; do
    echo "[$(date '+%H:%M:%S')] 启动监听器..."

    if "$PYTHON" "$LISTENER" "$ROOM_ID" "$TIMEOUT"; then
        echo "[$(date '+%H:%M:%S')] 监听器正常退出（可能被@提及唤醒）"
        echo "   Claude 正在处理消息，3秒后重启监听器..."
    else
        echo "[$(date '+%H:%M:%S')] 监听器异常退出，3秒后重启..."
    fi

    sleep 3
done
