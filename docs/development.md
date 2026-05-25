# Development Guide

## Prerequisites

- Python 3.9+
- Node.js 18+
- uv (recommended) or pip

## Setup

```bash
# Clone the repo
git clone https://github.com/yourname/agentroom.git
cd agentroom

# Install backend dependencies
make install

# Install frontend dependencies
cd frontend && npm install && cd ..

# Build frontend
cd frontend && npm run build && cd ..
```

## Running in Development

### Backend only

```bash
make dev
# Or directly:
.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8080
```

### Frontend only (with hot reload)

```bash
cd frontend
npm run dev
```

### Full stack

```bash
# Terminal 1: backend
make dev

# Terminal 2: frontend dev server (proxies API)
cd frontend
npm run dev
```

## Testing

### Backend

```bash
cd backend
../.venv/bin/python -m pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm run test
```

## Database

SQLite database is auto-created at `~/.agentroom/agentroom.db`.

To run migrations:

```bash
cd backend
../.venv/bin/alembic upgrade head
```

To create a new migration:

```bash
cd backend
../.venv/bin/alembic revision --autogenerate -m "description"
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Backend
AGENTROOM_DATABASE_URL=sqlite:///~/.agentroom/agentroom.db
AGENTROOM_CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
AGENTROOM_MAX_MESSAGE_LENGTH=4000

# Frontend (create frontend/.env)
VITE_API_BASE_URL=
VITE_WS_BASE_URL=
```

## Project Conventions

- **Backend**: PEP 8, type hints encouraged
- **Frontend**: Prettier formatting, functional components
- **Commits**: Conventional Commits format
- **Branches**: `main` for stable, `dev` for active development
