# AgentRoom 开源前 Review 报告

> 军师全面审查，2026-05-23

---

## 一、项目整体评估

**结论：代码质量良好，架构清晰，适合开源。关键问题已修复。**

| 维度 | 评分 | 状态 |
|------|------|------|
| 架构设计 | ⭐⭐⭐⭐⭐ | 前后端分离，模块化清晰 |
| 代码质量 | ⭐⭐⭐⭐⭐ | 风格一致，错误处理完整 |
| 安全性 | ⭐⭐⭐⭐⭐ | token 暴露问题已修复 |
| 测试覆盖 | ⭐⭐⭐⭐⭐ | 22个测试全部通过 |
| 文档 | ⭐⭐⭐⭐ | 基本完整，需小幅更新 |
| 部署 | ⭐⭐⭐⭐⭐ | Docker + Makefile 完整 |

---

## 二、必须修复的问题（开源阻塞）

### 问题 1：安全漏洞 — token/secret 暴露

**严重程度：高**

- `schemas.py` 的 `MemberOut` 包含 `token` 字段 → 成员列表 API 会泄露认证凭证
- `schemas.py` 的 `RoomOut` 包含 `secret` 字段 → 房间列表 API 会泄露房间密钥

**修复方案**：
1. `MemberOut` 去掉 `token` 字段
2. 新建 `RoomListItem`（不含 secret），用于房间列表
3. `RoomOut` 保留 secret，仅在 join 等需要的场景返回

**分派：@Kimi-Agent**

---

### 问题 2：测试用例过时（9个失败）

**严重程度：高**

测试使用旧的 `from_name` 认证方式，当前 API 使用 `X-Member-Token`。

失败的测试：
- `test_send_message` — 认证方式过时
- `test_send_message_no_secret` — 认证方式过时
- `test_list_messages` — 认证方式过时
- `test_edit_message` — 认证方式过时
- `test_delete_message` — 认证方式过时
- `test_send_message_with_attachment` — 认证方式过时
- `test_message_rate_limit` — 房间列表为空（未认证）
- `test_message_rate_limit_per_user` — 房间列表为空（未认证）
- `test_list_rooms_after_create` — 房间列表需要认证

**修复方案**：
1. 测试先 join 房间获取 token
2. 后续请求使用 `X-Member-Token` header
3. `list_rooms` 测试需要先认证

**分派：@Kimi-Agent**

---

### 问题 3：CLI 缺少 room leave 命令

**严重程度：中**

后端 API 已有 `DELETE /members/{id}`，但 CLI 没有对应命令。

**修复方案**：
在 `cli/main.py` 添加 `room leave` 命令（或确认 `members remove` 已可用）。

**分派：@Kimi-Agent**

---

## 三、建议改进（非阻塞）

### 改进 1：前端打包体积优化

当前打包 1MB（超过 500KB 警告）。可用 `React.lazy` + `Suspense` 实现代码分割。

**分派：@claude-agent**

### 改进 2：前端无测试

只有后端有测试，前端没有任何测试。建议添加关键组件的单元测试。

**分派：@claude-agent**

---

## 四、已确认良好的模块

| 模块 | 评价 |
|------|------|
| WebSocket 连接管理 | 优秀 — 心跳、断线重连、agent 注册 |
| 认证机制 | 优秀 — cookie + header 多种方式 |
| 数据模型 | 优秀 — 关系完整，索引合理 |
| 监听器逻辑 | 优秀 — to_name 触发、文件锁协调 |
| 前端 @mention | 优秀 — 绿色徽章区分触发/普通 @ |
| 消息列表虚拟化 | 优秀 — @tanstack/react-virtual |
| 配置管理 | 优秀 — pydantic-settings |
| 日志系统 | 优秀 — structlog + trace ID |
| 数据库迁移 | 优秀 — Alembic 管理 |
| Docker 部署 | 优秀 — 多阶段构建 |
| Makefile | 优秀 — 命令完整 |
| 文档 | 良好 — AGENTS.md / COLLABORATION.md |

---

## 五、开源前检查清单

- [x] 修复 token 暴露（@claude-agent）✅ 已完成
- [x] 修复测试用例（@claude-agent）✅ 22个测试全部通过
- [x] 前端打包体积优化（@claude-agent）✅ 主 chunk 从 1023KB 降到 60KB
- [x] 前端构建检查（@claude-agent）✅ 无 TypeScript 错误
- [x] 代码风格检查（@claude-agent）✅ 已自动修复 27 个问题
- [ ] 确认 room leave CLI 可用（待确认）
- [ ] 更新 README.md（如有需要）
- [x] 确保 `make test` 全部通过 ✅ 22 passed
- [x] 确保 `make lint` 无核心代码错误 ✅ 剩余 9 个在 scripts/ 目录

---

## 六、2026-05-24 上线前复查

### 当前状态

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 测试 | 22 passed | 全部通过 |
| token/secret 暴露 | 已修复 | schemas.py 已清理 |
| 前端打包 | 60KB | 已优化 |
| lint | 通过 | 核心代码无错误 |
| WS 断连 bug | 已修复 | 心跳协议已对齐 |
| skill 重构 | 已完成 | 通用 + 适配层分离 |

### 新增问题

| 检查项 | 状态 | 说明 |
|--------|------|------|
| CLI 打包 | 缺失 | 无 pyproject.toml / setup.py，无法 pip install |
| 账号系统 | 缺失 | 无 User 表，无注册/登录，无前端 UI |
| 代码提交 | 未提交 | 大量改动在工作区，未 commit |
| Makefile agent 命令 | 硬编码 | 只针对 Kimi-Agent，不通用 |

### 上线前必须做的事（阻塞）

1. **Commit 所有改动** — 当前 41 个文件在工作区
2. **CLI 打包** — 添加 pyproject.toml，支持 `pip install agentroom`
3. **确认 README** — 新功能（drafts、read status、invites）是否已文档化

### 上线后做或不做（非阻塞）

1. **账号系统** — 需要 User 表 + 注册/登录 API + 前端 UI，工作量较大
2. **room leave 别名** — `room leave` 命令作为 `members remove` 的别名
3. **通用 Makefile** — `make agent` 支持任意 agent 名称
