"""路径工具模块"""
from pathlib import Path


def get_backend_dir() -> Path:
    """
    获取backend目录的绝对路径
    
    无论从哪个文件调用，都能正确返回backend目录
    """
    # 获取当前文件的绝对路径
    current_file = Path(__file__).resolve()
    # utils/paths.py位于: backend/app/utils/paths.py
    # 需要回到: backend/
    return current_file.parent.parent.parent


def get_uploads_dir() -> Path:
    """获取uploads目录路径"""
    return get_backend_dir() / 'uploads'


def get_uploads_images_dir() -> Path:
    """获取uploads/images目录路径"""
    images_dir = get_uploads_dir() / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    return images_dir


def get_uploads_attachments_dir() -> Path:
    """获取uploads/attachments目录路径"""
    attachments_dir = get_uploads_dir() / 'attachments'
    attachments_dir.mkdir(parents=True, exist_ok=True)
    return attachments_dir
