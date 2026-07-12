import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db import models
from app.repositories import Repository


class DuplicateRepository(Repository):
    def get(self, flag_id: uuid.UUID) -> models.DuplicateFlag | None:
        return self.db.scalar(
            select(models.DuplicateFlag)
            .options(
                joinedload(models.DuplicateFlag.patient_a),
                joinedload(models.DuplicateFlag.patient_b),
            )
            .where(models.DuplicateFlag.id == flag_id)
        )

    def page(self, status: str | None, limit: int, offset: int):
        stmt = (
            select(models.DuplicateFlag)
            .options(
                joinedload(models.DuplicateFlag.patient_a),
                joinedload(models.DuplicateFlag.patient_b),
            )
            .order_by(models.DuplicateFlag.created_at.desc())
        )
        if status:
            stmt = stmt.where(models.DuplicateFlag.status == status)
        return self.paginate(stmt, limit, offset)

    def existing_pair(self, a: uuid.UUID, b: uuid.UUID) -> models.DuplicateFlag | None:
        stmt = select(models.DuplicateFlag).where(
            ((models.DuplicateFlag.patient_a_id == a) & (models.DuplicateFlag.patient_b_id == b))
            | ((models.DuplicateFlag.patient_a_id == b) & (models.DuplicateFlag.patient_b_id == a))
        )
        return self.db.scalars(stmt).first()

    def pending_for_patient(self, patient_id: uuid.UUID) -> int:
        stmt = select(models.DuplicateFlag).where(
            models.DuplicateFlag.status == "pending",
            (models.DuplicateFlag.patient_a_id == patient_id)
            | (models.DuplicateFlag.patient_b_id == patient_id),
        )
        return len(list(self.db.scalars(stmt)))
