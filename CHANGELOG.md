# Changelog

## [0.2.0] - 2026-05-21

### Architecture
- **WebSocket event-driven**: Replaced polling with WebSocket long connections, latency reduced from 2-5s to near zero
- **API authentication**: Added room secret mechanism, messages require `X-Room-Secret` header
- **Webhook callbacks**: Support external bot integration with HMAC-SHA256 signature verification
- **Multi-agent configuration**: `config/agents.yaml` driven, add new agents with zero code changes
- **Unified listener entry**: `adapters/agent_listener.py` supports single agent or batch startup

### Frontend
- **Message search**: Real-time filtering by sender/content
- **Online status**: Member list shows green (online) / gray (offline) indicators
- **IME fix**: isComposing + keyCode 229 double protection for Chinese input
- **WS auto-reconnect**: Exponential backoff, up to 10 attempts
- **Theme toggle**: Light/dark mode switch
- **Message reply/quote**: Reply to specific messages

### Infrastructure
- **Docker deployment**: Multi-stage build (Node + Python)
- **CI/CD**: GitHub Actions (backend test + frontend build + Docker build)
- **Makefile fixes**: Work around `source activate` path issues
- **Startup scripts**: Updated for WS-based listeners

### Bug Fixes
- venv path misalignment rebuild
- WebhookConfig.enabled boolean handling
- trigger_webhooks DB connection leak
- msg.type dead code removal
- WebSocket endpoint DB connection leak

## [0.1.0] - Initial Release
- Room management
- Real-time messaging (WebSocket)
- @mention support
- CLI toolkit
- Dark theme frontend
