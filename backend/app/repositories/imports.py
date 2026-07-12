import uuid

from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class ImportRepository(Repository):
    def get(self, batch_id: uuid.UUID) -> models.ImportBatch | None:
        return self.db.get(models.ImportBatch, batch_id)

    def page(self, limit: int, offset: int):
        stmt = select(models.ImportBatch).order_by(models.ImportBatch.created_at.desc())
        return self.paginate(stmt, limit, offset)

    def issues_page(self, batch_id: uuid.UUID, limit: int, offset: int):
        stmt = (
            select(models.ImportIssue)
            .where(models.ImportIssue.batch_id == batch_id)
            .order_by(models.ImportIssue.record_number)
        )
        return self.paginate(stmt, limit, offset)

    def add(self, batch: models.ImportBatch) -> models.ImportBatch:
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch
