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
import random
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import websockets

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import load_config, get_agent_config, get_global_config


def _is_process_alive(pid: int) -> bool:
    """检查指定 PID 的进程是否仍在运行。"""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def try_acquire_lock(agent_name: str, room_id: int, ttl_seconds: int = 30) -> bool:
    """尝试获取文件锁，确保同一时刻只有一个监听器响应 @ 消息。
    使用 fcntl.flock (POSIX) 避免过期锁清理的竞态窗口。"""
    import fcntl

    lock_path = os.path.join(tempfile.gettempdir(), f"agentroom-lock-{agent_name}-{room_id}.json")
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
                # 锁在 TTL 内且持有进程还活着 → 归别人持有
                if now - lock_time <= ttl_seconds and _is_process_alive(lock_pid):
                    # 释放 flock 并关闭 fd，让其他进程有机会竞争
                    fcntl.flock(fd, fcntl.LOCK_UN)
                    os.close(fd)
                    return False
                # 否则视为过期/孤儿锁，继续执行并覆盖
        except Exception:
            pass  # 文件为空或损坏，视为可获取

        # 清空并写入自己的锁数据
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        lock_data = json.dumps({"timestamp": now, "pid": my_pid})
        os.write(fd, lock_data.encode())
        os.fsync(fd)
        return True
    except Exception:
        # 异常时释放锁并关闭 fd
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        raise


