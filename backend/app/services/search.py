from sqlalchemy.orm import Session

from app.db import models
from app.repositories.encounters import EncounterRepository
from app.repositories.patients import PatientRepository

CLINICAL_ROLES = ("clinician", "admin")


def search(db: Session, user: models.User, query: str) -> dict:
    """Search patients and encounters, scoped to what the caller may see.

    Front desk can find patients for scheduling but never clinical
    encounters; clinicians and admins see both.
    """
    patients, _ = PatientRepository(db).page(query, limit=8, offset=0)
    encounters = (
        EncounterRepository(db).search(query) if user.role in CLINICAL_ROLES else []
    )
    return {"patients": patients, "encounters": encounters}
