import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.db import models
from app.repositories import Repository

_LOADS = (
    joinedload(models.Message.sender),
    joinedload(models.Message.recipient),
    joinedload(models.Message.patient),
    selectinload(models.Message.attachments),
)


class MessageRepository(Repository):
    def get(self, message_id: uuid.UUID) -> models.Message | None:
        return self.db.scalar(
            select(models.Message).options(*_LOADS).where(models.Message.id == message_id)
        )

    def get_attachment(self, attachment_id: uuid.UUID) -> models.MessageAttachment | None:
        return self.db.scalar(
            select(models.MessageAttachment)
            .options(joinedload(models.MessageAttachment.message))
            .where(models.MessageAttachment.id == attachment_id)
        )

    def inbox(
        self, user_id: uuid.UUID, unread_only: bool, archived: bool, limit: int, offset: int
    ):
        stmt = (
            select(models.Message)
            .options(*_LOADS)
            .where(models.Message.recipient_id == user_id)
            .order_by(models.Message.created_at.desc())
        )
        stmt = (
            stmt.where(models.Message.archived_at.is_not(None))
            if archived
            else stmt.where(models.Message.archived_at.is_(None))
        )
        if unread_only:
            stmt = stmt.where(models.Message.read_at.is_(None))
        return self.paginate(stmt, limit, offset)

    def sent(self, user_id: uuid.UUID, limit: int, offset: int):
        stmt = (
            select(models.Message)
            .options(*_LOADS)
            .where(models.Message.sender_id == user_id)
            .order_by(models.Message.created_at.desc())
        )
        return self.paginate(stmt, limit, offset)

    def unread_count(self, user_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count(models.Message.id)).where(
                    models.Message.recipient_id == user_id,
                    models.Message.read_at.is_(None),
                    models.Message.archived_at.is_(None),
                )
            )
            or 0
        )

    def fingerprint(self, user_id: uuid.UUID) -> str:
        """Cheap change signature for the SSE channel: unread count + latest id."""
        unread = self.unread_count(user_id)
        latest = self.db.scalar(
            select(models.Message.id)
            .where(
                (models.Message.recipient_id == user_id) | (models.Message.sender_id == user_id)
            )
            .order_by(models.Message.created_at.desc())
            .limit(1)
        )
        return f"{unread}:{latest}"

    def thread(self, root_id: uuid.UUID, user_id: uuid.UUID) -> list[models.Message]:
        """Every message in the conversation the user participates in."""
        stmt = (
            select(models.Message)
            .options(*_LOADS)
            .where(
                models.Message.root_id == root_id,
                (models.Message.sender_id == user_id) | (models.Message.recipient_id == user_id),
            )
            .order_by(models.Message.created_at)
        )
        return list(self.db.scalars(stmt))

    def add(self, message: models.Message) -> models.Message:
        self.db.add(message)
        self.db.commit()
        return self.get(message.id)
