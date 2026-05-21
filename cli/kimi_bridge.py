#!/usr/bin/env python3
"""Kimi-Agent Bridge: 自动监听聊天室消息 (纯标准库，零依赖)"""
import sys
import time
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8080"
KIMI_AGENT_NAME = "Kimi-Agent"

def api_get(path):
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[ERROR] GET {path} 失败: {e}", flush=True)
        return None

def api_post(path, payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(f"{BASE_URL}{path}", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[ERROR] POST {path} 失败: {e}", flush=True)
        return False

def main():
    room_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    poll_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    print(f"🤖 Kimi-Agent Bridge 启动 | 房间: {room_id} | 轮询: {poll_interval}s")
    print("=" * 50, flush=True)
    
    messages = api_get(f"/api/rooms/{room_id}/messages") or []
    last_seen_id = max((m["id"] for m in messages), default=0)
    
    print(f"📌 已同步 {len(messages)} 条消息，从 ID={last_seen_id} 开始监听...")
    print("⏳ 等待新消息... (Ctrl+C 停止)", flush=True)
    print("-" * 50, flush=True)
    
    try:
        while True:
            time.sleep(poll_interval)
            messages = api_get(f"/api/rooms/{room_id}/messages") or []
            new_msgs = [m for m in messages if m["id"] > last_seen_id]
            
            for msg in new_msgs:
                last_seen_id = msg["id"]
                sender = msg.get("sender") or {}
                sender_name = sender.get("name", "unknown")
                content = msg.get("content", "")
                msg_type = msg.get("msg_type", "message")
                
                if sender_name == KIMI_AGENT_NAME or msg_type != "message":
                    continue
                
                ts = msg.get("created_at", "").split("T")[1][:8] if "T" in msg.get("created_at", "") else ""
                print(f"\n🔔 [{ts}] {sender_name}: {content}", flush=True)
                print(f"[NEW_MSG] room={room_id} sender={sender_name} id={msg['id']}", flush=True)
                print("-" * 50, flush=True)
                
    except KeyboardInterrupt:
        print("\n👋 Bridge 已停止")

if __name__ == "__main__":
    main()
