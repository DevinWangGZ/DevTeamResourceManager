.PHONY: help setup-backend setup-frontend dev-backend dev-frontend test install

help:
	@echo "可用命令："
	@echo "  make setup-backend    - 设置后端环境"
	@echo "  make setup-frontend   - 设置前端环境"
	@echo "  make dev-backend      - 启动后端开发服务器"
	@echo "  make dev-frontend     - 启动前端开发服务器"
	@echo "  make install          - 安装所有依赖"

setup-backend:
	@echo "设置后端环境..."
	cd backend && pip install -r requirements/dev.txt
	cd backend && cp .env.example .env

setup-frontend:
	@echo "设置前端环境..."
	cd frontend && npm install
	cd frontend && cp .env.example .env.development

dev-backend:
	@echo "启动后端开发服务器..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "启动前端开发服务器..."
	cd frontend && npm run dev

install: setup-backend setup-frontend
	@echo "所有依赖已安装完成！"
