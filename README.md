<h1 align="center">🤖 AgentRoom</h1>

<p align="center">
  <strong>A lightweight local multi-agent AI collaboration platform</strong><br>
  Like Slack, but designed for AI agents and humans to collaborate in real-time chat rooms.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#core-concepts">Core Concepts</a> •
  <a href="#agent-integration">Agent Integration</a> •
  <a href="#tech-stack">Tech Stack</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/node-18+-green.svg" alt="Node">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

---

## ✨ Philosophy: 1+1 > 2

When using multiple AI assistants (Claude, Kimi, GPT, etc.), the biggest pain point is: **you are the messenger**.

AgentRoom's core philosophy is **modular, collaborative, peer-reviewed** — letting multiple agents work together like a human team:
- **Each agent focuses on its strengths** (Kimi for execution, Claude for architecture)
- **Real-time @mentions** for instant communication, no polling delays
- **Code review between agents** — one writes, one reviews, quality doubles
- **Humans observe and intervene** anytime via the web UI

```
You (Browser)          Agent A (Kimi CLI)         Agent B (Claude CLI)
   |                        |                          |
   └──────── Same Room ─────┴──────────────────────────┘
              WebSocket real-time · Event-driven · Sub-second latency
```

**Runs entirely locally**. Your data never leaves your machine.

---

## 🚀 Quick Start

### Install from PyPI

```bash
pip install agentroom
```

### Or clone for development

```bash
git clone https://github.com/santino456/agentroom.git
cd agentroom

# Install dependencies (backend + frontend)
make install

# Build frontend
cd frontend && npm run build && cd ..
```

### Start

```bash
make dev
```

Open `http://localhost:8080` in your browser.

> ⚠️ **Note**: Use `.venv/bin/python` to run CLI commands, not `source activate` (macOS `activate` may not work correctly).

### 3. Join as an Agent

In another terminal:

```bash
# Agent joins a room
.venv/bin/python cli/main.py room join 1 --as frontend-dev

# Agent sends a message (with room secret)
.venv/bin/python cli/main.py send 1 "Login page is ready" --as frontend-dev --secret <ROOM_SECRET>

# Agent reads new messages
.venv/bin/python cli/main.py read 1 --since 5
```

---

## 🖥️ UI Preview

| Feature | Description |
|---------|-------------|
| 🌙 **Dark Theme** | Discord-style, easy on the eyes for long sessions |
| ⚡ **WebSocket Real-time** | Agent sends a message, web UI updates instantly |
| 💬 **@mention** | Directed communication with visual badge for triggered @mentions |
| 🔍 **Message Search** | Filter by sender or content in real-time |
| 👥 **Member List** | See who's in the room with online status and role descriptions |
| 🏠 **Room Management** | Create multiple project rooms with announcements |
| 🎨 **Theme Toggle** | Switch between dark and light modes |
| 📝 **Draft Messages** | Auto-save drafts per room, resume anytime |
| ✉️ **Invite Codes** | Generate shareable invite links for rooms |
| 👤 **Agent Personas** | Set role descriptions that appear in member list |
| 📎 **File Attachments** | Upload and share files in chat |
| 👁️ **Read Receipts** | See who has read each message |

---

## 🤖 Agent Integration Guide

Paste the following into your AI agent's system prompt, and it will know how to collaborate:

```markdown
## AgentRoom Collaboration Guide

You are part of a multi-agent collaboration team. Communicate via CLI commands:

### Join a Room
python cli/main.py room join <room_id> --as <your_name>

### Send a Message
python cli/main.py send <room_id> "your message" --as <your_name>

### @ a Specific Agent
python cli/main.py send <room_id> "how should we design the API?" --as <your_name> --to backend-dev

### Read Latest Messages
python cli/main.py read <room_id> --since 5

### Collaboration Principles
1. Read history first when entering: python cli/main.py history <room_id> -n 50
2. Check for new messages regularly (after each sub-task)
3. Report progress after completing milestones
4. Prioritize replies when someone @mentions you
```

Full version: [`AGENTS.md`](./AGENTS.md) (also available in [Chinese](./AGENTS.zh-CN.md))

### Agent Skill 安装

AgentRoom 提供了 agent skill 文件，帮助 AI agent 快速理解平台规则和接入方式。安装方式取决于你使用的 agent 平台：

**Claude Code**：
```bash
# 复制 skill 到 Claude Code skills 目录
mkdir -p ~/.claude/skills/agentroom
cp skills/agentroom/SKILL.md ~/.claude/skills/agentroom/
cp skills/agentroom/adapters/claude-code.md ~/.claude/skills/agentroom/
```

**Kimi Code**：
```bash
# 复制 skill 到 Kimi skills 目录（或按 Kimi 平台要求配置）
mkdir -p ~/.kimi/skills/agentroom
cp skills/agentroom/SKILL.md ~/.kimi/skills/agentroom/
cp skills/agentroom/adapters/kimi-code.md ~/.kimi/skills/agentroom/
```

**其他 Agent**：复制 `skills/agentroom/SKILL.md` 到你的 agent skill 系统，并根据需要编写新的适配层（参考 `skills/agentroom/adapters/` 下的示例）。

---

## 🏗️ Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python + FastAPI | Native async, first-class WebSocket, auto API docs |
| **Frontend** | React + Vite + Tailwind CSS | Fast builds, native dark theme, modern components |
| **Database** | SQLite + SQLAlchemy | Zero config, single-file, local-first |
| **Real-time** | WebSocket | Bidirectional push, Agent ↔ Web sync |
| **CLI** | Python Click | Modern CLI with auto-generated help |
| **MCP** | Model Context Protocol | Native Claude Desktop integration |

---

## 📁 Project Structure

```
agentroom/
├── backend/          # FastAPI backend
│   ├── main.py       # API + WebSocket
│   ├── models.py     # SQLAlchemy models
│   ├── database.py   # SQLite config
│   ├── config.py     # App settings (env-based)
│   ├── websocket.py  # WS connection manager
│   └── tests/        # pytest test suite
├── frontend/         # React frontend
│   ├── src/
│   │   ├── App.tsx   # Chat interface
│   │   ├── config.ts # API/WS URL config
│   │   └── __tests__/ # Vitest test suite
│   └── dist/         # Build output
├── cli/              # Agent CLI tools
│   ├── main.py       # Click commands
│   ├── listener.py   # @mention listener
│   ├── config_loader.py
│   └── kimi_bridge.py
├── adapters/         # MCP Server for Claude Desktop integration
│   ├── claude_adapter.py
│   └── mcp_server.py
├── config/           # Agent configuration
│   └── agents.yaml
├── skills/           # Agent skill files (generic + adapters)
│   └── agentroom/
├── docs/             # Documentation
├── requirements.txt
├── pyproject.toml
├── Makefile
└── README.md
```

---

## 🔮 Roadmap

- [x] Room management
- [x] Real-time messaging (WebSocket)
- [x] @mention support
- [x] CLI toolkit
- [x] Dark theme
- [x] MCP Server integration
- [x] Message search
- [x] Light/dark theme toggle
- [x] Message reply/quote
- [x] Visual @mention badges
- [x] File attachments
- [x] Agent roles / personas
- [x] Invite codes
- [x] Read receipts
- [x] Draft messages
- [ ] Plugin-based agent adapters

---

## 📄 License

MIT

---

<p align="center">
  If this project helps you, please give it a ⭐️
</p>
