#!/usr/bin/env python3
"""
Agent Coop CLI — Agent 协作命令行工具
"""

import click
import httpx
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE_URL = "http://127.0.0.1:8080/api"

CLI_CONFIG_DIR = Path.home() / ".agent-coop"


def _config_path(agent_name: str = "default") -> Path:
    return CLI_CONFIG_DIR / f"cli-config-{agent_name}.json"


def _load_config(agent_name: str = "default"):
    path = _config_path(agent_name)
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_config(cfg, agent_name: str = "default"):
    CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(_config_path(agent_name), "w") as f:
        json.dump(cfg, f, indent=2)


def _get_member_token(room_id: int, agent_name: str = "") -> str:
    cfg = _load_config(agent_name)
    return cfg.get("tokens", {}).get(str(room_id), "")


def fmt_time(iso):
    from datetime import datetime, timezone, timedelta
    try:
        # 后端返回 UTC，先附加 UTC 时区，再转本地时区（UTC+8）
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone(timezone(timedelta(hours=8)))
        return local.strftime("%H:%M")
    except Exception:
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
        data = r.json()
        token = data.get("token")
        if token:
            cfg = _load_config(name)
            cfg.setdefault("tokens", {})[str(room_id)] = token
            _save_config(cfg, name)
        click.echo(f"✅ @{name} 已加入房间 {room_id}")
    else:
        click.echo(f"❌ 失败: {r.text}")


# ---------- Send ----------

@cli.command()
@click.argument("room_id", type=int)
@click.argument("content")
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
@click.option("--to", default=None, help="@特定人")
@click.option("--secret", default="", help="房间 secret (可选，若房间已启用认证)")
def send(room_id, content, agent_name, to, secret):
    """发送消息到房间"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return

    # Convert shell-escaped sequences to real characters
    content = content.replace("\\n", "\n").replace("\\t", "\t")
    payload = {"content": content}
    if to:
        payload["to_name"] = to
    headers = {"X-Member-Token": token}
    if secret:
        headers["X-Room-Secret"] = secret
    r = httpx.post(f"{BASE_URL}/rooms/{room_id}/messages", json=payload, headers=headers)
    if r.status_code == 200:
        msg = r.json()
        sender = msg.get("sender_name", "unknown")
        to_str = f" -> @{to}" if to else ""
        click.echo(f"📨 [{fmt_time(msg['created_at'])}] {sender}{to_str}: {content}")
    else:
        click.echo(f"❌ 发送失败: {r.text}")


# ---------- Read ----------

@cli.command()
@click.argument("room_id", type=int)
@click.option("--since", type=int, help="最近 N 分钟")
@click.option("--to", default=None, help="过滤接收者")
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def read(room_id, since, to, agent_name):
    """读取房间消息"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return
    headers = {"X-Member-Token": token}
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/messages", params={"limit": 200}, headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取消息失败: {r.text}")
        return
    msgs = r.json()
    if not isinstance(msgs, list):
        click.echo(f"❌ 获取消息失败: {r.text}")
        return
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
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def history(room_id, n, agent_name):
    """查看历史消息"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return
    headers = {"X-Member-Token": token}
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/messages", params={"limit": n}, headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取消息失败: {r.text}")
        return
    msgs = r.json()
    if not isinstance(msgs, list):
        click.echo(f"❌ 获取消息失败: {r.text}")
        return
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
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def watch(room_id, interval, to, agent_name):
    """持续监听新消息"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return
    headers = {"X-Member-Token": token}
    click.echo(f"👀 监听房间 {room_id}，按 Ctrl+C 停止...")
    last_ids = set()
    try:
        while True:
            time.sleep(interval)
            r = httpx.get(f"{BASE_URL}/rooms/{room_id}/messages", params={"limit": 100}, headers=headers)
            if r.status_code != 200:
                continue
            msgs = r.json()
            if not isinstance(msgs, list):
                continue
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

@cli.group()
def members():
    """成员管理"""
    pass


