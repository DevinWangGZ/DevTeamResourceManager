.PHONY: help setup-backend setup-frontend dev-backend dev-frontend test install check

help:
	@echo "可用命令："
	@echo "  make setup-backend    - 设置后端环境"
	@echo "  make setup-frontend   - 设置前端环境"
	@echo "  make dev-backend      - 启动后端开发服务器"
	@echo "  make dev-frontend     - 启动前端开发服务器"
	@echo "  make install          - 安装所有依赖"
	@echo "  make check            - 检查服务状态"

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

dev-frontend:
	@echo "启动前端开发服务器..."
	@echo "前端地址: http://localhost:5173"
	cd frontend && npm run dev

install: setup-backend setup-frontend
	@echo "所有依赖已安装完成！"

check:
	@echo "检查服务状态..."
	@curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "✓ 后端服务运行中 (http://localhost:8000)" || echo "✗ 后端服务未运行"
	@curl -s http://localhost:5173 > /dev/null 2>&1 && echo "✓ 前端服务运行中 (http://localhost:5173)" || echo "✗ 前端服务未运行"
