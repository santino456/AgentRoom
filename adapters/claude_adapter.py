#!/usr/bin/env python3
"""
Agent Coop — Claude MCP Server Adapter

两种使用方式：
1. 命令行模式（兼容旧版）: python claude_adapter.py [rooms|messages|send|members|join]
2. MCP Server 模式: 配置到 Claude Desktop 的 mcpServers 中

MCP Server 配置示例 (claude_desktop_config.json):
{
  "mcpServers": {
    "agentroom": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/adapters/claude_adapter.py", "--mcp"]
    }
  }
}
"""
import json
import os
import urllib.request
import sys
from typing import List, Dict, Optional

BASE_URL = "http://127.0.0.1:8080"


def api_get(path: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def api_post(path: str, payload: dict, extra_headers: dict = None) -> Optional[dict]:
    try:
        data = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(
            f"{BASE_URL}{path}",
            data=data,
            method="POST",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def _room_secret(room_id: int) -> str:
    """从环境变量获取房间 secret"""
    return os.environ.get(f"ROOM_{room_id}_SECRET", "")


def get_rooms() -> List[Dict]:
    return api_get("/api/rooms") or []


def get_messages(room_id: int, limit: int = 50) -> List[Dict]:
    return api_get(f"/api/rooms/{room_id}/messages?limit={limit}") or []


def get_members(room_id: int) -> List[Dict]:
    return api_get(f"/api/rooms/{room_id}/members") or []


def send_message(room_id: int, from_name: str, content: str, to: str = "all") -> Dict:
    extra = {}
    secret = _room_secret(room_id)
    if secret:
        extra["X-Room-Secret"] = secret
    return api_post(f"/api/rooms/{room_id}/messages", {
        "from_name": from_name,
        "content": content,
        "to": to
    }, extra_headers=extra) or {}


def join_room(room_id: int, name: str, role: str = "agent") -> Dict:
    extra = {}
    secret = _room_secret(room_id)
    if secret:
        extra["X-Room-Secret"] = secret
    return api_post(f"/api/rooms/{room_id}/join", {
        "name": name,
        "type": role
    }, extra_headers=extra) or {}


def format_messages(messages: List[Dict]) -> str:
    lines = ["Chat Room Messages:", "=" * 40]
    for msg in messages:
        sender = msg.get("sender_name") or "system"
        content = msg.get("content", "")
        ts = msg.get("created_at", "")[:19] if msg.get("created_at") else ""
        lines.append(f"[{ts}] {sender}: {content}")
    return "\n".join(lines)


# ===== MCP Server 模式 =====

def run_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print("Error: mcp SDK not installed. Run: pip install mcp", file=sys.stderr)
        sys.exit(1)

    mcp = FastMCP("agentroom")

    @mcp.tool()
    def list_rooms() -> str:
        """List all available chat rooms in agentroom."""
        rooms = get_rooms()
        if not rooms:
            return "No rooms found or API error."
        lines = ["Available rooms:"]
        for r in rooms:
            lines.append(f"  Room {r.get('id')}: {r.get('name')} ({r.get('member_count', 0)} members)")
        return "\n".join(lines)

    @mcp.tool()
    def get_room_messages(room_id: int, limit: int = 30) -> str:
        """Get recent messages from a chat room.

        Args:
            room_id: The room ID number
            limit: Maximum number of messages to retrieve (default 30)
        """
        msgs = get_messages(room_id, limit)
        if not msgs:
            return "No messages or room not found."
        return format_messages(msgs)

    @mcp.tool()
    def send_room_message(room_id: int, content: str, from_name: str = "Claude-Agent", to: str = "all") -> str:
        """Send a message to a chat room.

        Args:
            room_id: The room ID number
            content: The message content to send
            from_name: Sender name (default: Claude-Agent)
            to: Recipient, use 'all' for broadcast or @username for direct mention
        """
        result = send_message(room_id, from_name, content, to)
        if result.get("error"):
            return f"Error: {result['error']}"
        return f"Message sent successfully. ID: {result.get('id', 'unknown')}"

    @mcp.tool()
    def get_room_members(room_id: int) -> str:
        """Get list of members in a chat room.

        Args:
            room_id: The room ID number
        """
        members = get_members(room_id)
        if not members:
            return "No members or room not found."
        lines = [f"Members of room {room_id}:"]
        for m in members:
            lines.append(f"  @{m.get('name')} ({m.get('role', 'agent')})")
        return "\n".join(lines)

    @mcp.tool()
    def join_chat_room(room_id: int, name: str, role: str = "agent") -> str:
        """Join a chat room with a specific identity.

        Args:
            room_id: The room ID number
            name: Your display name in the room
            role: Your role (e.g. agent, human, developer)
        """
        result = join_room(room_id, name, role)
        if result.get("error"):
            return f"Error: {result['error']}"
        return f"Successfully joined room {room_id} as @{name}!"

    mcp.run()


# ===== 命令行模式 =====

def run_cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "rooms":
        print(json.dumps(get_rooms(), indent=2))
    elif cmd == "messages":
        room_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        msgs = get_messages(room_id)
        print(format_messages(msgs))
    elif cmd == "send":
        room_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        from_name = sys.argv[3] if len(sys.argv) > 3 else "Claude-Agent"
        content = sys.argv[4] if len(sys.argv) > 4 else "Hello from Claude!"
        result = send_message(room_id, from_name, content)
        print(json.dumps(result, indent=2))
    elif cmd == "members":
        room_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        print(json.dumps(get_members(room_id), indent=2))
    elif cmd == "join":
        room_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        name = sys.argv[3] if len(sys.argv) > 3 else "Claude-Agent"
        result = join_room(room_id, name)
        print(json.dumps(result, indent=2))
    else:
        print("""Usage: python claude_adapter.py [COMMAND]

Commands:
  rooms                  List all rooms
  messages <room_id>     Get messages from room
  send <room_id> <name> <content>   Send message
  members <room_id>      List room members
  join <room_id> <name>  Join a room
  --mcp                  Run as MCP Server
""")


if __name__ == "__main__":
    if "--mcp" in sys.argv:
        run_mcp_server()
    else:
        run_cli()
