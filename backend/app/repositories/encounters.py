import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.db import models
from app.repositories import Repository


class EncounterRepository(Repository):
    def get(self, encounter_id: uuid.UUID) -> models.Encounter | None:
        return self.db.scalar(
            select(models.Encounter)
            .options(
                joinedload(models.Encounter.clinician),
                selectinload(models.Encounter.observations),
            )
            .where(models.Encounter.id == encounter_id)
        )

    def page_for_patient(self, patient_id: uuid.UUID, limit: int, offset: int):
        stmt = (
            select(models.Encounter)
            .options(
                joinedload(models.Encounter.clinician),
                selectinload(models.Encounter.observations),
            )
            .where(models.Encounter.patient_id == patient_id)
            .order_by(models.Encounter.occurred_at.desc())
        )
        return self.paginate(stmt, limit, offset)

    def add(self, encounter: models.Encounter) -> models.Encounter:
        self.db.add(encounter)
        self.db.commit()
        self.db.refresh(encounter)
        return encounter

    def save(self, encounter: models.Encounter) -> models.Encounter:
        self.db.commit()
        self.db.refresh(encounter)
        return encounter
