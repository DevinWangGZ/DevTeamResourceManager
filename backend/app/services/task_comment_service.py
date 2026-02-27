"""任务留言服务"""
from sqlalchemy.orm import Session
from typing import List

from app.models.task import Task
from app.models.task_comment import TaskComment
from app.models.task_collaborator import TaskCollaborator
from app.schemas.task_comment import TaskCommentCreate, TaskCommentUpdate, TaskCommentResponse
from app.core.exceptions import NotFoundError, PermissionDeniedError


class TaskCommentService:
    """任务留言服务类"""

    @staticmethod
    def _check_task_access(db: Session, task_id: int, user_id: int) -> Task:
        """校验任务是否存在，以及用户是否有权限留言（任务参与者：发布人/认领人/协助人均可）"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError(f"任务 {task_id} 不存在")

        # 任务发布人、认领人、协助人均可留言
        is_creator = task.creator_id == user_id
        is_assignee = task.assignee_id == user_id
        is_collaborator = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task_id,
            TaskCollaborator.user_id == user_id
        ).first() is not None

        if not (is_creator or is_assignee or is_collaborator):
            raise PermissionDeniedError("您不是该任务的参与者，无法留言")

        return task

    @staticmethod
    def get_comments(db: Session, task_id: int, user_id: int) -> List[TaskCommentResponse]:
        """获取任务留言列表（任务参与者可查看）"""
        TaskCommentService._check_task_access(db, task_id, user_id)

        comments = (
            db.query(TaskComment)
            .filter(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.desc())
            .all()
        )

        return [
            TaskCommentResponse(
                id=c.id,
                task_id=c.task_id,
                user_id=c.user_id,
                user_name=c.user.username if c.user else "未知",
                user_full_name=c.user.full_name if c.user else None,
                content=c.content,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in comments
        ]

    @staticmethod
    def create_comment(
        db: Session,
        task_id: int,
        user_id: int,
        data: TaskCommentCreate,
    ) -> TaskCommentResponse:
        """发表留言"""
        TaskCommentService._check_task_access(db, task_id, user_id)

        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            content=data.content.strip(),
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        return TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            user_id=comment.user_id,
            user_name=comment.user.username if comment.user else "未知",
            user_full_name=comment.user.full_name if comment.user else None,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    @staticmethod
    def update_comment(
        db: Session,
        comment_id: int,
        user_id: int,
        data: TaskCommentUpdate,
    ) -> TaskCommentResponse:
        """编辑留言（只有留言本人可以编辑）"""
        comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
        if not comment:
            raise NotFoundError(f"留言 {comment_id} 不存在")
        if comment.user_id != user_id:
            raise PermissionDeniedError("只有留言本人可以编辑")

        comment.content = data.content.strip()
        db.commit()
        db.refresh(comment)

        return TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            user_id=comment.user_id,
            user_name=comment.user.username if comment.user else "未知",
            user_full_name=comment.user.full_name if comment.user else None,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    @staticmethod
    def delete_comment(db: Session, comment_id: int, user_id: int) -> None:
        """删除留言（只有留言本人可以删除）"""
        comment = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
        if not comment:
            raise NotFoundError(f"留言 {comment_id} 不存在")
        if comment.user_id != user_id:
            raise PermissionDeniedError("只有留言本人可以删除")

        db.delete(comment)
        db.commit()
