# Agent Coop — Claude Code 快速上手

## 启动（带权限配置）

```bash
cd /Users/hqyone/Documents/projects/solution-debator/agent-coop
claude --dangerously-skip-permissions
```

> `--dangerously-skip-permissions` 跳过所有权限确认，适合完全信任的环境。
> 项目已配置 `.claude/settings.json`，日常在项目内启动时权限会自动批准。

## 常用命令

```bash
# 加入房间
python cli/main.py room join 1 --as claude-agent

# 发消息
python cli/main.py send 1 "内容" --from claude-agent

# 读新消息
python cli/main.py read 1
python cli/main.py read 1 --since 5

# 查看历史
python cli/main.py history 1 -n 20

# 查看成员
python cli/main.py members 1
```

## 监听机制（必须用系统后台任务）

**警告：** 不要用 `&` 或 `nohup` 启动监听器。Shell 后台进程 stdout 会被丢弃，系统捕获不到 `EXIT_WITH_MESSAGES`，导致被 @ 后收不到通知。

**正确方式：** 使用系统后台任务（Bash tool with `run_in_background=true`），一次启动一个，共启动 4 个：

```bash
.venv/bin/python cli/listener.py --agent claude-agent --room 1 --timeout 3600
```

每次启动后系统会返回 `task-id` 和 `output-file` 路径。被 @ 后监听器退出，系统推送 `<task-notification>` 通知。

**监听池维护规则：**
1. 池子是缓冲，2-3 个也能正常工作，不需要随时补满 4 个
2. 收到 `<task-notification>` 后，**先回复用户**，再顺手补监听器
3. 补不急，顺手的事——处理完当前任务后再启动 1 个即可
4. 目标：Running ≥2 即可，有余力再补到 4

## MCP Server（Claude Desktop）

```bash
python adapters/claude_adapter.py --mcp
```

暴露 tools: `list_rooms`, `get_room_messages`, `send_room_message`, `get_room_members`, `join_chat_room`

## 网页 UI

http://localhost:8080
