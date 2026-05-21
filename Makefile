.PHONY: dev install backend frontend build clean

# 一键启动整个应用（后端 + 前端已构建）
dev:
	@echo "🚀 启动 Agent Coop..."
	@cd backend && ../.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8080 --reload

# 安装后端依赖
install:
	@echo "📦 安装后端依赖..."
	@uv venv && uv pip install -r requirements.txt
	@echo "📦 安装前端依赖..."
	@cd frontend && npm install

# 构建前端
build:
	@echo "🏗️ 构建前端..."
	@cd frontend && npm run build

# 清理（⚠️ 会删除数据库！需要确认）
clean:
	@echo "⚠️ 这将删除：frontend/dist, .venv, ~/.agent-coop（数据库）"
	@read -p "确定继续? [y/N] " confirm && [ "$$confirm" = "y" ] || (echo "已取消" && exit 1)
	@rm -rf frontend/dist .venv ~/.agent-coop

# 测试后端 API
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
