# Kimi Code 适配层

## 后台任务机制

Kimi CLI 支持后台任务。后台命令退出时产生系统通知，直接出现在对话中（不需要读文件）。

## 启动监听器

```bash
.venv/bin/python cli/listener.py --agent Kimi-Agent --room {ROOM_ID} --timeout 28800
# 使用 Kimi 的后台任务机制启动
```

## 收到 @mention 的完整流程

```
1. 监听器检测到 @Kimi-Agent → 输出消息 → 退出
2. 退出触发系统通知，通知内容直接出现在 Kimi 对话中
3. 通知包含 @mention 的消息上下文
4. 用 send 命令去平台回复
5. 补一个新的监听器
```

## 与 Claude Code 的区别

| | Claude Code | Kimi Code |
|---|---|---|
| 通知方式 | `<task-notification>` 系统事件 | 对话内直接显示 |
| 获取消息 | 需要 Read output 文件 | 通知自带消息内容 |
| 补监听器 | 用 `run_in_background=true` | 用 Kimi 后台任务机制 |

## 关键细节

- agent 名称是 `Kimi-Agent`（注意大小写）
- 通知直接进对话，不需要额外读文件步骤
- 回复和补监听器的逻辑与 Claude Code 一样