def api_get(base_url: str, path: str, headers: dict = None):
    try:
        req = urllib.request.Request(f"{base_url}{path}", method="GET")
        req.add_header("Accept", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
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


def fetch_messages(base_url: str, room_id: int, token: str = "", limit: int = 50):
    headers = {"X-Member-Token": token} if token else None
    return api_get(base_url, f"/api/rooms/{room_id}/messages?limit={limit}", headers) or []


def fetch_members(base_url: str, room_id: int, token: str = ""):
    """获取房间成员列表，用于动态识别 @ 目标。"""
    headers = {"X-Member-Token": token} if token else None
    return api_get(base_url, f"/api/rooms/{room_id}/members", headers) or []


def build_aliases_from_members(members: list, agent_name: str) -> list[str]:
    """从成员列表构建触发关键词。每个监听器只响应 @自己 和 @all。"""
    # 监听自己的 name 和 display_name，以及 @all
    aliases = {agent_name.lower(), "all"}
    for m in members:
        if m.get("name", "").lower() == agent_name.lower():
            dn = (m.get("display_name") or "").strip()
            if dn:
                aliases.add(dn.lower())
            break
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


def _check_missed_mentions(
    base_http: str,
    room_id: int,
    agent_name: str,
    aliases: list[str],
    last_seen_id: int,
    start_time: float,
    token: str = "",
):
    """启动时兜底：检查最近 2 分钟是否有 @ 自己的消息被漏掉。"""
    cutoff = start_time - 120  # 2 分钟前
    recent = fetch_messages(base_http, room_id, token, limit=20)
    missed = []
    for m in recent:
        if m["id"] > last_seen_id:
            continue
        sender = m.get("sender_name") or ""
        if sender.lower() == agent_name.lower():
            continue
        if m.get("msg_type") != "message":
            continue
        created = m.get("created_at", "")
        try:
            # 解析 ISO 时间
            if created.endswith("Z"):
                created = created[:-1] + "+00:00"
            msg_ts = datetime.fromisoformat(created).timestamp()
        except Exception:
            continue
        if msg_ts < cutoff:
            continue
        to_name = (m.get("to_name") or "").lower()
        is_mentioned = (
            to_name in (a.lower() for a in aliases if a != "all")
            or to_name == "all"
            or is_mentioning(m.get("content", ""), aliases)
        )
        if is_mentioned:
            missed.append(m)

    if missed:
        print(f"[{agent_name}] WARNING: {len(missed)} missed @ mention(s) detected!", flush=True)
        # 尝试获取锁并立即输出
        if try_acquire_lock(agent_name, room_id):
            print(f"\n{'=' * 50}", flush=True)
            print(f"ALERT: @{agent_name} mentioned! (missed during dead window)", flush=True)
            print(f"{'=' * 50}", flush=True)
            for m in missed:
                ts = m.get("created_at", "")[:19]
                sender = m.get("sender_name", "unknown")
                print(f"[{ts}] @{sender}: {m.get('content', '')}", flush=True)
            print(f"\n{'=' * 50}", flush=True)
            print("EXIT_WITH_MESSAGES", flush=True)
            sys.exit(0)


def _get_member_token(room_id: int, agent_name: str) -> str:
    import json
    from pathlib import Path
    config_path = Path.home() / ".agentroom" / f"cli-config-{agent_name}.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            cfg = json.load(f)
        return cfg.get("tokens", {}).get(str(room_id), "")
    return ""


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
    token = _get_member_token(room_id, agent_name)
    init_msgs = fetch_messages(base_http, room_id, token)
    last_seen_id = max((m["id"] for m in init_msgs), default=0)

    # 动态获取成员列表构建 aliases
    members = fetch_members(base_http, room_id, token)
    aliases = build_aliases_from_members(members, agent_name)
    if not aliases or aliases == ["all"]:
        aliases = fallback_aliases
        print(f"[{agent_name}] Using fallback aliases: {aliases}", flush=True)
    else:
        print(f"[{agent_name}] Dynamic aliases from members: {aliases}", flush=True)

    print(f"[{agent_name}] Room {room_id} | Timeout {timeout}s", flush=True)
    print(f"[{agent_name}] Baseline ID: {last_seen_id}", flush=True)

    start_time = time.time()

    # 兜底：启动时扫描最近 2 分钟的消息，防止「全死窗口」漏掉 @
    try:
        _check_missed_mentions(
            base_http, room_id, agent_name, aliases,
            last_seen_id, start_time, token
        )
    except Exception as e:
        print(f"[{agent_name}] _check_missed_mentions skipped: {e}", flush=True)

    pending_messages = []
    ws_url = f"{base_ws}/ws/{room_id}"
    reconnect_delay = 1.0

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
                        await asyncio.sleep(25)
                        try:
                            await ws.send(json.dumps({"type": "heartbeat", "agent": agent_name}))
                        except Exception:
                            break
                heartbeat_task = asyncio.create_task(heartbeat_loop())

                try:
                    while True:
                        # 超时检查：在等待消息之前也要检查
                        elapsed = time.time() - start_time
                        if timeout and elapsed > timeout:
                            print(f"\n[{agent_name}] Timeout ({timeout}s). No mentions.", flush=True)
                            return pending_messages, "timeout"

                        remaining = None
                        if timeout:
                            remaining = max(0.1, timeout - elapsed)

                        try:
                            raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        except asyncio.TimeoutError:
                            print(f"\n[{agent_name}] Timeout ({timeout}s). No mentions.", flush=True)
                            return pending_messages, "timeout"

                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        if msg.get("type") == "ping":
                            await ws.send("pong")
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

                        # 触发规则：
                        # 1. to_name 定向匹配（精确匹配 name 或 display_name）
                        # 2. to_name == "all" 或内容含 @all（广播）
                        # 3. 消息内容中的普通 @mention 不再触发（避免误触发）
                        to_name = (msg.get("to_name") or "").lower()
                        is_mentioned = (
                            to_name in (a.lower() for a in aliases if a != "all")
                            or to_name == "all"
                            or (not to_name and "@all" in content.lower())
                        )
                        if is_mentioned:
                            # 文件锁协调：短暂重试，避免因 WS 断线导致两个监听器都漏消息
                            lock_acquired = False
                            for _retry in range(3):
                                if try_acquire_lock(agent_name, room_id):
                                    lock_acquired = True
                                    break
                                print(f"[{agent_name}] Lock held, retry {_retry+1}/3...", flush=True)
                                time.sleep(0.5)
                            if not lock_acquired:
                                print(f"[{agent_name}] Lock still held after retries, skipping (other listener should process)", flush=True)
                                continue

                            # 拉取上下文
                            recent = fetch_messages(base_http, room_id, token, limit=5)
                            context = [m for m in recent if m["id"] > last_seen_id - 10]
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

                            print(f"\n{'=' * 50}", flush=True)
                            print("ACTION ORDER:", flush=True)
                            print("  1. 先立刻去平台回复 @ 消息", flush=True)
                            print("  2. 顺手补监听器（如果需要）", flush=True)
                            print("  3. 再去做该做的事", flush=True)
                            print(f"{'=' * 50}", flush=True)

                            remaining = count_running_listeners(base_http, room_id, agent_name)
                            need = max(0, 2 - remaining)
                            print(f"\n[Listener Status] Running: {remaining} | Pool: 2 | Refill: {need}", flush=True)
                            print("  Note: Pool is a buffer, 2 is fine. Reply first, refill when convenient.", flush=True)
                            if need > 0:
                                print(f"  Command: .venv/bin/python cli/listener.py --agent {agent_name} --room {room_id}", flush=True)
                            return all_msgs, "mention"

                except websockets.exceptions.ConnectionClosed:
                    raise
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

    room_id = args.room

    global_cfg = get_global_config(config)
    base_http = global_cfg.get("base_url", "http://127.0.0.1:8080")
    base_ws = global_cfg.get("ws_base", "ws://127.0.0.1:8080")
    heartbeat = global_cfg.get("heartbeat_interval", 20)
    max_reconnect = global_cfg.get("reconnect_max_delay", 30)

    # 加随机 jitter，避免多个监听器同时 timeout
    timeout = args.timeout
    if timeout:
        timeout = int(timeout * (0.8 + random.random() * 0.4))  # 80%~120% 浮动
        print(f"[{args.agent}] Timeout jittered: {timeout}s", flush=True)

    try:
        asyncio.run(listen_websocket(
            room_id=room_id,
            agent_name=args.agent,
            fallback_aliases=aliases,
            base_http=base_http,
            base_ws=base_ws,
            heartbeat_interval=heartbeat,
            max_reconnect_delay=max_reconnect,
            timeout=timeout,
        ))
    except KeyboardInterrupt:
        print(f"\n[{args.agent}] Stopped")


if __name__ == "__main__":
    sys.exit(main())
