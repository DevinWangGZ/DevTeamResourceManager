#!/bin/bash
# 启动开发环境脚本

set -e

echo "🚀 启动 DevTeam Manager 开发环境"
echo ""

# 检查后端服务
check_backend() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ 后端服务已运行 (http://localhost:8000)"
        return 0
    else
        echo "✗ 后端服务未运行"
        return 1
    fi
}

# 检查前端服务
check_frontend() {
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo "✓ 前端服务已运行 (http://localhost:5173)"
        return 0
    else
        echo "✗ 前端服务未运行"
        return 1
    fi
}

# 启动后端
start_backend() {
    echo "📦 启动后端服务..."
    cd backend
    if [ ! -f ".env" ]; then
        echo "⚠️  未找到 .env 文件，请先配置环境变量"
        echo "   可以复制 env.example 为 .env"
    fi
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo "   后端服务PID: $BACKEND_PID"
    sleep 3
    if check_backend; then
        echo "   API文档: http://localhost:8000/docs"
    else
        echo "   ⚠️  后端服务启动可能失败，请检查日志"
    fi
    cd ..
}

# 启动前端
start_frontend() {
    echo "📦 启动前端服务..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    echo "   前端服务PID: $FRONTEND_PID"
    sleep 3
    if check_frontend; then
        echo "   前端地址: http://localhost:5173"
    else
        echo "   ⚠️  前端服务启动可能失败，请检查日志"
    fi
    cd ..
}

# 主逻辑
if [ "$1" == "backend" ]; then
    start_backend
elif [ "$1" == "frontend" ]; then
    start_frontend
elif [ "$1" == "check" ]; then
    echo "🔍 检查服务状态..."
    check_backend
    check_frontend
else
    echo "用法:"
    echo "  ./scripts/start-dev.sh backend   - 启动后端"
    echo "  ./scripts/start-dev.sh frontend  - 启动前端"
    echo "  ./scripts/start-dev.sh check    - 检查服务状态"
    echo ""
    echo "或者使用 Makefile:"
    echo "  make dev-backend   - 启动后端"
    echo "  make dev-frontend  - 启动前端"
fi
