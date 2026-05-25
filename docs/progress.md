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

## Phase 5: Feature Expansion (In Progress)

| Item | Status | Commit |
|------|--------|--------|
| Agent adapter plugin system | Done | Kimi-Dev |
| Message search backend (FTS5) | Pending | |
| File attachments | Partial | Kimi-Agent |
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

## Phase 6: Production Readiness (Pending)

| Item | Status |
|------|--------|
| JWT authentication + API keys | Pending |
| PostgreSQL support | Pending |
| Monitoring / Prometheus metrics | Pending |
| One-click deploy (Railway/Fly.io) | Pending |

## Technical Debt

| Item | Priority | Notes |
|------|----------|-------|
| Agent token isolation | High | Current dev mode trusts all agents on same machine. Need container-level isolation or encrypted token storage before production. |
| WebSocket authentication | High | Anyone can connect to any room's WebSocket without auth. Must add token validation on WS handshake. |
| Message sender verification | High | `delete_message` and `update_message` do not verify the sender identity. Anyone can delete/edit any message. |
| Room creation unauthenticated | Medium | `create_room` allows anyone to create rooms without auth. |
| Dangling foreign keys on member deletion | Medium | Deleting a member leaves `sender_id` / `to_member_id` FKs in messages pointing to non-existent members. Added null-guard in `_message_to_dict`, but root cause not fixed. |
| Room cascade delete risk | Medium | `Room.members` has `cascade="all, delete-orphan"`. Could cause unexpected cascading behavior. |
| Chunk size warning | Low | Frontend JS bundle ~1MB, could benefit from code splitting. |
| Backend stability | Medium | Service experienced restart loops (WS 1012). Root cause investigation pending. |
| Theme background depth | Low | User requested richer thematic visuals (SVG patterns/image assets). |
| Message scroll flickering | Low | Partially mitigated, may need further virtualizer tuning. |

## Current Team

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Kimi-Dev** | Backend Dev + CLI + Review | Backend APIs, CLI tools, code review, bug fixes, multi-agent coordination |
| **Kimi-Agent** | Backend Dev + CLI (legacy) | Original backend/CLI implementation |
| **Claude-Agent** | Frontend Dev | React/TS UI, component design, UX polish |
| **claude-军师** | Architect | Architecture design, tech choices, code review (read-only) |
| **金角大王** | PM / Human | Product decisions, testing, feedback |

## 同步机制
- 每完成一个功能点，在群里 @ 对方通知
- 有接口变更提前沟通
- 每日站会（通过平台消息）
