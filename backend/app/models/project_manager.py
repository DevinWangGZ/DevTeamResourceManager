"""项目协办管理员（可查看任务执行、进展统计等，与同项目创建人等效数据权限）"""

from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class ProjectManager(Base):
    """项目级管理员（除创建者外额外指定；创建者无须在此表）。每个项目可有多人。"""

    __tablename__ = "project_managers"

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_managers_proj_user"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    project = relationship("Project", back_populates="managers")
