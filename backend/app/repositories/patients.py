import uuid

from sqlalchemy import or_, select

from app.db import models
from app.repositories import Repository


class PatientRepository(Repository):
    def get(self, patient_id: uuid.UUID) -> models.Patient | None:
        return self.db.get(models.Patient, patient_id)

    def by_mrn(self, mrn: str) -> models.Patient | None:
        return self.db.scalar(select(models.Patient).where(models.Patient.mrn == mrn))

    SORTS = {
        "name": (models.Patient.last_name, models.Patient.first_name),
        "dob": (models.Patient.dob,),
        "newest": (models.Patient.created_at.desc(),),
    }

    def page(self, search: str | None, limit: int, offset: int, sort: str = "name"):
        order = self.SORTS.get(sort, self.SORTS["name"])
        stmt = (
            select(models.Patient)
            .where(models.Patient.merged_into_id.is_(None))
            .order_by(*order)
        )
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    models.Patient.first_name.ilike(like),
                    models.Patient.last_name.ilike(like),
                    (models.Patient.first_name + " " + models.Patient.last_name).ilike(like),
                    models.Patient.mrn.ilike(like),
                    models.Patient.phone.ilike(like),
                    models.Patient.email.ilike(like),
                )
            )
        return self.paginate(stmt, limit, offset)

    def add(self, patient: models.Patient) -> models.Patient:
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def save(self, patient: models.Patient) -> models.Patient:
        self.db.commit()
        self.db.refresh(patient)
        return patient