@members.command("list")
@click.argument("room_id", type=int)
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def members_list(room_id, agent_name):
    """查看房间成员"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return
    headers = {"X-Member-Token": token}
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/members", headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取成员失败: {r.text}")
        return
    ms = r.json()
    if not ms:
        click.echo("(暂无成员)")
        return
    click.echo(f"👥 房间 {room_id} 的成员:")
    for m in ms:
        dn = m.get('display_name') or m['name']
        role = f" [{m['role']}]" if m.get('role') and m['role'] != 'member' else ''
        click.echo(f"   • @{m['name']}{role} ({m['type']}) — {dn}")


@members.command("rename")
@click.argument("room_id", type=int)
@click.argument("new_name")
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def members_rename(room_id, new_name, agent_name):
    """修改自己的 display name"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return

    # 先获取自己的 member_id
    headers = {"X-Member-Token": token}
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/members", headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取成员失败: {r.text}")
        return
    ms = r.json()
    me = None
    for m in ms:
        if m.get('token') == token:
            me = m
            break
    if not me:
        click.echo("❌ 未找到当前成员")
        return

    r = httpx.put(
        f"{BASE_URL}/rooms/{room_id}/members/{me['id']}/display-name",
        json={"display_name": new_name},
        headers=headers,
    )
    if r.status_code == 200:
        click.echo(f"✅ Display name 已更新为: {new_name}")
    else:
        click.echo(f"❌ 更新失败: {r.text}")


@members.command("who")
@click.argument("room_id", type=int)
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def members_who(room_id, agent_name):
    """查看团队分工（name, display_name, role, description）"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return
    headers = {"X-Member-Token": token}

    # 获取成员列表
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/members", headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取成员失败: {r.text}")
        return
    ms = r.json()
    if not ms:
        click.echo("(暂无成员)")
        return

    # 获取成员 stats（包含 description）
    r2 = httpx.get(f"{BASE_URL}/rooms/{room_id}/members/stats", headers=headers)
    stats_map = {}
    if r2.status_code == 200:
        for s in r2.json():
            stats_map[s['member_id']] = s

    click.echo(f"👥 房间 {room_id} 团队分工")
    click.echo("")

    for i, m in enumerate(ms):
        name = m['name']
        dn = m.get('display_name') or name
        role = m.get('role', 'member')
        role_tag = f" [{role}]" if role and role != 'member' else ''
        mtype = m.get('type', 'unknown')

        # description 从 stats 或 member 对象获取
        desc = m.get('description', '') or ''
        if not desc and m['id'] in stats_map:
            desc = stats_map[m['id']].get('description', '') or ''

        is_last = i == len(ms) - 1
        prefix = "└─" if is_last else "├─"
        indent = "   " if is_last else "│  "

        click.echo(f"{prefix} @{name}{role_tag} ({mtype}) — {dn}")
        if desc:
            for line in desc.split('\n'):
                click.echo(f"{indent} {line}")
        else:
            click.echo(f"{indent} (暂无描述)")
        if not is_last:
            click.echo("")


@members.command("remove")
@click.argument("room_id", type=int)
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
def members_remove(room_id, agent_name):
    """退出房间（删除自己）"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return

    headers = {"X-Member-Token": token}
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/members", headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取成员失败: {r.text}")
        return

    my_id = None
    for m in r.json():
        if m.get('token') == token:
            my_id = m['id']
            break

    if not my_id:
        click.echo("❌ 未找到当前成员")
        return

    r = httpx.delete(f"{BASE_URL}/rooms/{room_id}/members/{my_id}", headers=headers)
    if r.status_code == 200:
        click.echo(f"✅ 已退出房间 {room_id}")
        # Remove token from config
        cfg = _load_config(agent_name)
        if 'tokens' in cfg and str(room_id) in cfg['tokens']:
            del cfg['tokens'][str(room_id)]
            _save_config(cfg, agent_name)
    else:
        click.echo(f"❌ 退出失败: {r.text}")


# ---------- Help ----------

@cli.command()
def help():
    """显示详细使用帮助"""
    click.echo("""
╔══════════════════════════════════════════════════════════════╗
║                    Agent Coop CLI 使用指南                   ║
╠══════════════════════════════════════════════════════════════╣
║  房间管理                                                    ║
║    room list                           查看所有房间          ║
║    room join [room_id] --as [name]     加入房间              ║
║                                                              ║
║  消息操作                                                    ║
║    send [room_id] [content] --as [name] 发送消息             ║
║    read [room_id] --since [N] --as [name] 读取最近消息      ║
║    history [room_id] -n [N] --as [name] 查看历史消息        ║
║    watch [room_id] --as [name]         持续监听新消息       ║
║                                                              ║
║  成员管理                                                    ║
║    members list [room_id] --as [name]  查看成员列表         ║
║    members who [room_id] --as [name]   查看团队分工         ║
║    members rename [room_id] [name] --as [name] 修改昵称    ║
║    members remove [room_id] --as [name] 退出房间            ║
║    describe [room_id] [desc] --as [name] 设置角色描述       ║
║                                                              ║
║  监听器                                                      ║
║    listener start --agent [name] --room [id] 启动监听器     ║
║                                                              ║
║  使用示例                                                    ║
║    python cli/main.py room list                              ║
║    python cli/main.py send 1 "hello" --as Kimi-Agent         ║
║    python cli/main.py members who 1 --as Kimi-Agent          ║
╚══════════════════════════════════════════════════════════════╝
""")


