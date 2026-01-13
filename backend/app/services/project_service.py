"""项目服务"""
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from decimal import Decimal

from app.models.project import Project
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """项目服务类"""

    @staticmethod
    def create_project(db: Session, project_data: ProjectCreate, creator_id: int) -> Project:
        """创建项目"""
        # 检查项目名称是否已存在
        existing = db.query(Project).filter(Project.name == project_data.name).first()
        if existing:
            raise ValueError(f"项目名称 '{project_data.name}' 已存在")

        project = Project(
            name=project_data.name,
            description=project_data.description,
            estimated_output_value=project_data.estimated_output_value,
            created_by=creator_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """获取项目"""
        from sqlalchemy.orm import joinedload
        from app.models.user import User
        
        return db.query(Project).options(joinedload(Project.creator)).filter(Project.id == project_id).first()

    @staticmethod
    def get_projects(
        db: Session,
        creator_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Project], int]:
        """获取项目列表"""
        from sqlalchemy.orm import joinedload
        from app.models.user import User
        
        query = db.query(Project).options(joinedload(Project.creator))
        
        if creator_id is not None:
            query = query.filter(Project.created_by == creator_id)
        
        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
        
        return projects, total

    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        project_data: ProjectUpdate,
        current_user_id: int
    ) -> Project:
        """更新项目"""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise NotFoundError("项目不存在")

        # 权限检查：只有创建者可以更新
        if project.created_by != current_user_id:
            raise PermissionDeniedError("只能更新自己创建的项目")

        # 如果更新名称，检查是否重复
        if project_data.name and project_data.name != project.name:
            existing = db.query(Project).filter(
                Project.name == project_data.name,
                Project.id != project_id
            ).first()
            if existing:
                raise ValueError(f"项目名称 '{project_data.name}' 已存在")
            project.name = project_data.name

        if project_data.description is not None:
            project.description = project_data.description
        if project_data.estimated_output_value is not None:
            project.estimated_output_value = project_data.estimated_output_value

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: int, current_user_id: int) -> None:
        """删除项目"""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise NotFoundError("项目不存在")

        # 权限检查：只有创建者可以删除
        if project.created_by != current_user_id:
            raise PermissionDeniedError("只能删除自己创建的项目")

        db.delete(project)
        db.commit()
