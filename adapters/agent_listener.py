#!/usr/bin/env python3
"""
Agent Coop — 统一监听器入口

读取 config/agents.yaml，为每个启用的 Agent 启动对应监听器。
支持 adapter 类型：cli / mcp / webhook

用法:
    python adapters/agent_listener.py [agent_name]

示例:
    python adapters/agent_listener.py              # 启动所有启用的 Agent
    python adapters/agent_listener.py claude-agent # 只启动 claude-agent
"""
import asyncio
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import websockets

# 加载配置
sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))
from config_loader import load_config, get_agent_config, list_agents

BASE_HTTP = "http://127.0.0.1:8080"
BASE_WS = "ws://127.0.0.1:8080"

# 持久化日志，避免后台任务输出被清理
LOG_FILE = Path("/tmp/agent-listener.log")


def log(msg: str):
    """同时输出到 stdout 和持久化日志文件"""
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()


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
        log(f"[ERROR] API request failed: {e}")
        return []


async def listen_agent(agent: dict, global_cfg: dict):
    """
    为单个 Agent 启动 WebSocket 监听器。
    累积所有新消息，检测到 @aliases 时输出并退出。
    """
    name = agent["name"]
    aliases = [f"@{a.lower()}" for a in agent.get("aliases", [])]
    if not aliases:
        aliases = [f"@{name.lower()}"]

    rooms = agent.get("rooms", [])
    if not rooms:
        log(f"[{name}] No rooms configured, skipping.")
        return

    # 目前只支持单房间，多房间可扩展
    room = rooms[0]
    room_id = room["id"]
    room_secret = room.get("secret", "")

    timeout = global_cfg.get("listener_timeout", 3600)
    heartbeat = global_cfg.get("heartbeat_interval", 20)
    max_reconnect = global_cfg.get("reconnect_max_delay", 30)

    # 初始化基准线
    init_msgs = fetch_messages(room_id)
    last_seen_id = max((m.get("id", 0) for m in init_msgs), default=0)

    log(f"[{name}] Room {room_id} | Timeout {timeout}s")
    log(f"[{name}] Watching for: {', '.join(aliases)}")
    log(f"[{name}] Baseline ID: {last_seen_id}")

    pending_messages = []
    mention_detected = False
    ws_url = f"{BASE_WS}/ws/{room_id}"
    reconnect_delay = 1.0
    start_time = time.time()

    while True:
        if timeout and (time.time() - start_time) > timeout:
            log(f"\n[{name}] Timeout ({timeout}s). No mentions.")
            return

        try:
            async with websockets.connect(
                ws_url, ping_interval=heartbeat, ping_timeout=10
            ) as ws:
                reconnect_delay = 1.0
                log(f"[{name}] WS connected", flush=True)

                async for raw in ws:
                    if timeout and (time.time() - start_time) > timeout:
                        log(f"\n[{name}] Timeout ({timeout}s). No mentions.")
                        return

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

                    if sender.lower() == name.lower():
                        continue
                    if msg_type != "message":
                        continue

                    pending_messages.append(msg)

                    for alias in aliases:
                        if alias in content:
                            mention_detected = True
                            break

                    if mention_detected:
                        log(f"\n{'=' * 50}")
                        log(f"[{name}] ALERT: {len(pending_messages)} new message(s)!")
                        log(f"{'=' * 50}")
                        for m in pending_messages:
                            ts = m.get("created_at", "")[:19]
                            s = m.get("sender_name", "unknown")
                            c = m.get("content", "")
                            log(f"\n[{ts}] @{s}:\n  {c}")
                        log(f"\n{'=' * 50}")
                        log("EXIT_WITH_MESSAGES")
                        return

        except Exception as e:
            log(
                f"[{name}] WS error: {e}, reconnect in {reconnect_delay}s...",
                flush=True,
            )
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect)


def main():
    # 启动前清空旧日志
    LOG_FILE.write_text("", encoding="utf-8")

    target_agent = sys.argv[1] if len(sys.argv) > 1 else None

    config_path = Path("config/agents.yaml")
    if not config_path.exists():
        log(f"Config not found: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))
    global_cfg = config.get("global", {})

    agents = config.get("agents", [])
    if not agents:
        log("No agents configured.")
        sys.exit(1)

    if target_agent:
        # 启动指定 Agent
        try:
            agent = get_agent_config(config, target_agent)
        except ValueError as e:
            log(f"Error: {e}")
            log(f"Available agents: {', '.join(list_agents(config))}")
            sys.exit(1)

        if not agent.get("enabled", True):
            log(f"Agent '{target_agent}' is disabled.")
            sys.exit(1)

        asyncio.run(listen_agent(agent, global_cfg))
    else:
        # 启动所有启用的 Agent
        tasks = []
        for agent in agents:
            if not agent.get("enabled", True):
                log(f"[{agent['name']}] Skipped (disabled)")
                continue
            tasks.append(listen_agent(agent, global_cfg))

        if tasks:
            asyncio.run(asyncio.gather(*tasks))
        else:
            log("No enabled agents to start.")


if __name__ == "__main__":
    sys.exit(main())
