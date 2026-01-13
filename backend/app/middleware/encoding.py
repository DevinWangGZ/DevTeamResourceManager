"""编码中间件"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class EncodingMiddleware(BaseHTTPMiddleware):
    """确保所有响应使用UTF-8编码"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 确保JSON响应使用UTF-8编码
        if isinstance(response, Response):
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type and "charset" not in content_type:
                response.headers["content-type"] = "application/json; charset=utf-8"
        
        return response
