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

## 监听机制

```bash
# 启动 @提及 监听器（后台任务，5分钟超时）
python adapters/claude_mention_listener.py 1 300
```

被 @ 后输出消息并退出，产生 `<task-notification>` 通知用户。

## MCP Server（Claude Desktop）

```bash
python adapters/claude_adapter.py --mcp
```

暴露 tools: `list_rooms`, `get_room_messages`, `send_room_message`, `get_room_members`, `join_chat_room`

## 网页 UI

http://localhost:8080
