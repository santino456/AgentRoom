# AgentRoom — Roadmap

> 愿景：从「本地多 Agent 聊天室」演进为「Agent & 人类协作的多 Agent 管理平台」
>
> 终极形态：Agent 与人类协作的企微 / WeChat —— 每个人管理自己的 Agent 团队，Agent 有角色卡片、有 Home，能自主工作、能协作。

---

## 已完成（2026-05-25）

### 全局用户认证系统改造
- ✅ `user_token` 提升为全局身份标识（所有房间共享同一个 token）
- ✅ WebSocket 支持 `user_token` cookie + query param 认证
- ✅ 后端 `dependencies.py`：`X-Member-Token` header 兼容 `user_token`
- ✅ 前端 `useMemberToken.ts`：废弃按房间存 token，改为全局 cookie 模式
- ✅ 前端 `ChatHeader`：新增 WS 状态 `"Need login"` / `"Not joined"`

### WebSocket 稳定性
- ✅ 前端 WebSocket `ping/pong` 心跳
- ✅ 全局单连接限制：同一 member 同一房间只能有一个 WS，新连接踢旧连接
- ✅ WS 1008 (Unauthorized) 不重连

### 多 @mention 支持
- ✅ 后端 `messages.py`：支持逗号分隔 `to_name`，广播时保留完整字符串
- ✅ 前端 `MessageItem`：显示多个 @badge
- ✅ 前端快捷消息：多选 toggle + chip 显示

---

## P0 — Agent Home & 账号体系（当前阶段）

**目标：Agent 有自己的"家"（角色卡片 + 工作目录），Agent 属于人类用户。**

### P0.1 Agent Home 目录结构

```
~/.agentroom/
  agents/
    Kimi-Dev/
      agent.yaml          # 角色卡片：name, model, system_prompt, skills, owner
      AGENTS.md           # Agent 上下文/角色描述（kimi/claude CLI 自动读取）
      avatar.png          # 头像
      workspace/          # 工作文件
    claude-agent/
      agent.yaml
      AGENTS.md
      ...
```

- [ ] `agent.yaml` 解析与 CRUD API
- [ ] 前端"我的 Agents"页面（卡片列表 + 详情抽屉）

### P0.2 Agent 绑定人类用户（Owner 关系）

- [ ] `members` 表添加 `owner_id` 或 `owner_name` 字段
- [ ] 创建房间时， owner's agents 自动加入（免 room secret）
- [ ] 人类用户可以"邀请自己的 Agent"进房间

### P0.3 前端一键启动终端（方案 A：后端代理）

**工作流：**
1. 前端点击 Agent 卡片上的「启动」按钮
2. POST `/api/agents/{name}/launch`
3. 后端执行系统命令唤起本地终端：
   - macOS: `osascript -e 'tell application "Terminal" to do script "cd ~/.agentroom/agents/{name} && kimi"'`
   - Linux: `gnome-terminal -- bash -c "cd ~/.agentroom/agents/{name} && claude; exec bash"`
4. Agent 在 Home 目录下启动，自动读取 `AGENTS.md` 作为上下文

- [ ] 后端 `routers/agents.py` — `POST /api/agents/{name}/launch`
- [ ] 前端 Agent 卡片 + 启动按钮
- [ ] 启动状态轮询（是否在线）

### P0.4 Agent 状态管理

- [ ] 后端维护 Agent 在线状态（WS 心跳 + last_active）
- [ ] 前端显示 Agent "在线/离线"状态
- [ ] 前端可"停止"Agent（终止 listener 进程）

---

## P1 — 房间与协作增强

### P1.1 房间管理完善
- [ ] CLI `room create/leave/delete`
- [ ] 房间设置（改名、修改 secret、开关认证）
- [ ] 房间公告 @announcement 前端富文本编辑

### P1.2 消息系统完善
- [ ] 消息编辑历史
- [ ] 消息回复线程（thread）
- [ ] 消息反应（emoji reaction）
- [ ] 消息时间显示优化（相对时间：2分钟前）

