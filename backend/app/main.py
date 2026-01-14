"""FastAPI应用入口"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from jose import JWTError
import logging
import json

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.v1.router import api_router
from app.middleware.encoding import EncodingMiddleware
from app.utils.paths import get_uploads_dir, get_uploads_images_dir

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 编码中间件（确保UTF-8编码）
app.add_middleware(EncodingMiddleware)

# CORS配置
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 全局异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "code": exc.code or "APP_ERROR"
        },
        media_type="application/json; charset=utf-8"
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "请求参数验证失败",
            "code": "VALIDATION_ERROR",
            "errors": errors
        },
        media_type="application/json; charset=utf-8"
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "服务器内部错误",
            "code": "INTERNAL_ERROR"
        },
        media_type="application/json; charset=utf-8"
    )

# 配置静态文件服务（用于访问上传的图片）
# 注意：静态文件服务必须在路由注册之前配置，否则会被路由拦截
uploads_base_dir = get_uploads_dir()
uploads_images_dir = get_uploads_images_dir()

# 挂载静态文件服务
try:
    app.mount("/uploads", StaticFiles(directory=str(uploads_base_dir)), name="uploads")
    logger.info(f"静态文件服务已挂载: {uploads_base_dir}")
except Exception as e:
    logger.warning(f"静态文件服务挂载失败: {e}")

# 注册路由（必须在静态文件服务之后）
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "DevTeam Manager API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
