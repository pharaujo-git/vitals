from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class AuditRepository(Repository):
    def page(self, action: str | None, entity_id: str | None, limit: int, offset: int):
        stmt = select(models.AuditLog).order_by(models.AuditLog.created_at.desc())
        if action:
            stmt = stmt.where(models.AuditLog.action == action)
        if entity_id:
            stmt = stmt.where(models.AuditLog.entity_id == entity_id)
        return self.paginate(stmt, limit, offset)

    def actions(self) -> list[str]:
        stmt = select(models.AuditLog.action).distinct().order_by(models.AuditLog.action)
        return list(self.db.scalars(stmt))
