import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update

from app.db import models
from app.repositories import Repository


class NotificationRepository(Repository):
    def page(self, user_id: uuid.UUID, limit: int, offset: int):
        stmt = (
            select(models.Notification)
            .where(models.Notification.user_id == user_id)
            .order_by(models.Notification.created_at.desc())
        )
        return self.paginate(stmt, limit, offset)

    def unread_count(self, user_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count(models.Notification.id)).where(
                    models.Notification.user_id == user_id,
                    models.Notification.read_at.is_(None),
                )
            )
            or 0
        )

    def mark_all_read(self, user_id: uuid.UUID) -> None:
        self.db.execute(
            update(models.Notification)
            .where(models.Notification.user_id == user_id,
                   models.Notification.read_at.is_(None))
            .values(read_at=datetime.now(timezone.utc))
        )
        self.db.commit()

    def fingerprint(self, user_id: uuid.UUID) -> str:
        latest = self.db.scalar(
            select(models.Notification.id)
            .where(models.Notification.user_id == user_id)
            .order_by(models.Notification.created_at.desc())
            .limit(1)
        )
        return f"{self.unread_count(user_id)}:{latest}"
