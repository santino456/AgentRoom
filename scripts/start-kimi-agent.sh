#!/bin/bash
# ============================================================
# Kimi-Agent 事件驱动监听器启动脚本 (WebSocket 版)
#
# 用法:
#   ./scripts/start-kimi-agent.sh [room_id] [timeout_sec]
#
# 示例:
#   ./scripts/start-kimi-agent.sh              # 默认: 房间1, 无超时
#   ./scripts/start-kimi-agent.sh 1 300        # 房间1, 300秒超时
#
# 机制:
#   1. WebSocket 长连接实时接收消息推送
#   2. 检测 @提及 → 输出消息 → 退出
#   3. 退出产生系统通知 → 唤醒 Kimi → Kimi 回复 → 重启脚本
#   4. 支持断线重连 + 心跳保活
# ============================================================

set -e

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LISTENER_SCRIPT="$PROJECT_DIR/cli/kimi_agent_listener.py"
PYTHON="$PROJECT_DIR/.venv/bin/python"

# 参数
ROOM_ID="${1:-1}"
TIMEOUT="${2:-}"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}  🤖 Kimi-Agent WebSocket 事件驱动监听器${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "  房间 ID:     ${YELLOW}$ROOM_ID${NC}"
echo -e "  超时:        ${YELLOW}${TIMEOUT:-无}${NC}"
echo -e "  Python:      ${YELLOW}$PYTHON${NC}"
echo -e "${BLUE}------------------------------------------------------------${NC}"
echo -e "  机制: WS 长连接 → 实时推送 → 检测@提及 → 退出 → 通知唤醒"
echo -e "  按 Ctrl+C 停止"
echo -e "${BLUE}============================================================${NC}"

# 检查 Python
if [ ! -x "$PYTHON" ]; then
    echo -e "${YELLOW}错误: 虚拟环境 Python 不存在: $PYTHON${NC}"
    echo -e "${YELLOW}请先运行: make install${NC}"
    exit 1
fi

# 检查监听脚本
if [ ! -f "$LISTENER_SCRIPT" ]; then
    echo -e "${YELLOW}错误: 监听脚本不存在: $LISTENER_SCRIPT${NC}"
    exit 1
fi

# 启动监听器
cd "$PROJECT_DIR"
if [ -n "$TIMEOUT" ]; then
    "$PYTHON" "$LISTENER_SCRIPT" "$ROOM_ID" "$TIMEOUT"
else
    "$PYTHON" "$LISTENER_SCRIPT" "$ROOM_ID"
fi
