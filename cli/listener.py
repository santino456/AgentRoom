#!/usr/bin/env python3
"""
Agent Coop — 通用监听器 (Unified Listener)
支持多 Agent 通过 --agent 参数切换，自动读取 config/agents.yaml

用法:
    python cli/listener.py --agent Kimi-Agent --room 1
    python cli/listener.py --agent claude-agent --room 1 --timeout 3600
"""
import argparse
import asyncio
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config, get_agent_config, get_global_config


def try_acquire_lock(agent_name: str, room_id: int, ttl_seconds: int = 30) -> bool:
    """尝试获取文件锁，确保同一时刻只有一个监听器响应 @ 消息。
    使用 fcntl.flock (POSIX) 避免过期锁清理的竞态窗口。"""
    import fcntl

    lock_path = f"/tmp/agent-coop-lock-{agent_name}-{room_id}.json"
    now = time.time()
    my_pid = os.getpid()

    # 打开（或创建）锁文件，用 flock 保护所有操作
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    try:
        # 非阻塞获取排他锁；如果已被占用立即失败
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError):
        os.close(fd)
        return False

    try:
        # 持有 flock 后安全地读写锁文件内容
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            data_raw = os.read(fd, 1024).decode()
            if data_raw:
                data = json.loads(data_raw)
                lock_time = data.get("timestamp", 0)
                lock_pid = data.get("pid", 0)
                # 检查锁是否过期（且持有进程已不存在）
                if now - lock_time <= ttl_seconds:
                    # 锁未过期，归别人持有
                    return False
                # 锁已过期，继续执行（在 flock 保护下清理并重新写入）
        except Exception:
            pass  # 文件为空或损坏，视为可获取

        # 清空并写入自己的锁数据
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        lock_data = json.dumps({"timestamp": now, "pid": my_pid})
        os.write(fd, lock_data.encode())
        os.fsync(fd)
        return True
    finally:
        # 注意：不要在这里解锁（fcntl.flock(fd, fcntl.LOCK_UN)），
        # 因为进程退出时内核会自动释放 flock。
        # 保持 fd 打开直到进程退出，确保其他进程看到锁被占用。
        pass


