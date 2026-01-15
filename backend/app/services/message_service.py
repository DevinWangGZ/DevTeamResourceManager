"""消息通知服务"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.message import Message, MessageType
from app.models.task import Task, TaskStatus
from app.core.exceptions import NotFoundError, PermissionDeniedError


class MessageService:
    """消息通知服务类"""

    @staticmethod
    def create_message(
        db: Session,
        user_id: int,
        title: str,
        content: Optional[str] = None,
        message_type: str = MessageType.TASK_STATUS_CHANGE.value,
        related_task_id: Optional[int] = None
    ) -> Message:
        """创建消息"""
        message = Message(
            user_id=user_id,
            title=title,
            content=content,
            type=message_type,
            related_task_id=related_task_id,
            is_read=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def create_task_status_change_message(
        db: Session,
        task: Task,
        old_status: Optional[str] = None,
        new_status: str = None
    ) -> Optional[Message]:
        """创建任务状态变更消息"""
        if not task:
            return None

        # 确定接收消息的用户
        recipient_id = None
        title = ""
        content = ""

        if new_status == TaskStatus.PUBLISHED.value:
            # 任务发布：通知所有开发人员（这里简化处理，实际可以通知所有开发人员）
            # 暂时不创建消息，因为不知道具体通知谁
            return None

        elif new_status == TaskStatus.PENDING_EVAL.value:
            # 任务派发给开发人员：通知被派发的开发人员
            if task.assignee_id:
                recipient_id = task.assignee_id
                title = "新任务待评估"
                content = f"任务《{task.title}》已派发给您，请及时评估。"
            else:
                return None

        elif new_status == TaskStatus.CLAIMED.value:
            # 任务被认领：通知项目经理
            if task.creator_id:
                recipient_id = task.creator_id
                assignee_name = task.assignee.full_name or task.assignee.username if task.assignee else "未知"
                title = "任务已被认领"
                content = f"任务《{task.title}》已被 {assignee_name} 认领。"
            else:
                return None

        elif new_status == TaskStatus.IN_PROGRESS.value:
            # 任务开始：通知项目经理
            if task.creator_id:
                recipient_id = task.creator_id
                assignee_name = task.assignee.full_name or task.assignee.username if task.assignee else "未知"
                title = "任务已开始"
                content = f"任务《{task.title}》已由 {assignee_name} 开始执行。"
            else:
                return None

        elif new_status == TaskStatus.SUBMITTED.value:
            # 任务提交：通知项目经理
            if task.creator_id:
                recipient_id = task.creator_id
                assignee_name = task.assignee.full_name or task.assignee.username if task.assignee else "未知"
                title = "任务已提交，等待确认"
                content = f"任务《{task.title}》已由 {assignee_name} 提交，请及时确认。"
            else:
                return None

        elif new_status == TaskStatus.CONFIRMED.value:
            # 任务确认：通知开发人员
            if task.assignee_id:
                recipient_id = task.assignee_id
                title = "任务已确认"
                content = f"您提交的任务《{task.title}》已被确认。"
            else:
                return None

        elif new_status == TaskStatus.ARCHIVED.value:
            # 任务归档：通知相关用户（创建者和认领者）
            # 这里简化处理，只通知创建者
            if task.creator_id:
                recipient_id = task.creator_id
                title = "任务已归档"
                content = f"任务《{task.title}》已被归档。"
            else:
                return None

        if recipient_id:
            return MessageService.create_message(
                db=db,
                user_id=recipient_id,
                title=title,
                content=content,
                message_type=MessageType.TASK_STATUS_CHANGE.value,
                related_task_id=task.id
            )
        return None

    @staticmethod
    def create_todo_reminder_message(
        db: Session,
        user_id: int,
        title: str,
        content: str,
        related_task_id: Optional[int] = None
    ) -> Message:
        """创建待办提醒消息"""
        return MessageService.create_message(
            db=db,
            user_id=user_id,
            title=title,
            content=content,
            message_type=MessageType.TODO_REMINDER.value,
            related_task_id=related_task_id
        )

    @staticmethod
    def get_messages(
        db: Session,
        user_id: int,
        message_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Message], int]:
        """获取用户消息列表"""
        query = db.query(Message).filter(Message.user_id == user_id)

        if message_type:
            query = query.filter(Message.type == message_type)

        if is_read is not None:
            query = query.filter(Message.is_read == is_read)

        total = query.count()
        messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

        return messages, total

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """获取用户未读消息数量"""
        return db.query(Message).filter(
            Message.user_id == user_id,
            Message.is_read == False
        ).count()

    @staticmethod
    def mark_as_read(db: Session, message_id: int, user_id: int) -> Message:
        """标记消息为已读"""
        message = db.query(Message).filter(
            Message.id == message_id,
            Message.user_id == user_id
        ).first()

        if not message:
            raise NotFoundError("消息", str(message_id))

        message.is_read = True
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int, message_type: Optional[str] = None) -> int:
        """标记所有消息为已读"""
        query = db.query(Message).filter(
            Message.user_id == user_id,
            Message.is_read == False
        )

        if message_type:
            query = query.filter(Message.type == message_type)

        count = query.update({"is_read": True})
        db.commit()
        return count

    @staticmethod
    def delete_message(db: Session, message_id: int, user_id: int) -> None:
        """删除消息"""
        message = db.query(Message).filter(
            Message.id == message_id,
            Message.user_id == user_id
        ).first()

        if not message:
            raise NotFoundError("消息", str(message_id))

        db.delete(message)
        db.commit()
