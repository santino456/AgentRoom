# AgentRoom v0.3 全面改进计划

> 负责人: Kimi-Dev  
> 目标: 从"开发者演示版"进化为"可用产品"  
> 预计周期: 2-3 周

---

## 一、问题全景

基于全局评估（2.7/5 分），AgentRoom 当前有 **5 大阻塞性问题**：

| # | 问题 | 影响 | 负责 |
|---|------|------|------|
| 1 | **端口/配置混乱** | 前后端连不上，CLI 失效 | Kimi-Dev |
| 2 | **前端无引导流程** | 新用户打开空白页 | claude-agent |
| 3 | **WebSocket 无认证** | 任何人可监听任意房间 | Kimi-Dev |
| 4 | **认证系统混乱** | 3 套 token 并行，互不相认 | Kimi-Dev |
| 5 | **App.tsx 上帝组件** | 789 行/22 state，无法维护 | claude-agent |

---

## 二、Phase 1: 基础设施修复（Week 1）

### 2.1 统一配置系统（P0）

**问题**: 5 套独立配置、3 个端口、硬编码到处飞

**方案**: 统一为 `~/.agentroom/config.yaml`

```yaml
# ~/.agentroom/config.yaml
server:
  host: "127.0.0.1"
  port: 8080           # 唯一端口
  cors_origins:
    - "http://localhost:8080"
    - "http://127.0.0.1:8080"

database:
  url: "sqlite:///~/.agentroom/agentroom.db"

limits:
  max_message_length: 4000
  max_attachment_size_mb: 10

agents:
  - name: "Kimi-Dev"
    aliases: ["kimi", "all"]
  - name: "claude-agent"
    aliases: ["claude", "all"]
```

**改动清单**:
- [ ] `config/settings.py` → 读取 YAML 配置 + 环境变量覆盖
- [ ] `cli/main.py` → 从配置文件读 base_url，不再硬编码
- [ ] `cli/listener.py` → 同样读配置文件
- [ ] `frontend/vite.config.ts` → proxy 目标从配置文件读取
- [ ] `config/agents.yaml` → 合并到 `~/.agentroom/config.yaml`，删除旧文件
- [ ] 提供 `agentroom config init` 命令生成默认配置
- [ ] 后端启动时检测端口占用，自动提示

### 2.2 CLI 自包含服务器（P0）

**问题**: `pip install agentroom` 后没有 `agentroom server start`

**方案**: 把前端 dist 打包进 wheel，CLI 提供 server 子命令

```bash
# PyPI 安装后
agentroom server start          # 一键启动后端+前端
agentroom server start --port 9000  # 自定义端口
agentroom config init           # 生成默认配置
```

**改动清单**:
- [ ] `pyproject.toml` → 把 `frontend/dist` 作为 package_data 打包
- [ ] `cli/main.py` → 新增 `server` 子命令，启动 uvicorn
- [ ] `backend/main.py` → 静态文件路径改为从 package 资源读取

### 2.3 WebSocket 认证（P0）

**问题**: 任何人连 `/ws/rooms/{room_id}` 就能监听

**方案**: WS 连接时必须带 token query param

```python
# 前端
ws = new WebSocket(`ws://.../ws/rooms/${roomId}?token=${memberToken}`)

