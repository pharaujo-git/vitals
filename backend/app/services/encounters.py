import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db import models
from app.repositories.encounters import EncounterRepository
from app.repositories.patients import PatientRepository
from app.services import observations as observation_catalog

ENCOUNTER_TYPES = ("visit", "admission", "telehealth", "imported")


def create_encounter(
    db: Session,
    *,
    patient_id: uuid.UUID,
    clinician_id: uuid.UUID | None,
    occurred_at: datetime,
    encounter_type: str,
    reason: str | None,
    notes: str | None,
    observations: list[dict],
    source: str = "manual",
) -> models.Encounter:
    if PatientRepository(db).get(patient_id) is None:
        raise ValueError("Patient not found")
    if encounter_type not in ENCOUNTER_TYPES:
        raise ValueError(f"Encounter type must be one of: {', '.join(ENCOUNTER_TYPES)}")

    encounter = models.Encounter(
        patient_id=patient_id,
        clinician_id=clinician_id,
        occurred_at=occurred_at,
        encounter_type=encounter_type,
        reason=reason,
        notes=notes,
        source=source,
    )
    for obs in observations:
        encounter.observations.append(
            build_observation(
                patient_id=patient_id,
                code=obs["code"],
                value_num=obs.get("value_num"),
                value_text=obs.get("value_text"),
                taken_at=obs.get("taken_at") or occurred_at,
                source=source,
            )
        )
    return EncounterRepository(db).add(encounter)


def build_observation(
    *,
    patient_id: uuid.UUID,
    code: str,
    value_num: float | None,
    value_text: str | None,
    taken_at: datetime,
    source: str = "manual",
) -> models.Observation:
    """Validate against the catalog and construct an (unpersisted) observation."""
    obs_type = observation_catalog.validate(code, value_num, value_text)
    return models.Observation(
        patient_id=patient_id,
        code=code,
        value_num=value_num,
        value_text=value_text,
        unit=obs_type.unit,
        taken_at=taken_at,
        source=source,
    )


def add_observation(
    db: Session,
    encounter: models.Encounter,
    *,
    code: str,
    value_num: float | None,
    value_text: str | None,
    taken_at: datetime | None,
) -> models.Encounter:
    observation = build_observation(
        patient_id=encounter.patient_id,
        code=code,
        value_num=value_num,
        value_text=value_text,
        taken_at=taken_at or encounter.occurred_at,
        source=encounter.source,
    )
    encounter.observations.append(observation)
    return EncounterRepository(db).save(encounter)
