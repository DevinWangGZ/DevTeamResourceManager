.PHONY: help setup-backend setup-frontend dev-backend dev-frontend dev-frontend-remote test install check \
        start-backend stop-backend restart-backend logs-backend status-backend \
        start-frontend-remote stop-frontend-remote restart-frontend-remote logs-frontend-remote status-frontend-remote

# 后台运行相关配置
BACKEND_PID_FILE := /tmp/devteam_backend.pid
BACKEND_LOG_FILE := logs/backend.log
FRONTEND_REMOTE_PID_FILE := /tmp/devteam_frontend_remote.pid
FRONTEND_REMOTE_LOG_FILE := logs/frontend_remote.log
# 与 dev-frontend-remote 一致；可在命令前覆盖：VITE_API_BASE_URL=http://ip:8000 make start-frontend-remote
VITE_API_BASE_URL ?= http://175.178.182.23:8000

help:
	@echo "可用命令："
	@echo "  make setup-backend        - 设置后端环境"
	@echo "  make setup-frontend       - 设置前端环境"
	@echo "  make dev-backend          - 启动后端开发服务器（前台，关闭SSH即停止）"
	@echo "  make start-backend        - 后台启动后端服务器（SSH断开后继续运行）"
	@echo "  make stop-backend         - 停止后台后端服务器"
	@echo "  make restart-backend      - 重启后台后端服务器"
	@echo "  make logs-backend         - 实时查看后端日志（Ctrl+C退出）"
	@echo "  make status-backend       - 查看后端服务状态"
	@echo "  make dev-frontend         - 启动前端开发服务器（连接本地 localhost:8000）"
	@echo "  make dev-frontend-remote  - 启动前端开发服务器（连接远程后端，前台）"
	@echo "  make start-frontend-remote - 后台启动前端（SSH 断开后继续运行）"
	@echo "  make stop-frontend-remote  - 停止后台前端"
	@echo "  make logs-frontend-remote  - 查看前端后台日志"
	@echo "  make status-frontend-remote - 查看前端后台状态"
	@echo "  make install              - 安装所有依赖"
	@echo "  make check                - 检查服务状态"

setup-backend:
	@echo "设置后端环境..."
	cd backend && pip install -r requirements/dev.txt
	@if [ ! -f backend/.env ]; then \
		echo "创建 .env 文件..."; \
		cp backend/env.example backend/.env 2>/dev/null || echo "请手动创建 backend/.env 文件"; \
	fi

setup-frontend:
	@echo "设置前端环境..."
	cd frontend && npm install
	@if [ ! -f frontend/.env.development ]; then \
		echo "创建 .env.development 文件..."; \
		echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env.development; \
		echo "VITE_APP_TITLE=DevTeam Manager (开发环境)" >> frontend/.env.development; \
	fi

dev-backend:
	@echo "启动后端开发服务器..."
	@echo "API文档: http://localhost:8000/docs"
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-backend:
	@mkdir -p logs
	@if [ -f $(BACKEND_PID_FILE) ] && kill -0 $$(cat $(BACKEND_PID_FILE)) 2>/dev/null; then \
		echo "后端服务已在运行中 (PID: $$(cat $(BACKEND_PID_FILE)))，请先执行 make stop-backend"; \
	else \
		echo "后台启动后端服务器..."; \
		cd backend && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 \
			> ../$(BACKEND_LOG_FILE) 2>&1 & echo $$! > $(BACKEND_PID_FILE); \
		sleep 1; \
		if kill -0 $$(cat $(BACKEND_PID_FILE)) 2>/dev/null; then \
			echo "✓ 后端服务已启动 (PID: $$(cat $(BACKEND_PID_FILE)))"; \
			echo "  API文档: http://localhost:8000/docs"; \
			echo "  日志文件: $(BACKEND_LOG_FILE)"; \
			echo "  查看日志: make logs-backend"; \
		else \
			echo "✗ 启动失败，请查看日志: $(BACKEND_LOG_FILE)"; \
		fi \
	fi

stop-backend:
	@if [ -f $(BACKEND_PID_FILE) ] && kill -0 $$(cat $(BACKEND_PID_FILE)) 2>/dev/null; then \
		echo "停止后端服务 (PID: $$(cat $(BACKEND_PID_FILE)))..."; \
		kill $$(cat $(BACKEND_PID_FILE)); \
		rm -f $(BACKEND_PID_FILE); \
		echo "✓ 后端服务已停止"; \
	else \
		echo "后端服务未在运行"; \
		rm -f $(BACKEND_PID_FILE); \
	fi