def api_get(base_url: str, path: str):
    try:
        req = urllib.request.Request(f"{base_url}{path}", method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def count_running_listeners(base_url: str, room_id: int, agent_name: str) -> int:
    """统计当前运行中的监听器数量。"""
    try:
        data = api_get(base_url, f"/api/rooms/{room_id}/agent-status/listener-count?agent={agent_name}")
        if data:
            return data.get("listener_count", 0)
    except Exception:
        pass
    return 0


def fetch_messages(base_url: str, room_id: int, limit: int = 50):
    return api_get(base_url, f"/api/rooms/{room_id}/messages?limit={limit}") or []


def fetch_members(base_url: str, room_id: int):
    """获取房间成员列表，用于动态识别 @ 目标。"""
    return api_get(base_url, f"/api/rooms/{room_id}/members") or []


def build_aliases_from_members(members: list, agent_name: str) -> list[str]:
    """从成员列表构建触发关键词。每个监听器只响应 @自己 和 @all。"""
    # 只监听自己的名字和 @all，避免交叉触发其他 agent
    aliases = {agent_name.lower(), "all"}
    return list(aliases)


def is_mentioning(content: str, aliases: list[str]) -> bool:
    if not content:
        return False
    content_lower = content.lower()
    if "@all" in content_lower:
        return True
    for name in aliases:
        if f"@{name.lower()}" in content_lower:
            return True
    return False


async def listen_websocket(
    room_id: int,
    agent_name: str,
    fallback_aliases: list[str],
    base_http: str,
    base_ws: str,
    heartbeat_interval: int,
    max_reconnect_delay: int,
    timeout: int = None,
):
    init_msgs = fetch_messages(base_http, room_id)
    last_seen_id = max((m["id"] for m in init_msgs), default=0)

    # 动态获取成员列表构建 aliases
    members = fetch_members(base_http, room_id)
    aliases = build_aliases_from_members(members, agent_name)
    if not aliases or aliases == ["all"]:
        aliases = fallback_aliases
        print(f"[{agent_name}] Using fallback aliases: {aliases}", flush=True)
    else:
        print(f"[{agent_name}] Dynamic aliases from members: {aliases}", flush=True)

    print(f"[{agent_name}] Room {room_id} | Timeout {timeout}s", flush=True)
    print(f"[{agent_name}] Baseline ID: {last_seen_id}", flush=True)

    pending_messages = []
    ws_url = f"{base_ws}/ws/{room_id}"
    reconnect_delay = 1.0
    start_time = time.time()

    while True:
        if timeout and (time.time() - start_time) > timeout:
            print(f"\n[{agent_name}] Timeout ({timeout}s). No mentions.", flush=True)
            return pending_messages, "timeout"

        try:
            async with websockets.connect(
                ws_url, ping_interval=heartbeat_interval, ping_timeout=10
            ) as ws:
                reconnect_delay = 1.0
                print(f"[{agent_name}] WS connected", flush=True)

                await ws.send(json.dumps({"type": "heartbeat", "agent": agent_name}))

                async def heartbeat_loop():
                    while True:
                        await asyncio.sleep(60)
                        try:
                            await ws.send(json.dumps({"type": "heartbeat", "agent": agent_name}))
                        except Exception:
                            break
                heartbeat_task = asyncio.create_task(heartbeat_loop())

                try:
                    async for raw in ws:
                        if timeout and (time.time() - start_time) > timeout:
                            print(f"\n[{agent_name}] Timeout ({timeout}s). No mentions.", flush=True)
                            return pending_messages, "timeout"

                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        msg_id = msg.get("id")
                        if msg_id is None or msg_id <= last_seen_id:
                            continue

                        last_seen_id = msg_id
                        sender_name = msg.get("sender_name") or "unknown"
                        content = msg.get("content", "")
                        msg_type = msg.get("msg_type", "message")

                        if sender_name.lower() == agent_name.lower():
                            continue
                        if msg_type != "message":
                            continue

                        pending_messages.append(msg)

                        if is_mentioning(content, aliases):
                            # 文件锁协调
                            if not try_acquire_lock(agent_name, room_id):
                                print(f"[{agent_name}] Lock held by another listener, continuing...", flush=True)
                                continue

                            # 拉取上下文
                            recent = fetch_messages(base_http, room_id, limit=10)
                            context = [m for m in recent if m["id"] > last_seen_id - 20]
                            seen = set()
                            all_msgs = []
                            for m in context + pending_messages:
                                if m["id"] not in seen:
                                    seen.add(m["id"])
                                    all_msgs.append(m)
                            all_msgs.sort(key=lambda x: x["id"])

                            print(f"\n{'=' * 50}", flush=True)
                            print(f"ALERT: @{agent_name} mentioned!", flush=True)
                            print(f"{'=' * 50}", flush=True)
                            for m in all_msgs:
                                ts = m.get("created_at", "")[:19]
                                sender = m.get("sender_name", "unknown")
                                print(f"[{ts}] @{sender}: {m.get('content', '')}", flush=True)
                            print(f"\n{'=' * 50}", flush=True)
                            print("EXIT_WITH_MESSAGES", flush=True)

                            remaining = count_running_listeners(base_http, room_id, agent_name)
                            need = max(0, 4 - remaining)
                            print(f"\n[Listener Status] Running: {remaining} | Pool: 4 | Refill: {need}", flush=True)
                            print("  Note: Pool is a buffer, 2-3 is fine. Reply first, refill when convenient.", flush=True)
                            if need > 0:
                                print(f"  Command: .venv/bin/python cli/listener.py --agent {agent_name} --room {room_id}", flush=True)
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
            print(f"[{agent_name}] WS error: {e}, reconnect in {reconnect_delay}s...", flush=True)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

        except KeyboardInterrupt:
            print(f"\n[{agent_name}] Stopped")
            return pending_messages, "interrupt"


def main():
    parser = argparse.ArgumentParser(description="Agent Coop — Unified Listener")
    parser.add_argument("--agent", required=True, help="Agent name (e.g. claude-agent, Kimi-Agent)")
    parser.add_argument("--room", type=int, default=1, help="Room ID")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    parser.add_argument("--config", default="config/agents.yaml", help="Config file path")
    args = parser.parse_args()

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}", flush=True)
        sys.exit(1)

    try:
        agent_cfg = get_agent_config(config, args.agent)
    except ValueError as e:
        print(f"[ERROR] {e}", flush=True)
        sys.exit(1)

    if not agent_cfg.get("enabled", True):
        print(f"[ERROR] Agent '{args.agent}' is disabled.", flush=True)
        sys.exit(1)

    aliases = agent_cfg.get("aliases", [args.agent])
    rooms = agent_cfg.get("rooms", [])
    if not rooms:
        print(f"[ERROR] No rooms configured for '{args.agent}'", flush=True)
        sys.exit(1)

    room = rooms[0]
    room_id = args.room

    global_cfg = get_global_config(config)
    base_http = global_cfg.get("base_url", "http://127.0.0.1:8080")
    base_ws = global_cfg.get("ws_base", "ws://127.0.0.1:8080")
    heartbeat = global_cfg.get("heartbeat_interval", 20)
    max_reconnect = global_cfg.get("reconnect_max_delay", 30)

    try:
        asyncio.run(listen_websocket(
            room_id=room_id,
            agent_name=args.agent,
            fallback_aliases=aliases,
            base_http=base_http,
            base_ws=base_ws,
            heartbeat_interval=heartbeat,
            max_reconnect_delay=max_reconnect,
            timeout=args.timeout,
        ))
    except KeyboardInterrupt:
        print(f"\n[{args.agent}] Stopped")


if __name__ == "__main__":
    sys.exit(main())
