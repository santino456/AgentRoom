#!/bin/bash
# Kimi-Agent 监听器池守护脚本
# 保持 4 个监听器始终在线，每 30 秒检查一次

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$PROJECT_DIR/.venv/bin/python"
LISTENER="$PROJECT_DIR/cli/listener.py"
AGENT="Kimi-Agent"
ROOM_ID="${1:-1}"
TARGET="${2:-4}"
INTERVAL="${3:-30}"

cd "$PROJECT_DIR"

# 获取当前监听器数量
get_count() {
  curl -s "http://127.0.0.1:8080/api/rooms/$ROOM_ID/agent-status/listener-count?agent=$AGENT" 2>/dev/null | \
    "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('listener_count',0))" 2>/dev/null || echo 0
}

echo "[$AGENT] Listener pool daemon started | Room $ROOM_ID | Target $TARGET | Check interval ${INTERVAL}s"

while true; do
  count=$(get_count)
  need=$((TARGET - count))

  if [ "$need" -gt 0 ]; then
    echo "[$AGENT] Running: $count / Target: $TARGET | Starting $need listener(s)..."
    for i in $(seq 1 $need); do
      "$PYTHON" "$LISTENER" --agent "$AGENT" --room "$ROOM_ID" &
    done
  fi

  sleep "$INTERVAL"
done
