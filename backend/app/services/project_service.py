"""项目服务"""
from sqlalchemy.orm import Session
from sqlalchemy import exists, or_
from sqlalchemy.orm import joinedload
from typing import Optional, List, Tuple
from decimal import Decimal

from app.models.project import Project
from app.models.project_manager import ProjectManager
from app.models.user import User
from app.models.role import RoleType
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """项目服务类"""

    @staticmethod
    def user_is_co_project_manager(db: Session, project_id: int, user_id: int) -> bool:
        """是否为本项目的协办管理员（不含创建者）"""
        row = db.query(ProjectManager.id).filter(
            ProjectManager.project_id == project_id,
            ProjectManager.user_id == user_id,
        ).first()
        return row is not None

    @staticmethod
    def user_can_manage_project(db: Session, project_id: int, user_id: int) -> bool:
        """创建者或协办管理员可操作项目基本信息（与非删除类接口一致）"""
        project = ProjectService.get_project(db, project_id)
        if not project:
            return False
        if project.created_by == user_id:
            return True
        return ProjectService.user_is_co_project_manager(db, project_id, user_id)

    @staticmethod
    def user_can_manage_co_managers(db: Session, project_id: int, user_id: int) -> bool:
        """仅创建者可指定协办项目经理（或由管理员代为操作）"""
        project = ProjectService.get_project(db, project_id)
        if not project:
            return False
        return project.created_by == user_id

    @staticmethod
    def get_co_manager_user_ids(db: Session, project_id: int) -> List[int]:
        rows = db.query(ProjectManager.user_id).filter(ProjectManager.project_id == project_id).all()
        return [r.user_id for r in rows]

    @staticmethod
    def get_projects_managed_by_user(
        db: Session,
        user_id: int,
        *,
        creator_filter: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Project], int]:
        """
        当前用户担任创建者或协办管理员的项目。
        creator_filter 若指定，则还要求项目创建者等于该 ID（供后台筛选）。
        """
        managed_exists = exists().where(
            ProjectManager.project_id == Project.id,
            ProjectManager.user_id == user_id,
        )
        query = db.query(Project).options(joinedload(Project.creator)).filter(
            or_(Project.created_by == user_id, managed_exists),
        )
        if creator_filter is not None:
            query = query.filter(Project.created_by == creator_filter)

        total = query.count()
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
        return projects, total

    @staticmethod
    def set_co_managers(db: Session, project_id: int, user_ids: List[int]) -> None:
        """替换协办项目经理列表（不含创建者）；user_ids 必须为具备项目经理角色的用户。"""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise NotFoundError("项目不存在")

        uid_set = {int(u) for u in user_ids if u is not None}
        uid_set.discard(project.created_by)

        for uid in uid_set:
            u = db.query(User).filter(User.id == uid).first()
            if not u:
                raise ValueError(f"用户不存在: {uid}")
            if not u.has_role(RoleType.PROJECT_MANAGER.value):
                raise ValueError(f"仅能指定具备「项目经理」角色的用户协办项目（无效用户 id={uid}）")

        db.query(ProjectManager).filter(ProjectManager.project_id == project_id).delete(synchronize_session=False)
        for uid in uid_set:
            db.add(ProjectManager(project_id=project_id, user_id=uid))
        db.commit()

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
        return db.query(Project).options(joinedload(Project.creator)).filter(Project.id == project_id).first()

    @staticmethod
    def get_projects(
        db: Session,
        creator_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Project], int]:
        """获取项目列表（按创建者过滤）"""
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

        # 权限：创建者或协办项目经理可编辑
        if not ProjectService.user_can_manage_project(db, project_id, current_user_id):
            raise PermissionDeniedError("无权限修改该项目")

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

        # 权限：仅创建者可删除项目（协办经理不可删除，避免误操作）
        if project.created_by != current_user_id:
            raise PermissionDeniedError("仅能删除本人创建的项目")

        db.delete(project)
        db.commit()
