# AgentRoom — Project Progress

> Last updated: 2026-05-25

## Phase 1: Foundation (Completed)

| Item | Status | Commit |
|------|--------|--------|
| Git repository initialized | Done | 2e73d24 |
| Backend testing framework (pytest) | Done | 2e73d24 |
| Frontend testing framework (vitest) | Done | 2e73d24 |
| Fix hardcoded API URLs | Done | 2e73d24 |
| Internationalization docs (EN/ZH) | Done | 2e73d24 |
| CI/CD enhancement (pytest + vitest + lint) | Done | 2e73d24 |
| Makefile (dev/test/lint/format) | Done | 2e73d24 |
| CONTRIBUTING.md + templates | Done | 2e73d24 |

**Tests:** Backend 13/13 passing, Frontend 7/7 passing.

## Phase 2: Architecture Split (Completed)

| Item | Status | Commit |
|------|--------|--------|
| Backend route modularization (9 routers) | Done | 4054cae |
| Pydantic schemas extracted | Done | 4054cae |
| Shared services extracted | Done | 4054cae |
| Frontend component decomposition | Done | 4054cae |
| ErrorBoundary | Done | 4054cae |
| AbortController request cancellation | Done | 4054cae |

**Metrics:** `main.py` 660 lines -> ~60 lines. `App.tsx` 762 lines -> ~250 lines.

## Phase 3: Security & Stability (Completed)

| Item | Status | Commit |
|------|--------|--------|
| CORS hardening (configured origins) | Done | 0fc999e |
| Input length limits (Pydantic Field) | Done | 0fc999e |
| Rate limiting (memory sliding-window) | Done | 0fc999e |
| Frontend virtual scrolling | Done | Kimi-Agent |
| X-Member-Token header auth | Done | Kimi-Agent |
| Per-agent config files (token isolation) | Done | Kimi-Agent |
| Image URL encoding (spaces in filenames) | Done | Kimi-Agent |
| Markdown rendering fixes (spacing, lists) | Done | Kimi-Agent + Claude-Agent |
| CLI newline fix (`\n` -> real newline) | Done | Claude-Agent |
| Old message data migration (30 msgs) | Done | Kimi-Agent |

**Tests:** Backend 16/16 passing.

## Phase 4: UI/UX Polish (Completed)

| Item | Status | Commit |
|------|--------|--------|
| 6-theme system (Midnight/Dawn/Ocean/Sunset/Forest/Cyber) | Done | Kimi-Agent |
| Theme selector dropdown | Done | Kimi-Agent |
| Collapsible search bar | Done | Kimi-Agent |
| Join room flow (name + secret) | Done | Kimi-Agent |
| Human online status removed (Agent only) | Done | Claude-Agent |
| Sidebar layout optimization | Done | Claude-Agent |
| Auto-resize textarea input | Done | Claude-Agent |
| Remove focus-visible outline (Apple style) | Done | Claude-Agent |
| Room announcement display | Done | Claude-Agent |
| Agent detail panel (role/description/stats) | Done | Claude-Agent |
| Agent role tags in MemberList | Done | Claude-Agent |

## Phase 5: Feature Expansion (Completed)

| Item | Status | Commit |
|------|--------|--------|
| Agent adapter plugin system | Done | Kimi-Dev |
| Message search backend (FTS5) | Done | Kimi-Dev |
| File attachments | Done | Kimi-Agent |
| Threaded replies | Pending | |
| Agent persona (description + role) | Done | Kimi-Agent + Claude-Agent |
| Member stats API (msg count, last active) | Done | Kimi-Agent |
| Room announcement API | Done | Kimi-Agent |
| CLI `describe` command | Done | Kimi-Agent |
| Remove `display_name` design (backend + frontend + CLI + docs) | Done | Kimi-Dev |
| Fix 500 error after member deletion (dangling FK) | Done | Kimi-Dev |
| CLI `describe`/`remove` name-matching fix (token no longer returned) | Done | Kimi-Dev |
| `kimi_bridge.py` API format fix (`sender_name`) | Done | Kimi-Dev |
| SKILL.md `members rename` removal | Done | Kimi-Dev |
| Full codebase review (3 bugs fixed, 5 issues identified) | Done | Kimi-Dev |

