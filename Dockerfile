# Agent Coop — Docker 部署
# 构建命令: docker build -t agent-coop .
# 运行命令: docker run -p 8080:8080 agent-coop

# ===== 前端构建阶段 =====
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ===== 后端运行阶段 =====
FROM python:3.13-slim
WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制依赖
COPY requirements.txt ./
RUN uv venv && uv pip install -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/
COPY cli/ ./cli/
COPY config/ ./config/
COPY adapters/ ./adapters/
COPY scripts/ ./scripts/
COPY Makefile ./

# 复制前端构建产物
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["./.venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
