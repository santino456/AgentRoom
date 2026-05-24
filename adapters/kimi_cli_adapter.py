#!/usr/bin/env python3
"""
Kimi CLI Adapter
利用 Kimi CLI 的后台任务 + 系统通知机制实现事件驱动 Agent

机制：
1. 启动后台监听器进程，轮询聊天室消息
2. 检测到有 @Kimi-Agent 时，监听器输出消息并退出
3. 退出产生系统通知，唤醒 Kimi CLI 中的 Agent
4. Agent 读取消息、生成回复、重新启动监听器
"""
import sys
import time
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"
KIMI_NAMES = {"Kimi-Agent", "kimi", "Kimi"}


def api_get(path: str):
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def is_mentioning_kimi(content: str) -> bool:
    if not content:
        return False
    for name in KIMI_NAMES:
        if f"@{name}" in content:
            return True
    return False


def run_listener(room_id: int = 1, poll_interval: int = 2):
    """
    运行一次监听循环
    返回: (has_messages: bool, messages: list) 
    当检测到有 @Kimi-Agent 时返回消息列表，否则返回空列表
    """
    messages = api_get(f"/api/rooms/{room_id}/messages") or []
    last_seen_id = max((m["id"] for m in messages), default=0)
    
    print(f"🤖 Kimi-Agent @监听器 | 房间: {room_id} | 从 ID={last_seen_id} 开始", flush=True)
    
    pending_messages = []
    
    try:
        while True:
            time.sleep(poll_interval)
            messages = api_get(f"/api/rooms/{room_id}/messages") or []
            new_msgs = [m for m in messages if m["id"] > last_seen_id]
            
            mention_detected = False
            for msg in new_msgs:
                last_seen_id = msg["id"]
                sender_name = msg.get("sender_name") or "unknown"
                content = msg.get("content", "")
                msg_type = msg.get("msg_type", "message")
                
                # 忽略自己和系统消息
                if sender_name in KIMI_NAMES or msg_type != "message":
                    continue
                
                pending_messages.append({
                    "id": msg["id"],
                    "sender": sender_name,
                    "content": content,
                    "time": msg.get("created_at", "")
                })
                
                if is_mentioning_kimi(content):
                    mention_detected = True
            
            if mention_detected and pending_messages:
                print(f"\n🚨 @Kimi-Agent 被提及！输出 {len(pending_messages)} 条新消息：", flush=True)
                print("=" * 50, flush=True)
                for msg in pending_messages:
                    ts = msg["time"].split("T")[1][:8] if "T" in msg["time"] else ""
                    print(f"[{ts}] {msg['sender']}: {msg['content']}", flush=True)
                print("=" * 50, flush=True)
                return True, pending_messages
                
    except KeyboardInterrupt:
        print("\n👋 监听器已停止")
        return False, []


if __name__ == "__main__":
    room_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    has_msgs, msgs = run_listener(room_id)
    sys.exit(0 if has_msgs else 0)