restart-backend: stop-backend
	@sleep 1
	@$(MAKE) start-backend

logs-backend:
	@mkdir -p logs
	@echo "实时查看后端日志（Ctrl+C 退出）..."
	@tail -f $(BACKEND_LOG_FILE)

status-backend:
	@if [ -f $(BACKEND_PID_FILE) ] && kill -0 $$(cat $(BACKEND_PID_FILE)) 2>/dev/null; then \
		echo "✓ 后端服务运行中 (PID: $$(cat $(BACKEND_PID_FILE)))"; \
		echo "  API文档: http://localhost:8000/docs"; \
		echo "  日志文件: $(BACKEND_LOG_FILE)"; \
	else \
		echo "✗ 后端服务未运行"; \
		rm -f $(BACKEND_PID_FILE); \
	fi

dev-frontend:
	@echo "启动前端开发服务器..."
	@echo "前端地址: http://localhost:5173"
	cd frontend && npm run dev

dev-frontend-remote:
	@echo "启动前端开发服务器（API: $(VITE_API_BASE_URL)）..."
	@echo "前端地址: http://0.0.0.0:5173（内网访问请用本机 IP）"
	cd frontend && VITE_API_BASE_URL=$(VITE_API_BASE_URL) npm run dev

start-frontend-remote:
	@mkdir -p logs
	@if [ -f $(FRONTEND_REMOTE_PID_FILE) ] && kill -0 $$(cat $(FRONTEND_REMOTE_PID_FILE)) 2>/dev/null; then \
		echo "前端服务已在运行中 (PID: $$(cat $(FRONTEND_REMOTE_PID_FILE)))，请先执行 make stop-frontend-remote"; \
	else \
		echo "后台启动前端（API: $(VITE_API_BASE_URL)）..."; \
		cd frontend && nohup env VITE_API_BASE_URL=$(VITE_API_BASE_URL) npm run dev \
			> ../$(FRONTEND_REMOTE_LOG_FILE) 2>&1 & echo $$! > $(FRONTEND_REMOTE_PID_FILE); \
		sleep 2; \
		if kill -0 $$(cat $(FRONTEND_REMOTE_PID_FILE)) 2>/dev/null; then \
			echo "✓ 前端服务已启动 (PID: $$(cat $(FRONTEND_REMOTE_PID_FILE)))"; \
			echo "  日志文件: $(FRONTEND_REMOTE_LOG_FILE)"; \
			echo "  查看日志: make logs-frontend-remote"; \
		else \
			echo "✗ 启动失败，请查看日志: $(FRONTEND_REMOTE_LOG_FILE)"; \
		fi \
	fi

stop-frontend-remote:
	@if [ -f $(FRONTEND_REMOTE_PID_FILE) ] && kill -0 $$(cat $(FRONTEND_REMOTE_PID_FILE)) 2>/dev/null; then \
		echo "停止前端服务 (PID: $$(cat $(FRONTEND_REMOTE_PID_FILE)))..."; \
		kill $$(cat $(FRONTEND_REMOTE_PID_FILE)); \
		rm -f $(FRONTEND_REMOTE_PID_FILE); \
		echo "✓ 前端服务已停止"; \
	else \
		echo "前端服务未在运行"; \
		rm -f $(FRONTEND_REMOTE_PID_FILE); \
	fi

restart-frontend-remote: stop-frontend-remote
	@sleep 1
	@$(MAKE) start-frontend-remote

logs-frontend-remote:
	@mkdir -p logs
	@echo "实时查看前端日志（Ctrl+C 退出）..."
	@tail -f $(FRONTEND_REMOTE_LOG_FILE)

status-frontend-remote:
	@if [ -f $(FRONTEND_REMOTE_PID_FILE) ] && kill -0 $$(cat $(FRONTEND_REMOTE_PID_FILE)) 2>/dev/null; then \
		echo "✓ 前端服务运行中 (PID: $$(cat $(FRONTEND_REMOTE_PID_FILE)))"; \
		echo "  日志文件: $(FRONTEND_REMOTE_LOG_FILE)"; \
	else \
		echo "✗ 前端服务未运行"; \
		rm -f $(FRONTEND_REMOTE_PID_FILE); \
	fi

install: setup-backend setup-frontend
	@echo "所有依赖已安装完成！"

check:
	@echo "检查服务状态..."
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "✓ 后端服务运行中 (http://localhost:8000)" || echo "✗ 后端服务未运行"
	@curl -s http://localhost:5173 > /dev/null 2>&1 && echo "✓ 前端服务运行中 (http://localhost:5173)" || echo "✗ 前端服务未运行"
