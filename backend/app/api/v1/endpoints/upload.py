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
from app.utils.paths import get_uploads_images_dir, get_uploads_attachments_dir

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

# 附件最大文件大小（50MB）
MAX_ATTACHMENT_SIZE = 50 * 1024 * 1024

# 上传目录
UPLOAD_DIR = get_uploads_images_dir()
ATTACHMENTS_DIR = get_uploads_attachments_dir()

# 允许的附件类型
ALLOWED_ATTACHMENT_TYPES = {
    # Word文档
    'application/msword',  # .doc
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    # PowerPoint
    'application/vnd.ms-powerpoint',  # .ppt
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
    # PDF
    'application/pdf',  # .pdf
    # Excel
    'application/vnd.ms-excel',  # .xls
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
}

# 文件扩展名到文件类型的映射
FILE_EXT_TO_TYPE = {
    '.doc': 'word',
    '.docx': 'word',
    '.ppt': 'ppt',
    '.pptx': 'ppt',
    '.pdf': 'pdf',
    '.xls': 'excel',
    '.xlsx': 'excel',
}


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


@router.post("/attachment")
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传附件（Word、PPT、PDF、Excel）
    
    权限：所有登录用户都可以上传
    支持格式：.doc, .docx, .ppt, .pptx, .pdf, .xls, .xlsx
    最大大小：50MB
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        # 也检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in FILE_EXT_TO_TYPE:
            raise ValidationError(
                f"不支持的文件类型。支持的格式: Word (.doc, .docx), PowerPoint (.ppt, .pptx), PDF (.pdf), Excel (.xls, .xlsx)"
            )
    
    # 验证文件大小
    file_content = await file.read()
    if len(file_content) > MAX_ATTACHMENT_SIZE:
        raise ValidationError(f"文件大小不能超过 {MAX_ATTACHMENT_SIZE / 1024 / 1024}MB")
    
    # 获取文件扩展名和类型
    file_ext = Path(file.filename).suffix.lower()
    file_type = FILE_EXT_TO_TYPE.get(file_ext, 'unknown')
    
    # 生成唯一文件名
    filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = ATTACHMENTS_DIR / filename
    
    # 保存文件
    try:
        with open(file_path, 'wb') as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 返回文件URL（相对路径，前端会自动拼接baseURL）
    file_url = f"/uploads/attachments/{filename}"
    
    return {
        "url": file_url,
        "filename": file.filename,  # 原始文件名
        "saved_filename": filename,  # 保存的文件名
        "size": len(file_content),
        "type": file_type,
        "mime_type": file.content_type or "application/octet-stream",
    }