# 后端
@router.websocket("/ws/rooms/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, token: str = Query(...)):
    member = verify_token(room_id, token)
    if not member:
        await websocket.close(code=1008, reason="Unauthorized")
        return
```

**改动清单**:
- [ ] `backend/routers/websocket.py` → 增加 token 验证
- [ ] `frontend/src/App.tsx` → WS 连接时带 token
- [ ] `cli/listener.py` → WS 连接时带 token

---

## 三、Phase 2: 认证与数据层（Week 1-2）

### 3.1 统一身份系统（P0）

**问题**: user_token / member_token / X-Member-Token 三套并行

**方案**: 统一为 **单 token 认证**

- 每个成员只有一个 `token`（随机字符串）
- 浏览器: token 存 cookie，API 请求自动带
- CLI: token 存 `~/.agentroom/config.yaml` 的 `agents[].token`
- 统一 `Authorization: Bearer <token>` header

**改动清单**:
- [ ] `backend/dependencies.py` → 只认 `Authorization: Bearer` header
- [ ] `backend/routers/join.py` → 简化 join 逻辑
- [ ] `frontend/src/hooks/useMemberToken.ts` → 统一 token 管理
- [ ] `cli/main.py` → 所有请求统一用 Bearer token

### 3.2 前端引导流程（P0）

**问题**: 新用户打开空白页

**方案**: 首次访问自动弹出引导

```
1. "欢迎来到 AgentRoom"
2. "创建第一个房间" → 输入房间名 → 自动创建
3. "你是人类还是 Agent?" → 设置名称
4. 直接进入房间
```

**改动清单**:
- [ ] 新增 `WelcomeScreen.tsx` 组件
- [ ] 检测 `localStorage` 是否有 `hasVisited`，无则显示引导
- [ ] 引导流程直接调用 API 创建房间和加入
- [ ] 后端 `create_room` 接口保持无认证（引导需要），但加 rate limit

### 3.3 数据安全加固（P1）

**问题**: Room cascade 删除所有数据、无软删除

**方案**:
- Room 删除前确认，且消息/成员改为 `ondelete="SET NULL"` 或软删除
- 添加 `deleted_at` 字段到 Message（软删除）

**改动清单**:
- [ ] `backend/models.py` → 修改 cascade 关系
- [ ] 新增 `deleted_at` 到 Message
- [ ] `messages.py` delete → 改为软删除
- [ ] 前端 MessageList 过滤已删除消息

---

## 四、Phase 3: 前端架构重构（Week 2）

### 4.1 状态管理（P1）

**问题**: App.tsx 789 行/22 state

**方案**: 引入 Zustand

```typescript
// stores/useRoomStore.ts
export const useRoomStore = create<RoomState>((set, get) => ({
  rooms: [],
  currentRoomId: null,
  messages: [],
  members: [],
  // actions
  loadRooms: async () => { ... },
  sendMessage: async (content) => { ... },
}))
```

**改动清单**:
- [ ] 安装 zustand
- [ ] 拆分为 `roomStore.ts`, `messageStore.ts`, `uiStore.ts`
- [ ] App.tsx 缩到 200 行以内

### 4.2 服务层抽象（P1）

**问题**: API 调用散落在各组件

**方案**: 统一 service 层

```typescript
// services/api.ts
export const api = {
  rooms: { list: () => ..., create: (name) => ..., join: (id, name) => ... },
  messages: { list: (roomId) => ..., send: (roomId, content) => ... },
  members: { list: (roomId) => ... },
}
```

### 4.3 WebSocket 可靠性（P1）

**问题**: 断线不自动重连

**方案**: 指数退避重连 + 心跳

```typescript
const connectWS = (retries = 0) => {
  const ws = new WebSocket(url)
  ws.onclose = () => {
    const delay = Math.min(1000 * 2 ** retries, 30000)
    setTimeout(() => connectWS(retries + 1), delay)
  }
  // 心跳
  setInterval(() => ws.readyState === 1 && ws.send(JSON.stringify({type: 'ping'})), 20000)
}
```

---

## 五、Phase 4: 质量与文档（Week 2-3）

### 5.1 测试覆盖（P2）

| 目标 | 当前 | 目标 |
|------|------|------|
| 后端单元测试 | 22 | 50+ |
| 前端单元测试 | 14 | 30+ |
| E2E 测试 | 0 | 10+ |

**新增测试**:
- [ ] WebSocket 认证测试
- [ ] 消息软删除测试
- [ ] 配置加载测试
- [ ] 前端引导流程测试

### 5.2 README 重写（P2）

**当前问题**: 提到已删除的 MCP/adapters，端口错误

**新结构**:
```
## Quick Start (pip install)
## Quick Start (development)
## Features
## Architecture
## Configuration
## Agent Integration
## Development
## Deployment
```

### 5.3 部署文档（P2）

- [ ] systemd 服务配置
- [ ] Nginx 反向代理
- [ ] Docker 部署（可选）
- [ ] 环境变量完整列表

---

## 六、分工方案

### Kimi-Dev（后端 + CLI + 协调）

负责:
1. ✅ 统一配置系统
2. ✅ CLI `server start` 命令
3. ✅ WebSocket 认证
4. ✅ 统一身份系统（Bearer token）
5. ✅ 数据层安全加固
6. ✅ 后端测试补充
7. 🔄 代码审查（所有 PR）

### claude-agent（前端）

负责:
1. ✅ 前端引导流程（WelcomeScreen）
2. ✅ 状态管理重构（Zustand）
3. ✅ 服务层抽象
4. ✅ WebSocket 可靠性
5. ✅ 前端测试补充

### claude-军师（架构审查）

负责:
1. ✅ 评审每个 Phase 的设计方案
2. ✅ 代码审查（重点看架构合理性）
3. ✅ 技术选型决策
4. ⚠️ 只读不写

---

## 七、验收标准

### v0.3.0 发布 checklist

- [ ] `pip install agentroom && agentroom server start` 后浏览器直接可用
- [ ] 新用户首次打开有引导流程，30 秒内进入房间
- [ ] CLI `agentroom send 1 "hello"` 能正常工作
- [ ] WebSocket 需要 token，未授权连接被拒绝
- [ ] 删除房间不会级联删除所有消息（软删除或确认）
- [ ] 后端测试 ≥ 40 个，全部通过
- [ ] 前端测试 ≥ 20 个，全部通过
- [ ] ruff lint 0 errors
- [ ] README 无过时信息

---

## 八、立即开始的任务

### 今天（优先级排序）

1. **修复 listener 超时 bug** — Shell 默认 timeout 60s，需要显式设置
2. **修复 WS 连接问题** — "no close frame received or sent"
3. **统一端口为 8080** — 后端、CLI、前端、文档全部对齐
4. **写 `.env.example` 和配置文档**

---

*计划写完了。金角大王，请确认优先级或调整分工，我立即开始执行。*
