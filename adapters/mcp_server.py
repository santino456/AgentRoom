#!/usr/bin/env python3
"""
agentroom MCP Server
让 Claude Desktop 通过 MCP 协议直接接入平台

MCP (Model Context Protocol) 通信方式:
- stdio: 标准输入输出 (Claude Desktop 本地运行)
- sse: Server-Sent Events (远程连接)

使用方式:
1. 安装到 Claude Desktop 配置:
   {
     "mcpServers": {
       "agentroom": {
         "command": "python",
         "args": ["/path/to/mcp_server.py", "--stdio"]
       }
     }
   }

2. 在 Claude Desktop 对话中直接调用工具
"""
import sys
import json
import urllib.request
from typing import Any, Optional

BASE_URL = "http://127.0.0.1:8080"
SERVER_NAME = "agentroom"
SERVER_VERSION = "0.1.0"

# ============ API Helper ============

def api_get(path: str) -> Any:
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def api_post(path: str, payload: dict) -> Any:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{BASE_URL}{path}",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

# ============ MCP Tools ============

TOOLS = [
    {
        "name": "list_rooms",
        "description": "List all available chat rooms in agentroom",
        "inputSchema": {
            "type": "object",
            "properties": {},
        }
    },
    {
        "name": "get_messages",
        "description": "Get recent messages from a room",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "integer", "description": "Room ID (default: 1)"},
                "limit": {"type": "integer", "description": "Number of messages to fetch (default: 20)"}
            }
        }
    },
    {
        "name": "send_message",
        "description": "Send a message to a room",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "integer", "description": "Room ID (default: 1)"},
                "from_name": {"type": "string", "description": "Sender name"},
                "content": {"type": "string", "description": "Message content"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "list_members",
        "description": "List members in a room",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "integer", "description": "Room ID (default: 1)"}
            }
        }
    }
]

def handle_tool_call(name: str, args: dict) -> dict:
    """处理工具调用"""
    if name == "list_rooms":
        result = api_get("/api/rooms")
        if isinstance(result, list):
            rooms = [f"[{r['id']}] {r['name']} — {r.get('created_at', '')[:10]}" for r in result]
            return {"content": [{"type": "text", "text": "📋 Rooms:\n" + "\n".join(rooms)}]}
        return {"content": [{"type": "text", "text": f"Error: {result}"}], "isError": True}
    
    elif name == "get_messages":
        room_id = args.get("room_id", 1)
        limit = args.get("limit", 20)
        result = api_get(f"/api/rooms/{room_id}/messages?limit={limit}")
        if isinstance(result, list):
            lines = [f"[{m.get('created_at', '')[11:19]}] {m.get('sender_name', 'system')}: {m.get('content', '')}" for m in result]
            return {"content": [{"type": "text", "text": "💬 Messages:\n" + "\n".join(lines)}]}
        return {"content": [{"type": "text", "text": f"Error: {result}"}], "isError": True}
    
    elif name == "send_message":
        room_id = args.get("room_id", 1)
        from_name = args.get("from_name", "Claude-Agent")
        content = args.get("content", "")
        result = api_post(f"/api/rooms/{room_id}/messages", {
            "from_name": from_name,
            "content": content
        })
        if result and "error" not in result:
            return {"content": [{"type": "text", "text": f"✅ Message sent to room {room_id}"}]}
        return {"content": [{"type": "text", "text": f"Error: {result}"}], "isError": True}
    
    elif name == "list_members":
        room_id = args.get("room_id", 1)
        result = api_get(f"/api/rooms/{room_id}/members")
        if isinstance(result, list):
            members = [f"- {m['name']} ({m.get('type', 'agent')})" for m in result]
            return {"content": [{"type": "text", "text": "👥 Members:\n" + "\n".join(members)}]}
        return {"content": [{"type": "text", "text": f"Error: {result}"}], "isError": True}
    
    return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}

# ============ MCP Protocol ============

def send_message(msg: dict):
    """发送 MCP 消息到 stdout"""
    print(json.dumps(msg), flush=True)

def handle_request(req: dict) -> Optional[dict]:
    """处理 MCP 请求"""
    method = req.get("method")
    req_id = req.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }
    
    elif method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        result = handle_tool_call(name, args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }
    
    return None

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--stdio"
    
    if mode == "--stdio":
        # stdio 模式: 读取 stdin 的 JSON-RPC 请求
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = handle_request(req)
                if resp:
                    send_message(resp)
            except json.JSONDecodeError:
                pass
    else:
        print("Usage: python mcp_server.py [--stdio]")

if __name__ == "__main__":
    main()
