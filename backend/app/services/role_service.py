"""角色服务"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.role import Role, RoleType
from app.core.exceptions import NotFoundError


class RoleService:
    """角色服务类"""

    @staticmethod
    def get_role_by_code(db: Session, role_code: str) -> Optional[Role]:
        """根据角色代码获取角色"""
        return db.query(Role).filter(Role.code == role_code).first()

    @staticmethod
    def get_role(db: Session, role_id: int) -> Optional[Role]:
        """根据ID获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()

    @staticmethod
    def get_all_roles(db: Session) -> List[Role]:
        """获取所有角色"""
        return db.query(Role).all()

    @staticmethod
    def get_or_create_role_by_code(db: Session, role_code: str) -> Role:
        """根据角色代码获取或创建角色"""
        role = RoleService.get_role_by_code(db, role_code)
        if role:
            return role

        # 如果不存在，创建角色
        role_type = RoleType(role_code)
        role_name_map = {
            RoleType.DEVELOPER: "开发人员",
            RoleType.PROJECT_MANAGER: "项目经理",
            RoleType.DEVELOPMENT_LEAD: "开发组长",
            RoleType.SYSTEM_ADMIN: "系统管理员",
        }
        role_description_map = {
            RoleType.DEVELOPER: "负责开发任务的技术人员",
            RoleType.PROJECT_MANAGER: "负责项目管理和任务分配",
            RoleType.DEVELOPMENT_LEAD: "负责团队管理和资源分配",
            RoleType.SYSTEM_ADMIN: "系统管理员，拥有所有权限",
        }

        role = Role(
            name=role_name_map.get(role_type, role_code),
            code=role_code,
            description=role_description_map.get(role_type, "")
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    @staticmethod
    def init_default_roles(db: Session) -> List[Role]:
        """初始化默认角色"""
        roles = []
        for role_type in RoleType:
            role = RoleService.get_or_create_role_by_code(db, role_type.value)
            roles.append(role)
        return roles
