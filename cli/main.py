#!/usr/bin/env python3
"""
Agent Coop CLI — Agent 协作命令行工具
"""

import click
import httpx
import time
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8080/api"


def fmt_time(iso):
    try:
        return iso[11:16]
    except Exception:
        return ""


@click.group()
def cli():
    """Agent Coop — 本地 Agent 协作平台 CLI"""
    pass


# ---------- Room ----------

@cli.group()
def room():
    """房间管理"""
    pass


@room.command("list")
def room_list():
    """列出所有房间"""
    r = httpx.get(f"{BASE_URL}/rooms")
    rooms = r.json()
    if not rooms:
        click.echo("(暂无房间)")
        return
    click.echo("📋 房间列表:")
    for rm in rooms:
        click.echo(f"   [{rm['id']}] {rm['name']} — {rm['created_at'][:10]}")


@room.command("create")
@click.argument("name")
def room_create(name):
    """创建房间"""
    r = httpx.post(f"{BASE_URL}/rooms", json={"name": name})
    if r.status_code == 200:
        rm = r.json()
        click.echo(f"✅ 房间 '{rm['name']}' 创建成功 (id={rm['id']})")
    else:
        click.echo(f"❌ 失败: {r.text}")


@room.command("join")
@click.argument("room_id", type=int)
@click.option("--as", "name", required=True, help="你的 Agent 名称")
@click.option("--type", "type_", default="agent", help="类型: agent/human")
@click.option("--secret", default="", help="房间 secret (可选，若房间已启用认证)")
def room_join(room_id, name, type_, secret):
    """加入房间"""
    headers = {}
    if secret:
        headers["X-Room-Secret"] = secret
    r = httpx.post(f"{BASE_URL}/rooms/{room_id}/join", json={"name": name, "type": type_}, headers=headers)
    if r.status_code == 200:
        click.echo(f"✅ @{name} 已加入房间 {room_id}")
    else:
        click.echo(f"❌ 失败: {r.text}")


# ---------- Send ----------

@cli.command()
@click.argument("room_id", type=int)
@click.argument("content")
@click.option("--from", "from_", default="human", help="发送者名称")
@click.option("--to", default=None, help="@特定人")
@click.option("--secret", default="", help="房间 secret (可选，若房间已启用认证)")
def send(room_id, content, from_, to, secret):
    """发送消息到房间"""
    payload = {"from_name": from_, "content": content}
    if to:
        payload["to_name"] = to
    headers = {}
    if secret:
        headers["X-Room-Secret"] = secret
    r = httpx.post(f"{BASE_URL}/rooms/{room_id}/messages", json=payload, headers=headers)
    if r.status_code == 200:
        msg = r.json()
        to_str = f" -> @{to}" if to else ""
        click.echo(f"📨 [{fmt_time(msg['created_at'])}] {from_}{to_str}: {content}")
    else:
        click.echo(f"❌ 发送失败: {r.text}")


# ---------- Read ----------

@cli.command()
@click.argument("room_id", type=int)
@click.option("--since", type=int, help="最近 N 分钟")
@click.option("--to", default=None, help="过滤接收者")
def read(room_id, since, to):
    """读取房间消息"""
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/messages", params={"limit": 200})
    msgs = r.json()
    if since:
        cutoff = (datetime.utcnow() - timedelta(minutes=since)).isoformat()
        msgs = [m for m in msgs if m["created_at"] >= cutoff]
    if to:
        msgs = [m for m in msgs if m.get("to_name") in [to, None] or m.get("to_name") == to]

    if not msgs:
        click.echo("(暂无新消息)")
        return

    for m in msgs:
        to_str = f" -> @{m['to_name']}" if m.get("to_name") else ""
        sender = m.get("sender_name") or "system"
        click.echo(f"[{fmt_time(m['created_at'])}] {sender}{to_str}: {m['content']}")


# ---------- History ----------

@cli.command()
@click.argument("room_id", type=int)
@click.option("-n", default=50, help="最近 N 条")
def history(room_id, n):
    """查看历史消息"""
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/messages", params={"limit": n})
    msgs = r.json()
    if not msgs:
        click.echo("(暂无消息)")
        return
    click.echo(f"--- 最近 {len(msgs)} 条消息 ---")
    for m in msgs:
        to_str = f" -> @{m['to_name']}" if m.get("to_name") else ""
        sender = m.get("sender_name") or "system"
        click.echo(f"[{fmt_time(m['created_at'])}] {sender}{to_str}: {m['content']}")


# ---------- Watch ----------

@cli.command()
@click.argument("room_id", type=int)
@click.option("--interval", default=3, help="检查间隔(秒)")
@click.option("--to", default=None, help="过滤接收者")
def watch(room_id, interval, to):
    """持续监听新消息"""
    click.echo(f"👀 监听房间 {room_id}，按 Ctrl+C 停止...")
    last_ids = set()
    try:
        while True:
            time.sleep(interval)
            r = httpx.get(f"{BASE_URL}/rooms/{room_id}/messages", params={"limit": 100})
            msgs = r.json()
            for m in msgs:
                if m["id"] not in last_ids:
                    if to and m.get("to_name") not in [to, None]:
                        continue
                    to_str = f" -> @{m['to_name']}" if m.get("to_name") else ""
                    sender = m.get("sender_name") or "system"
                    click.echo(f"[{fmt_time(m['created_at'])}] {sender}{to_str}: {m['content']}")
                    last_ids.add(m["id"])
    except KeyboardInterrupt:
        click.echo("\n监听已停止。")


# ---------- Members ----------

@cli.command()
@click.argument("room_id", type=int)
def members(room_id):
    """查看房间成员"""
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/members")
    ms = r.json()
    if not ms:
        click.echo("(暂无成员)")
        return
    click.echo(f"👥 房间 {room_id} 的成员:")
    for m in ms:
        click.echo(f"   • @{m['name']} ({m['type']})")


if __name__ == "__main__":
    cli()
