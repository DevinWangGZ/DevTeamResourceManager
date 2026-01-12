# 日志与错误处理规范

> **文档版本**：v1.0 | **更新日期**：2024-05 | **负责人**：项目组

## 目录
- [日志规范](#日志规范)
- [错误处理规范](#错误处理规范)
- [前端日志](#前端日志)
- [后端日志](#后端日志)
- [错误码规范](#错误码规范)

---

## 日志规范

### 日志级别

- **DEBUG**：调试信息，开发时使用
- **INFO**：一般信息，记录正常操作
- **WARNING**：警告信息，不影响功能但需要注意
- **ERROR**：错误信息，功能异常但可恢复
- **CRITICAL**：严重错误，系统可能无法继续运行

### 日志格式

#### 前端日志格式

```typescript
// 使用console或日志库
console.log('[INFO]', '用户登录成功', { userId: 123 })
console.warn('[WARN]', 'API请求超时', { url: '/api/tasks' })
console.error('[ERROR]', '任务认领失败', { taskId: 456, error: error.message })
```

#### 后端日志格式

```python
import logging

logger = logging.getLogger(__name__)

# INFO级别
logger.info("用户登录成功", extra={"user_id": 123, "ip": "192.168.1.1"})

# WARNING级别
logger.warning("API请求超时", extra={"endpoint": "/api/tasks", "duration": 5.2})

# ERROR级别
logger.error("任务认领失败", extra={"task_id": 456, "error": str(e)}, exc_info=True)
```

### 日志内容要求

1. **包含上下文信息**
   - 用户ID、操作时间、IP地址
   - 请求参数、响应结果
   - 错误堆栈（ERROR级别）

2. **避免敏感信息**
   - 不记录密码、token等敏感信息
   - 不记录完整的请求体（如包含敏感数据）

3. **结构化日志**
   - 使用JSON格式（生产环境）
   - 便于日志分析和检索

---

## 错误处理规范

### 前端错误处理

#### 统一错误处理

```typescript
// utils/errorHandler.ts
import { ElMessage } from 'element-plus'

export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number
  ) {
    super(message)
    this.name = 'AppError'
  }
}

export function handleError(error: unknown) {
  if (error instanceof AppError) {
    ElMessage.error(error.message)
    // 记录错误日志
    console.error('[ERROR]', error.message, {
      code: error.code,
      statusCode: error.statusCode
    })
  } else if (error instanceof Error) {
    ElMessage.error(error.message || '操作失败，请稍后重试')
    console.error('[ERROR]', error.message, error)
  } else {
    ElMessage.error('未知错误，请稍后重试')
    console.error('[ERROR]', '未知错误', error)
  }
}
```

#### API错误处理

```typescript
// api/request.ts
import axios from 'axios'
import { handleError } from '@/utils/errorHandler'

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 未授权，跳转登录
          router.push('/login')
          break
        case 403:
          handleError(new AppError('无权限访问', 'FORBIDDEN', 403))
          break
        case 404:
          handleError(new AppError('资源不存在', 'NOT_FOUND', 404))
          break
        case 500:
          handleError(new AppError('服务器错误', 'SERVER_ERROR', 500))
          break
        default:
          handleError(
            new AppError(
              data?.message || '请求失败',
              data?.code,
              status
            )
          )
      }
    } else if (error.request) {
      handleError(new AppError('网络错误，请检查网络连接', 'NETWORK_ERROR'))
    } else {
      handleError(error)
    }
    
    return Promise.reject(error)
  }
)
```

### 后端错误处理

#### 统一异常处理

```python
# app/core/exceptions.py
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
```

#### 全局异常处理器

```python
# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理器"""
    logger.error(
        f"应用异常: {exc.message}",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    logger.warning(
        f"请求验证失败: {exc.errors()}",
        extra={"path": request.url.path}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "data": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        f"未处理的异常: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "data": None
        }
    )
```

---

## 前端日志

### 日志库选择

- **开发环境**：使用`console`即可
- **生产环境**：使用日志服务（如Sentry、LogRocket）

### 日志记录场景

1. **用户操作**
   ```typescript
   console.log('[INFO]', '用户认领任务', { taskId: 123, userId: 456 })
   ```

2. **API请求**
   ```typescript
   console.log('[INFO]', 'API请求', { url: '/api/tasks', method: 'GET' })
   console.error('[ERROR]', 'API请求失败', { url: '/api/tasks', error: error.message })
   ```

3. **性能监控**
   ```typescript
   const startTime = performance.now()
   // ... 操作
   const duration = performance.now() - startTime
   console.log('[PERF]', '操作耗时', { operation: 'task-list-load', duration })
   ```

---

## 后端日志

### 日志配置

```python
# app/core/logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                'logs/app.log',
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
        ]
    )
```

### 日志记录场景

1. **API请求**
   ```python
   logger.info(
       "API请求",
       extra={
           "method": request.method,
           "path": request.url.path,
           "user_id": current_user.id if current_user else None
       }
   )
   ```

2. **业务操作**
   ```python
   logger.info(
       "任务认领成功",
       extra={
           "task_id": task_id,
           "user_id": user_id,
           "status": "claimed"
       }
   )
   ```

3. **错误记录**
   ```python
   logger.error(
       "任务认领失败",
       extra={
           "task_id": task_id,
           "user_id": user_id,
           "error": str(e)
       },
       exc_info=True  # 包含堆栈信息
   )
   ```

---

## 错误码规范

### 错误码格式

- **格式**：`模块_错误类型`
- **示例**：`TASK_NOT_FOUND`、`AUTH_TOKEN_EXPIRED`

### 常见错误码

#### 认证相关（AUTH_*）
- `AUTH_TOKEN_EXPIRED`：Token过期
- `AUTH_TOKEN_INVALID`：Token无效
- `AUTH_CREDENTIALS_INVALID`：凭证无效

#### 权限相关（PERMISSION_*）
- `PERMISSION_DENIED`：权限不足
- `PERMISSION_REQUIRED`：需要权限

#### 资源相关（RESOURCE_*）
- `RESOURCE_NOT_FOUND`：资源不存在
- `RESOURCE_ALREADY_EXISTS`：资源已存在
- `RESOURCE_CONFLICT`：资源冲突

#### 验证相关（VALIDATION_*）
- `VALIDATION_ERROR`：验证错误
- `VALIDATION_REQUIRED`：必填字段缺失

#### 业务相关（BUSINESS_*）
- `BUSINESS_RULE_VIOLATION`：业务规则违反
- `BUSINESS_STATE_INVALID`：业务状态无效

### 错误响应格式

```json
{
  "code": "TASK_NOT_FOUND",
  "message": "任务不存在",
  "data": null,
  "timestamp": "2024-05-01T12:00:00Z"
}
```

---

## 更新日志

| 版本 | 日期 | 更新内容 | 负责人 |
|------|------|----------|--------|
| v1.0 | 2024-05 | 初始版本，制定日志与错误处理规范 | 项目组 |

---

**文档维护**：本文档随项目发展持续更新，重大变更需团队评审。
