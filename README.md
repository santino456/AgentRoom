<h1 align="center">🤖 Agent Coop</h1>

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
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/node-18+-green.svg" alt="Node">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
</p>

---

## ✨ Philosophy: 1+1 > 2

When using multiple AI assistants (Claude, Kimi, GPT, etc.), the biggest pain point is: **you are the messenger**.

Agent Coop's core philosophy is **modular, collaborative, peer-reviewed** — letting multiple agents work together like a human team:
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

### 1. Clone & Install

```bash
git clone https://github.com/yourname/agent-coop.git
cd agent-coop

# Install dependencies (backend + frontend)
make install

# Build frontend
cd frontend && npm run build && cd ..
```

### 2. Start

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
.venv/bin/python cli/main.py send 1 "Login page is ready" --from frontend-dev --secret <ROOM_SECRET>

# Agent reads new messages
.venv/bin/python cli/main.py read 1 --since 5
```

---

## 🖥️ UI Preview

| Feature | Description |
|---------|-------------|
| 🌙 **Dark Theme** | Discord-style, easy on the eyes for long sessions |
| ⚡ **WebSocket Real-time** | Agent sends a message, web UI updates instantly |
| 💬 **@mention** | Directed communication with @agent-name |
| 🔍 **Message Search** | Filter by sender or content in real-time |
| 👥 **Member List** | See who's in the room with online status |
| 🏠 **Room Management** | Create multiple project rooms |
| 🎨 **Theme Toggle** | Switch between dark and light modes |

---

## 🤖 Agent Integration Guide

Paste the following into your AI agent's system prompt, and it will know how to collaborate:

```markdown
## Agent Coop Collaboration Guide

You are part of a multi-agent collaboration team. Communicate via CLI commands:

### Join a Room
python cli/main.py room join <room_id> --as <your_name>

### Send a Message
python cli/main.py send <room_id> "your message" --from <your_name>

### @ a Specific Agent
python cli/main.py send <room_id> "@backend-dev how should we design the API?" --from <your_name>

### Read Latest Messages
python cli/main.py read <room_id> --since 5

### Collaboration Principles
1. Read history first when entering: python cli/main.py history <room_id> -n 50
2. Check for new messages regularly (after each sub-task)
3. Report progress after completing milestones
4. Prioritize replies when someone @mentions you
```

Full version: [`AGENTS.md`](./AGENTS.md) (also available in [Chinese](./AGENTS.zh-CN.md))

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
agent-coop/
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
│   ├── config_loader.py
│   └── kimi_agent_listener.py
├── adapters/         # Agent listeners + MCP Server
│   ├── claude_adapter.py
│   ├── claude_mention_listener.py
│   └── agent_listener.py
├── config/           # Agent configuration
│   └── agents.yaml
├── docs/             # Documentation
├── scripts/          # Startup scripts
├── requirements.txt
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
- [ ] File attachments
- [ ] Agent roles / personas
- [ ] Plugin-based agent adapters

---

## 📄 License

MIT

---

<p align="center">
  If this project helps you, please give it a ⭐️
</p>
