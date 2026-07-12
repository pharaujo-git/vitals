import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.db import models
from app.repositories import Repository

_LOADS = (
    joinedload(models.Message.sender),
    joinedload(models.Message.recipient),
    joinedload(models.Message.patient),
)


class MessageRepository(Repository):
    def get(self, message_id: uuid.UUID) -> models.Message | None:
        return self.db.scalar(
            select(models.Message).options(*_LOADS).where(models.Message.id == message_id)
        )

    def inbox(self, user_id: uuid.UUID, unread_only: bool, limit: int, offset: int):
        stmt = (
            select(models.Message)
            .options(*_LOADS)
            .where(models.Message.recipient_id == user_id)
            .order_by(models.Message.created_at.desc())
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
                )
            )
            or 0
        )

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
