# Agent Coop — 协同协议（技术机制版）

> 人类要求：用技术机制解决协同冲突，不只是口头约定。

## 1. 代码所有权边界

| 目录/文件 | 负责人 | 说明 |
|-----------|--------|------|
| `backend/` | kimi-agent | API、数据库模型、迁移、业务逻辑 |
| `adapters/` | kimi-agent | 监听脚本、MCP适配器 |
| `scripts/` | kimi-agent | 启动脚本、部署工具 |
| `cli/` | kimi-agent | CLI 命令行工具 |
| `frontend/src/` | claude-agent | React组件、页面逻辑 |
| `frontend/public/` | claude-agent | 静态资源、主题CSS |
| `docs/` | 共享 | 需获取锁 |
| `tests/` | 共享 | 需获取锁 |
| `requirements.txt` / `package.json` | 共享 | 需获取锁 |
| `README.md` / `CLAUDE.md` | 共享 | 需获取锁 |

**规则**：修改对方负责的文件前，必须在聊天室 @ 对方获取许可，同时通过锁 API 获取文件锁。

## 2. 编辑锁机制（技术 enforcement）

### API 端点

```
POST   /api/rooms/{room_id}/locks      # 获取锁
GET    /api/rooms/{room_id}/locks      # 列出活跃锁
DELETE /api/rooms/{room_id}/locks/{id} # 释放锁
```

### 使用流程

```bash
# 1. 检查目标文件是否被锁
curl http://127.0.0.1:8080/api/rooms/1/locks

# 2. 获取锁（TTL默认300秒）
curl -X POST http://127.0.0.1:8080/api/rooms/1/locks \
  -H "Content-Type: application/json" \
  -d '{"file_path": "frontend/src/App.tsx", "agent_name": "kimi-agent", "ttl_seconds": 300}'

# 3. 编辑文件...

# 4. 提交并释放锁
curl -X DELETE http://127.0.0.1:8080/api/rooms/1/locks/{lock_id}
```

### 冲突响应

如果文件已被锁定，API 返回 409：
```json
{"detail": "File locked by kimi-agent until 2026-05-21T12:32:19"}
```

## 3. Git 工作树隔离（物理隔离）

为彻底避免文件覆盖，每个 Agent 使用独立工作树：

```bash
# 主仓库（claude-agent）
cd /Users/hqyone/Documents/projects/agent-coop

# 为 kimi-agent 创建独立工作树
git worktree add ../agent-coop-kimi kimi/dev

# kimi-agent 在 ../agent-coop-kimi 工作
# 互不干扰，合并时 git merge
```

**当前状态**：暂不强制工作树，以锁机制为主。如冲突持续，启用工作树。

## 4. 通信协议

- **所有协调走聊天室**，不私下通信
- 需要对方协作时，@ 提及对方
- 修改共享文件前，先发消息说明意图，等对方确认
- 回复时明确引用上下文（避免"前面说的"这类模糊表述）

## 5. 监听-唤醒-续杯机制

### 架构

```
单次监听器后台运行 ──@提及──→ 退出 + 输出消息 ──→ 系统通知 ──→ Agent处理
                                                          │
                                                          └── 手动续杯（启动新监听器）
```

### 规则

1. **事件驱动**：监听是单次任务，被 @ 触发后退出
2. **手动续杯**：处理完成后，Agent 需主动启动下一个监听器
3. **状态可见**：前端成员列表显示「监听中 / 未监听 / 离线」双层状态
4. **不轮询**：不使用循环脚本，避免资源浪费和通知丢失

### 续杯命令

```bash
# 统一监听器（所有 Agent 通用）
.venv/bin/python cli/listener.py --agent <agent_name> --room <room_id> --timeout 28800

# 启动 2 个实例（推荐）
.venv/bin/python cli/listener.py --agent Kimi-Agent --room 1 --timeout 28800
.venv/bin/python cli/listener.py --agent Kimi-Agent --room 1 --timeout 28800
```

## 6. 冲突处理流程

```
发现冲突（文件被覆盖）
    │
    ├── 1. 在聊天室 @ 对方说明冲突文件
    ├── 2. 查看 git log 确认各自改动
    ├── 3. 协商保留哪个版本或合并
    └── 4. 人工裁决：人类用户有最终决定权
```
