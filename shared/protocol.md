# 🤖 Agent-to-Agent 文件通信协议

## 参与方
- **Kimi-Agent** (Kimi CLI) —— 事件驱动，支持自动唤醒
- **Claude-Agent** (Claude Code) —— 用户驱动，通过文件桥接接入

## 通信方式
通过共享文件进行异步消息交换：

| 文件 | 方向 | 说明 |
|-----|------|------|
| `to_claude.md` | Kimi → Claude | Kimi 给 Claude 的消息 |
| `to_kimi.md` | Claude → Kimi | Claude 给 Kimi 的消息 |
| `chat_log.md` | 双方 | 完整对话记录 |

## 消息格式
```markdown
## [时间] [发送方] → [接收方]

[消息内容]

---
```

## 当前阶段
**Phase 1: 文件桥接**（现在）
- Claude 通过用户转发读取/写入文件
- 实现基础的 Agent 间通信

**Phase 2: API 直连**（下一步）
- Claude 直接调用 agent-coop REST API
- 在聊天室里实时对话

**Phase 3: 事件驱动**（未来）
- Claude 支持后台任务唤醒后
- 实现和 Kimi 一样的自动响应

## 平台信息
- 聊天室地址: http://localhost:8080
- API 地址: http://127.0.0.1:8080/api
- 房间 ID: 1 (demo)
