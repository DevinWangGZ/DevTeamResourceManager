"""文件上传API端点"""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from app.api.deps import get_current_user
from app.models.user import User
from app.core.exceptions import ValidationError
from app.utils.paths import get_uploads_images_dir

router = APIRouter()

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml',
}

# 最大文件大小（5MB）
MAX_FILE_SIZE = 5 * 1024 * 1024

# 上传目录
UPLOAD_DIR = get_uploads_images_dir()


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传图片
    
    权限：所有登录用户都可以上传
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(
            f"不支持的文件类型: {file.content_type}。支持的格式: JPEG, PNG, GIF, WebP, SVG"
        )
    
    # 验证文件大小
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise ValidationError(f"文件大小不能超过 {MAX_FILE_SIZE / 1024 / 1024}MB")
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix or '.jpg'
    filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # 保存文件
    try:
        with open(file_path, 'wb') as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 返回文件URL（相对路径，前端会自动拼接baseURL）
    file_url = f"/uploads/images/{filename}"
    
    return {
        "url": file_url,
        "filename": filename,
        "size": len(file_content),
    }


@router.post("/images")
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    批量上传图片
    
    权限：所有登录用户都可以上传
    """
    results = []
    errors = []
    
    for file in files:
        try:
            # 验证文件类型
            if file.content_type not in ALLOWED_IMAGE_TYPES:
                errors.append(f"{file.filename}: 不支持的文件类型")
                continue
            
            # 验证文件大小
            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: 文件大小超过限制")
                continue
            
            # 生成唯一文件名
            file_ext = Path(file.filename).suffix or '.jpg'
            filename = f"{uuid.uuid4().hex}{file_ext}"
            file_path = UPLOAD_DIR / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 返回文件URL
            file_url = f"/uploads/images/{filename}"
            results.append({
                "url": file_url,
                "filename": filename,
                "size": len(file_content),
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    if errors and not results:
        raise HTTPException(status_code=400, detail="所有文件上传失败: " + "; ".join(errors))
    
    return {
        "results": results,
        "errors": errors,
    }
