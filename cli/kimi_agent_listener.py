#!/usr/bin/env python3
"""
Kimi-Agent @触发监听器 (WebSocket 事件驱动版)
- WebSocket 长连接，实时接收消息推送
- 收到消息时检测 @Kimi-Agent / @kimi / @Kimi
- 检测到时输出累积消息并退出，产生系统通知唤醒 Kimi
- 支持断线重连 + 心跳
"""
import sys
import time
import json
import asyncio
import urllib.request

import websockets

BASE_HTTP = "http://127.0.0.1:8080"
BASE_WS = "ws://127.0.0.1:8080"
KIMI_NAMES = {"Kimi-Agent", "kimi", "Kimi"}


def api_get(path):
    try:
        req = urllib.request.Request(f"{BASE_HTTP}{path}", method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def is_mentioning_kimi(content):
    if not content:
        return False
    content_lower = content.lower()
    if "@all" in content_lower:
        return True
    for name in KIMI_NAMES:
        if f"@{name.lower()}" in content_lower:
            return True
    return False


def fetch_messages(room_id, limit=50):
    return api_get(f"/api/rooms/{room_id}/messages?limit={limit}") or []


async def listen_websocket(room_id, timeout=None):
    """
    WebSocket 长连接监听。
    返回 (pending_messages, exit_reason)
    """
    # 先拉取历史消息作为基准线
    init_msgs = fetch_messages(room_id)
    last_seen_id = max((m["id"] for m in init_msgs), default=0)

    print(f"🤖 Kimi-Agent WS 监听器启动 | 房间: {room_id}")
    print("=" * 50, flush=True)
    print(f"📌 已同步 {len(init_msgs)} 条消息，从 ID={last_seen_id} 开始监听...")
    print("⏳ 等待 @Kimi-Agent 提及... (Ctrl+C 停止)", flush=True)
    print("-" * 50, flush=True)

    pending_messages = []
    ws_url = f"{BASE_WS}/ws/{room_id}"
    reconnect_delay = 1.0
    max_reconnect_delay = 30.0
    start_time = time.time()

    while True:
        if timeout and (time.time() - start_time) > timeout:
            print(f"\n[Listener] 超时 ({timeout}s)，无提及。")
            return pending_messages, "timeout"

        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                reconnect_delay = 1.0  # 重连成功后重置退避
                print(f"🔗 WS 已连接 {ws_url}", flush=True)

                # 发送初始心跳
                await ws.send(json.dumps({"type": "heartbeat", "agent": "Kimi-Agent"}))

                # 启动后台心跳任务
                async def heartbeat_loop():
                    while True:
                        await asyncio.sleep(60)
                        try:
                            await ws.send(json.dumps({"type": "heartbeat", "agent": "Kimi-Agent"}))
                        except Exception:
                            break
                heartbeat_task = asyncio.create_task(heartbeat_loop())

                try:
                    async for raw in ws:
                        if timeout and (time.time() - start_time) > timeout:
                            print(f"\n[Listener] 超时 ({timeout}s)，无提及。")
                            return pending_messages, "timeout"

                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        # 只处理新消息（忽略历史/心跳）
                        msg_id = msg.get("id")
                        if msg_id is None or msg_id <= last_seen_id:
                            continue

                        last_seen_id = msg_id
                        sender_name = msg.get("sender_name") or "unknown"
                        content = msg.get("content", "")
                        msg_type = msg.get("msg_type", "message")

                        # 忽略自己和系统消息
                        if sender_name.lower() in {n.lower() for n in KIMI_NAMES}:
                            continue
                        if msg_type != "message":
                            continue

                        pending_messages.append({
                            "id": msg_id,
                            "sender": sender_name,
                            "content": content,
                            "time": msg.get("created_at", "")
                        })

                        if is_mentioning_kimi(content):
                            # 拉取最近消息作为上下文，避免遗漏
                            recent = fetch_messages(room_id, limit=10)
                            context = [m for m in recent if m["id"] > last_seen_id - 20]
                            all_msgs = context + pending_messages
                            # 去重并按 ID 排序
                            seen = set()
                            all_msgs = [m for m in all_msgs if not (m["id"] in seen or seen.add(m["id"]))]
                            all_msgs.sort(key=lambda x: x["id"])
                            
                            print(f"\n🚨 ALERT: @Kimi-Agent 被提及！输出 {len(all_msgs)} 条消息（含上下文）：", flush=True)
                            print("=" * 50, flush=True)
                            for m in all_msgs:
                                ts = m.get("created_at", "").split("T")[1][:8] if "T" in m.get("created_at", "") else ""
                                sender = m.get("sender_name") or m.get("sender", "unknown")
                                print(f"[{ts}] {sender}: {m.get('content', '')}", flush=True)
                            print("=" * 50, flush=True)
                            print("EXIT_WITH_MESSAGES", flush=True)
                            print("\n⚠️ 【续杯提醒】监听器已退出，请马上调用 Shell 工具续杯！", flush=True)
                            print("   命令: .venv/bin/python cli/kimi_agent_listener.py 1", flush=True)
                            return all_msgs, "mention"
                finally:
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass

        except (websockets.exceptions.ConnectionClosed,
                websockets.exceptions.InvalidStatusCode,
                OSError) as e:
            print(f"⚠️ WS 断开: {e}，{reconnect_delay}s 后重连...", flush=True)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

        except asyncio.CancelledError:
            raise

        except KeyboardInterrupt:
            print("\n👋 监听器已停止")
            return pending_messages, "interrupt"


def main():
    room_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        asyncio.run(listen_websocket(room_id, timeout))
    except KeyboardInterrupt:
        print("\n👋 监听器已停止")
    return 0


if __name__ == "__main__":
    sys.exit(main())