## Phase 6: v0.3 Infrastructure Overhaul (Completed — 2026-05-25)

| Item | Status | Commit |
|------|--------|--------|
| Unified config system (YAML + env vars) | Done | Kimi-Dev |
| CLI `server start` command | Done | Kimi-Dev |
| CLI `config init/show` commands | Done | Kimi-Dev |
| WebSocket authentication (token required) | Done | Kimi-Dev |
| Bearer token support (`Authorization: Bearer`) | Done | Kimi-Dev |
| Frontend onboarding flow (WelcomeScreen) | Done | Kimi-Dev |
| Zustand store foundation | Done | Kimi-Dev |
| README rewrite (remove MCP/adapters, add config docs) | Done | Kimi-Dev |
| Fix datetime JSON serialization bug | Done | Kimi-Dev |
| Fix Chinese name cookie encoding bug | Done | Kimi-Dev |
| Fix listener double-exit race condition | Done | Kimi-Dev |
| CORS dev mode auto-widen | Done | Kimi-Dev |
| Port alignment (all to 8080) | Done | Kimi-Dev |
| PyPI release workflow (Trusted Publisher) | Done | Kimi-Dev |

**Tests:** Backend 22/22 passing, Frontend 14/14 passing. Ruff 0 errors.

## Phase 7: Production Readiness (Pending)

| Item | Status |
|------|--------|
| JWT authentication + API keys | Pending |
| PostgreSQL support | Pending |
| Monitoring / Prometheus metrics | Pending |
| One-click deploy (Railway/Fly.io) | Pending |
| App.tsx Zustand full migration | Pending |
| Test coverage: backend 40+, frontend 30+ | Pending |
| Message soft delete | Pending |

## Technical Debt

| Item | Priority | Status | Notes |
|------|----------|--------|-------|
| WebSocket authentication | High | ✅ Done | Token validation on WS handshake implemented |
| Message sender verification | High | ✅ Done | `update_message`/`delete_message` now verify sender |
| Unified configuration system | High | ✅ Done | YAML + env var based config |
| Webhook auth | Medium | ✅ Done | All webhook endpoints now require member auth |
| Agent token isolation | High | Pending | Current dev mode trusts all agents on same machine. Need container-level isolation or encrypted token storage before production. |
| Room creation unauthenticated | Medium | Pending | `create_room` allows anyone to create rooms without auth. |
| Dangling foreign keys on member deletion | Medium | Partial | Null-guard added in `_message_to_dict`, but root cause not fixed. |
| Room cascade delete risk | Medium | Pending | `Room.members` has `cascade="all, delete-orphan"`. Could cause unexpected cascading behavior. |
| Chunk size warning | Low | Pending | Frontend JS bundle ~1MB, could benefit from code splitting. |
| Backend stability | Medium | Pending | Service experienced restart loops (WS 1012). Root cause investigation pending. |
| Theme background depth | Low | Pending | User requested richer thematic visuals (SVG patterns/image assets). |
| Message scroll flickering | Low | Pending | Partially mitigated, may need further virtualizer tuning. |

## Current Team

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Kimi-Dev** | Backend Dev + CLI + Review + Coordination | Backend APIs, CLI tools, code review, bug fixes, multi-agent coordination |
| **claude-agent** | Frontend Dev | React/TS UI, component design, UX polish |
| **金角大王** | PM / Human | Product decisions, testing, feedback |

## 同步机制
- 每完成一个功能点，在群里 @ 对方通知
- 有接口变更提前沟通
- 每日站会（通过平台消息）
