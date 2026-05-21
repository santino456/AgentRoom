#!/usr/bin/env python3
"""
Agent 文件锁工具 — 编辑前获取锁，防止协同冲突
Usage:
    python scripts/lock_file.py acquire frontend/src/App.tsx kimi-agent
    python scripts/lock_file.py list
    python scripts/lock_file.py release 1
"""
import sys
import urllib.request
import json

API_BASE = "http://127.0.0.1:8080/api"
ROOM_ID = 1


def acquire(file_path: str, agent_name: str, ttl: int = 300):
    body = json.dumps({
        "file_path": file_path,
        "agent_name": agent_name,
        "ttl_seconds": ttl
    }).encode()
    req = urllib.request.Request(
        f"{API_BASE}/rooms/{ROOM_ID}/locks",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"✅ 锁获取成功: {data['file_path']}")
        print(f"   锁ID: {data['id']}, 过期: {data['expires_at']}")
        return data["id"]
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"❌ 获取锁失败: {err.get('detail', e.reason)}")
        return None


def list_locks():
    req = urllib.request.Request(f"{API_BASE}/rooms/{ROOM_ID}/locks")
    resp = urllib.request.urlopen(req)
    locks = json.loads(resp.read())
    if not locks:
        print("🔓 当前无活跃锁")
        return
    print(f"🔒 活跃锁 ({len(locks)} 个):")
    for lock in locks:
        print(f"   [{lock['id']}] {lock['file_path']} → {lock['agent_name']} (过期: {lock['expires_at']})")


def release(lock_id: int):
    req = urllib.request.Request(
        f"{API_BASE}/rooms/{ROOM_ID}/locks/{lock_id}",
        method="DELETE"
    )
    resp = urllib.request.urlopen(req)
    print(f"🔓 锁 {lock_id} 已释放")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "acquire":
        if len(sys.argv) < 4:
            print("Usage: lock_file.py acquire <file_path> <agent_name> [ttl_seconds]")
            sys.exit(1)
        ttl = int(sys.argv[4]) if len(sys.argv) > 4 else 300
        acquire(sys.argv[2], sys.argv[3], ttl)
    elif cmd == "list":
        list_locks()
    elif cmd == "release":
        if len(sys.argv) < 3:
            print("Usage: lock_file.py release <lock_id>")
            sys.exit(1)
        release(int(sys.argv[2]))
    else:
        print(__doc__)