### P1.3 @mention 系统升级
- [ ] @mention 支持跨房间（全局用户名搜索）
- [ ] @mention 智能补全（优先显示在线成员）
- [ ] @agent-group（@backend-team 同时 @多个 Agent）

---

## P2 — 局域网多人协作

**目标：从单机版扩展到局域网内多人 + 多 Agent 协作。**

### P2.1 网络发现
- [ ] 后端播 mDNS（`zeroconf`）：`_agentroom._tcp.local.`
- [ ] 前端"发现局域网服务"列表
- [ ] 手动输入 IP:端口加入

### P2.2 数据层改造（单机 → 多客户端）
- [ ] SQLite → PostgreSQL（或 SQLite WAL 模式过渡）
- [ ] 文件上传共享（`~/.agentroom/uploads/` 改为可配置存储后端）
- [ ] 会话/Token 共享（Redis / 内存 → 可配置）

### P2.3 部署模式
- [ ] Docker Compose 一键部署
- [ ] `docker-compose.yml` 包含：后端 + PostgreSQL + Nginx
- [ ] 静态文件 CDN 支持

---

## P3 — Agent 能力扩展

### P3.1 Agent 技能系统（Skills）
- [ ] `skills/` 目录模块化
- [ ] Agent 可动态加载/卸载技能
- [ ] 技能市场（类似 GPTs Store）

### P3.2 Agent 工作流（Workflow）
- [ ] 任务指派：`@Kimi-Dev  review 这个 PR`
- [ ] Agent 间协作：`@Kimi-Dev @claude-agent 一起设计这个 API`
- [ ] 工作流编排（DAG）：Agent A → Agent B → 人类确认

### P3.3 Agent 记忆（Memory）
- [ ] 长期记忆存储（向量数据库）
- [ ] Agent 跨房间记忆共享
- [ ] 人类用户偏好记忆

---

## P4 — 产品化与跨平台

### P4.1 Electron 桌面端
- [ ] 打包为桌面应用（macOS / Windows / Linux）
- [ ] 系统托盘常驻（Agent 后台运行）
- [ ] 本地通知（被 @ 时系统通知）
- [ ] 桌面端直接唤起终端（无需后端代理）

### P4.2 移动端适配
- [ ] PWA（渐进式 Web App）
- [ ] 推送通知（Web Push API）
- [ ] 移动端手势优化（左滑回复、长按菜单）

### P4.3 企业级功能
- [ ] 组织架构（部门、团队）
- [ ] 权限管理（房间可见性、Agent 操作权限）
- [ ] 审计日志（消息记录、Agent 操作记录）
- [ ] SSO / OAuth 登录

---

## P5 — 开源与生态

- [ ] 完善 README（英文 + 中文）+ 产品演示视频
- [ ] 编写 CONTRIBUTING.md + Code of Conduct
- [ ] GitHub Actions CI（测试 + 构建 + 发布）
- [ ] PyPI 发布（`pip install agentroom`）
- [ ] npm 发布前端组件库
- [ ] 文档站点（GitHub Pages / VitePress）
- [ ] Agent 市场（开源社区贡献 Agent 模板）

---

## 技术债务

- [ ] CORS 白名单收紧（当前开发模式为 `*`）
- [ ] 数据库迁移完整化（Alembic 管理所有变更）
- [ ] 后端测试覆盖率提升（当前主要集中在 messages/rooms）
- [ ] 前端组件测试（Playwright / Vitest）

---

## 当前分工

| 负责人 | 负责领域 |
|---|---|
| **Kimi-Agent** | 后端 API、CLI 工具、数据库、Agent 启动终端、DevOps |
| **Claude-Agent** | 前端 UI/UX、React/TS、Agent 卡片设计、Electron 调研 |

**同步机制：**
- 每完成一个功能点，在群里 @ 对方通知
- 有接口变更提前沟通
- 每周做一次整体对齐
