"""自定义异常"""
from fastapi import HTTPException, status
from typing import Optional


class AppException(Exception):
    """应用基础异常"""
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """资源不存在异常"""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource}不存在"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )


class PermissionDeniedError(AppException):
    """权限不足异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationError(AppException):
    """数据验证异常"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST
        )
