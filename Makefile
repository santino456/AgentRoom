.PHONY: dev dev-backend dev-frontend install backend frontend build test lint format clean

# Start backend only (with auto-reload)
dev-backend:
	@echo "🚀 Starting backend..."
	@cd backend && ../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8080 --reload

# Start frontend only (with hot reload, separate terminal)
dev-frontend:
	@echo "🚀 Starting frontend dev server..."
	@cd frontend && npm run dev

# Start full app (backend serves built frontend)
dev:
	@echo "🚀 Starting Agent Coop..."
	@cd backend && ../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8080 --reload

# Install dependencies
install:
	@echo "📦 Installing backend dependencies..."
	@uv venv && uv pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install

# Build frontend
build:
	@echo "🏗️ Building frontend..."
	@cd frontend && npm run build

# Run all tests
test:
	@echo "🧪 Running backend tests..."
	@cd backend && ../.venv/bin/python -m pytest tests/ -v
	@echo "🧪 Running frontend tests..."
	@cd frontend && npx vitest run

# Run linters
lint:
	@echo "🔍 Running backend linter..."
	@cd backend && ../.venv/bin/ruff check .
	@echo "🔍 Running frontend linter..."
	@cd frontend && npx prettier --check "src/**/*.{ts,tsx,css}"

# Auto-format code
format:
	@echo "✨ Formatting backend..."
	@cd backend && ../.venv/bin/ruff format .
	@echo "✨ Formatting frontend..."
	@cd frontend && npx prettier --write "src/**/*.{ts,tsx,css}"

# Clean (⚠️ deletes database!)
clean:
	@echo "⚠️ This will delete: frontend/dist, .venv, ~/.agent-coop (database)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "Cancelled" && exit 1)
	@rm -rf frontend/dist .venv ~/.agent-coop

# Test backend API
ping:
	@curl -s http://127.0.0.1:8080/api/health | python3 -m json.tool

# ============ Agent 监听器 ============

agent: ## 启动 Kimi-Agent 事件驱动监听器
	@bash scripts/start-kimi-agent.sh

agent-room: ## 启动监听器并指定房间 (用法: make agent-room ROOM=2)
	@bash scripts/start-kimi-agent.sh $(ROOM) 2

agent-forever: ## 循环启动监听器（自动重启）
	@bash scripts/start-kimi-agent-loop.sh

agent-stop: ## 停止所有 Kimi-Agent 监听器
	@pkill -f "kimi_agent_listener.py" 2>/dev/null && echo "✅ 监听器已停止" || echo "没有运行中的监听器"
