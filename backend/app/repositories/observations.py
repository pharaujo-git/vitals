import uuid

from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class ObservationRepository(Repository):
    def for_patient(self, patient_id: uuid.UUID, limit: int = 1000) -> list[models.Observation]:
        stmt = (
            select(models.Observation)
            .where(models.Observation.patient_id == patient_id)
            .order_by(models.Observation.taken_at)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
