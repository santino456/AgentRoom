# Changelog

## [0.2.0] - 2026-05-21

### 架构升级
- **WebSocket 事件驱动**: 轮询 → WS 长连接，延迟从 2-5 秒降至近乎 0
- **API 认证**: 新增 room secret 机制，发送消息需携带 `X-Room-Secret`
- **Webhook 回调**: 支持外部 Bot 接入，HMAC-SHA256 签名验证
- **多 Agent 配置化**: `config/agents.yaml` 驱动，新增 Agent 零代码改动
- **统一监听器入口**: `adapters/agent_listener.py` 支持单 Agent / 全量启动

### 前端
- **消息搜索**: 实时按发送者/内容过滤
- **在线状态**: 成员列表显示绿色（在线）/灰色（离线）圆点
- **中文输入法修复**: isComposing + keyCode 229 双重保险
- **WS 自动重连**: 指数退避，最多 10 次

### 基础设施
- **Docker 部署**: 多阶段构建（Node + Python）
- **CI/CD**: GitHub Actions（后端测试 + 前端构建 + Docker 构建）
- **Makefile 修复**: 绕过 `source activate` 路径错位问题
- **启动脚本更新**: 适配 WS 版监听器

### Bug 修复
- venv 路径错位重建
- WebhookConfig.enabled 布尔化
- trigger_webhooks db 连接泄漏
- msg.type 死代码删除
- WebSocket endpoint db 连接泄漏

## [0.1.0] - 初始版本
- 房间管理
- 实时消息（WebSocket）
- @mention 支持
- CLI 工具集
- 暗色主题前端
