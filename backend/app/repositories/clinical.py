import uuid

from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class ClinicalListRepository(Repository):
    """Problem list, medications and allergies for a patient (small, bounded lists)."""

    def problems(self, patient_id: uuid.UUID) -> list[models.Problem]:
        stmt = (
            select(models.Problem)
            .where(models.Problem.patient_id == patient_id)
            .order_by(models.Problem.status, models.Problem.created_at.desc())
            .limit(200)
        )
        return list(self.db.scalars(stmt))

    def medications(self, patient_id: uuid.UUID) -> list[models.Medication]:
        stmt = (
            select(models.Medication)
            .where(models.Medication.patient_id == patient_id)
            .order_by(models.Medication.active.desc(), models.Medication.created_at.desc())
            .limit(200)
        )
        return list(self.db.scalars(stmt))

    def allergies(self, patient_id: uuid.UUID) -> list[models.Allergy]:
        stmt = (
            select(models.Allergy)
            .where(models.Allergy.patient_id == patient_id)
            .order_by(models.Allergy.created_at.desc())
            .limit(200)
        )
        return list(self.db.scalars(stmt))

    def get_problem(self, problem_id: uuid.UUID) -> models.Problem | None:
        return self.db.get(models.Problem, problem_id)

    def get_medication(self, medication_id: uuid.UUID) -> models.Medication | None:
        return self.db.get(models.Medication, medication_id)

    def get_allergy(self, allergy_id: uuid.UUID) -> models.Allergy | None:
        return self.db.get(models.Allergy, allergy_id)

    def add(self, item) -> object:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def save(self, item) -> object:
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item) -> None:
        self.db.delete(item)
        self.db.commit()