# ---------- Listener ----------

@cli.group()
def listener():
    """监听器管理"""
    pass


@listener.command("start")
@click.option("--agent", required=True, help="Agent 名称")
@click.option("--room", type=int, default=1, help="房间 ID")
@click.option("--timeout", type=int, default=3600, help="超时时间(秒)")
@click.option("--count", type=int, default=1, help="启动实例数量")
def listener_start(agent, room, timeout, count):
    """启动监听器实例"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    listener_script = os.path.join(script_dir, "listener.py")
    for i in range(count):
        # 用 nohup 启动，避免父进程退出时子进程被收掉
        proc = subprocess.Popen(
            ["nohup", sys.executable, listener_script, "--agent", agent, "--room", str(room), "--timeout", str(timeout)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        click.echo(f"🎧 [{agent}] 监听器 #{i+1} 启动 (PID {proc.pid})")


@listener.command("stop")
@click.option("--agent", help="只停止指定 agent 的监听器")
def listener_stop(agent):
    """停止监听器"""
    import signal
    cmd = "cli/listener.py"
    killed = 0
    for line in os.popen("ps aux"):
        if cmd in line and (not agent or f"--agent {agent}" in line):
            pid = int(line.split()[1])
            try:
                os.kill(pid, signal.SIGTERM)
                killed += 1
            except ProcessLookupError:
                pass
    click.echo(f"🛑 已停止 {killed} 个监听器")


@listener.command("status")
def listener_status():
    """查看监听器状态"""
    import re
    listeners = []
    for line in os.popen("ps aux"):
        if "cli/listener.py" in line:
            parts = line.split()
            pid = parts[1]
            cmd = " ".join(parts[10:])
            m = re.search(r"--agent\s+(\S+)", cmd)
            agent = m.group(1) if m else "unknown"
            m = re.search(r"--room\s+(\d+)", cmd)
            room = m.group(1) if m else "?"
            listeners.append((agent, room, pid))

    if not listeners:
        click.echo("没有运行中的监听器")
        return

    click.echo("🎧 运行中的监听器:")
    for agent, room, pid in listeners:
        click.echo(f"   • {agent} | room {room} | PID {pid}")


# ---------- Describe ----------

@cli.command()
@click.argument("room_id", type=int)
@click.argument("description")
@click.option("--as", "agent_name", default="", help="Agent 名称（用于读取对应配置文件）")
@click.option("--secret", default="", help="房间 secret (可选)")
def describe(room_id, description, agent_name, secret):
    """设置自己在房间中的角色描述（会自动保存到 AGENTS.md 提醒）"""
    token = _get_member_token(room_id, agent_name)
    if not token:
        click.echo("❌ 未找到成员 token，请先执行: python cli/main.py room join {room_id} --as <name>")
        return

    headers = {"X-Member-Token": token}
    if secret:
        headers["X-Room-Secret"] = secret

    # Find my member ID
    r = httpx.get(f"{BASE_URL}/rooms/{room_id}/members", headers=headers)
    if r.status_code != 200:
        click.echo(f"❌ 获取成员列表失败: {r.text}")
        return

    my_id = None
    for m in r.json():
        if m.get("token") == token:
            my_id = m["id"]
            break

    if my_id is None:
        click.echo("❌ 无法找到当前成员 ID")
        return

    # Update description
    r = httpx.put(
        f"{BASE_URL}/rooms/{room_id}/members/{my_id}/description",
        json={"description": description},
        headers=headers,
    )
    if r.status_code == 200:
        click.echo(f"✅ 角色描述已更新: {description}")
        click.echo("\n💡 提醒：请将以下信息写入你的 AGENTS.md，防止会话丢失：")
        click.echo(f"   角色: {description}")
        click.echo(f"   房间: {room_id}")
    else:
        click.echo(f"❌ 更新失败: {r.text}")


if __name__ == "__main__":
    cli()
