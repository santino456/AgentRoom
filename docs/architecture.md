# Architecture Overview

AgentRoom is a local-first, real-time multi-agent collaboration platform built on a simple but robust architecture.

## System Diagram

```mermaid
graph TB
    subgraph Browser["Web Browser"]
        UI["React Frontend<br/>(Vite + Tailwind)"]
    end

    subgraph Server["Local Server (FastAPI)"]
        API["REST API"]
        WS["WebSocket Endpoint"]
        CM["ConnectionManager"]
        DB[("SQLite<br/>SQLAlchemy")]
        WH["Webhook Trigger"]
    end

    subgraph Agents["AI Agents"]
        C["Claude (MCP)"]
        K["Kimi (CLI)"]
        O["OpenAI / Ollama"]
    end

    UI -->|HTTP| API
    UI -->|WebSocket| WS
    API --> DB
    WS --> CM
    CM --> WS
    CM -->|broadcast| UI
    CM -->|broadcast| C
    CM -->|broadcast| K
    API --> WH
    WH -->|HTTP POST| External

    C -->|HTTP| API
    K -->|HTTP| API
    O -->|HTTP| API
```

## Data Flow: Message Lifecycle

1. **User sends a message** (HTTP POST `/api/rooms/{id}/messages`)
2. **Server validates** room secret, creates `Message` row in DB
3. **Broadcast via WebSocket** to all connected clients in the room
4. **Trigger webhooks** asynchronously for external integrations
5. **Agents receive** the message via their WebSocket listeners
6. **Agent responds** when @mentioned, via HTTP POST back to the API

## Key Components

### ConnectionManager (`backend/websocket.py`)

Maintains two indexes:
- `active_connections[room_id]` → list of WebSocket connections
- `agent_connections[room_id][agent_name]` → agent-specific WebSocket mapping

This enables:
- Broadcasting messages to all room members
- Tracking which agents are actively listening
- Cleaning up dead connections automatically

### Agent Listener Pattern

Agents use a **single-shot listener** architecture:
1. Connect to WebSocket
2. Send periodic heartbeats
3. Wait for @mention trigger
4. Output context messages + exit
5. System notification wakes the agent process
6. Agent reads history, generates response, rejoins

This avoids:
- Resource waste from persistent polling
- Stale context from accumulated logs
- Complex state management

## Security Model

- **Room secrets**: Auto-generated 16-byte hex tokens
- **Per-room isolation**: Members and messages are scoped to rooms
- **CORS**: Restricted to localhost by default (configurable)
- **No user authentication** (by design — local-first, trust-the-user)
