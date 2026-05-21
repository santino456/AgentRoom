#!/usr/bin/env python3
"""
Claude Mention Listener (WebSocket 事件驱动版)
- WS 长连接实时接收消息推送
- 检测 @claude-agent / @claude / @all
- 检测到时输出提醒并退出，产生系统通知唤醒 Claude
- 被唤醒后通过 API/CLI 自行拉取历史消息看上下文
"""
import asyncio
import json
import os
import sys
import time
import urllib.request

import websockets

BASE_HTTP = "http://127.0.0.1:8080"
BASE_WS = "ws://127.0.0.1:8080"
TARGETS = ["@claude-agent", "@claude", "@all"]
AGENT_NAME = "claude-agent"


def try_acquire_lock(room_id: int = 1, ttl_seconds: int = 30) -> bool:
    """尝试获取文件锁，确保同一时刻只有一个监听器响应 @ 消息。"""
    lock_path = f"/tmp/agent-coop-listener-lock-{AGENT_NAME}-{room_id}.json"
    now = time.time()
    my_pid = os.getpid()

    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        lock_data = json.dumps({"timestamp": now, "pid": my_pid})
        os.write(fd, lock_data.encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            with open(lock_path, "r") as f:
                data = json.load(f)
            lock_time = data.get("timestamp", 0)
            if now - lock_time > ttl_seconds:
                os.remove(lock_path)
                return try_acquire_lock(room_id, ttl_seconds)
        except Exception:
            pass
        return False
    except Exception:
        return False


def count_running_listeners(room_id: int = 1) -> int:
    """通过后端 API 统计当前运行中的监听器数量。"""
    try:
        req = urllib.request.Request(
            f"{BASE_HTTP}/api/rooms/{room_id}/agent-status/listener-count?agent={AGENT_NAME}",
            method="GET",
        )
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("listener_count", 0)
    except Exception:
        return 0


def fetch_messages(room_id: int, limit: int = 50):
    try:
        req = urllib.request.Request(
            f"{BASE_HTTP}/api/rooms/{room_id}/messages?limit={limit}",
            method="GET",
        )
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] API request failed: {e}", flush=True)
        return []


async def listen_websocket(room_id: int, timeout: int = None):
    init_msgs = fetch_messages(room_id)
    last_seen_id = max((m.get("id", 0) for m in init_msgs), default=0)

    print(f"[Claude Listener] Room {room_id} | Timeout {timeout}s", flush=True)
    print(f"[Claude Listener] Watching for: {', '.join(TARGETS)}", flush=True)
    print(f"[Claude Listener] Baseline ID: {last_seen_id} (ignoring older)", flush=True)

    ws_url = f"{BASE_WS}/ws/{room_id}"
    reconnect_delay = 1.0
    max_reconnect_delay = 30.0
    start_time = time.time()

    while True:
        if timeout and (time.time() - start_time) > timeout:
            print(f"\n[Claude Listener] Timeout ({timeout}s). No mentions.", flush=True)
            return [], "timeout"

        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
                reconnect_delay = 1.0
                print(f"[Claude Listener] WS connected {ws_url}", flush=True)

                await ws.send(json.dumps({"type": "heartbeat", "agent": "claude-agent"}))

                async def heartbeat_loop():
                    while True:
                        await asyncio.sleep(60)
                        try:
                            await ws.send(json.dumps({"type": "heartbeat", "agent": "claude-agent"}))
                        except Exception:
                            break
                heartbeat_task = asyncio.create_task(heartbeat_loop())

                try:
                    async for raw in ws:
                        if timeout and (time.time() - start_time) > timeout:
                            print(f"\n[Claude Listener] Timeout ({timeout}s). No mentions.", flush=True)
                            return [], "timeout"

                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        msg_id = msg.get("id")
                        if msg_id is None or msg_id <= last_seen_id:
                            continue

                        last_seen_id = msg_id
                        content = (msg.get("content") or "").lower()
                        sender = msg.get("sender_name", "")
                        msg_type = msg.get("msg_type", "message")

                        if sender == "claude-agent":
                            continue
                        if msg_type != "message":
                            continue

                        for target in TARGETS:
                            if target.lower() in content:
                                # 文件锁协调：确保只有一个监听器响应
                                if not try_acquire_lock(room_id):
                                    print(f"[Lock] 锁已被其他监听器获取，继续监听...", flush=True)
                                    continue

                                # 触发时实时拉取上下文
                                recent = fetch_messages(room_id, limit=10)
                                context = [m for m in recent if m["id"] > last_seen_id - 20]
                                seen = set()
                                all_msgs = []
                                for m in context:
                                    if m["id"] not in seen:
                                        seen.add(m["id"])
                                        all_msgs.append(m)
                                all_msgs.sort(key=lambda x: x["id"])

                                print(f"\n{'=' * 50}", flush=True)
                                print(f"ALERT: @claude-agent 被提及！", flush=True)
                                print(f"{'=' * 50}", flush=True)
                                for m in all_msgs:
                                    ts = m.get("created_at", "")[:19]
                                    sender = m.get("sender_name", "unknown")
                                    print(f"[{ts}] @{sender}: {m.get('content', '')}", flush=True)
                                print(f"\n{'=' * 50}", flush=True)
                                print("EXIT_WITH_MESSAGES", flush=True)

                                remaining = count_running_listeners(room_id)
                                need = max(0, 4 - remaining)
                                print(f"\n[Listener Status] 运行中: {remaining} | 目标: 4 | 建议续杯: {need}", flush=True)
                                if need > 0:
                                    print(f"  命令: .venv/bin/python adapters/claude_mention_listener.py 1 3600", flush=True)
                                return all_msgs, "mention"
                finally:
                    heartbeat_task.cancel()
                    try:
                        await heartbeat_task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            print(f"[Claude Listener] WS error: {e}, reconnect in {reconnect_delay}s...", flush=True)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)


def main():
    room_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else None
    try:
        asyncio.run(listen_websocket(room_id, timeout))
    except KeyboardInterrupt:
        print("\n[Claude Listener] Stopped")


if __name__ == "__main__":
    sys.exit(main())
