import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.encounters import EncounterRepository
from app.repositories.patients import PatientRepository
from app.services import consent as consent_service
from app.services import encounters as encounter_service
from app.services.consent import ConsentError
from app.services.observations import CATALOG

router = APIRouter(tags=["encounters"])


def _ensure_patient_access(db: Session, user: models.User, patient_id) -> None:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))

can_view = require_roles("clinician")
can_edit = require_roles("clinician")


@router.get("/observations/catalog", response_model=list[schemas.ObservationTypeOut])
def observation_catalog(_: models.User = Depends(can_view)):
    return list(CATALOG.values())


@router.get("/patients/{patient_id}/encounters", response_model=schemas.Page[schemas.EncounterOut])
def list_encounters(
    patient_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(can_view),
):
    _ensure_patient_access(db, user, patient_id)
    items, total = EncounterRepository(db).page_for_patient(patient_id, limit, offset)
    audit(db, user, "encounters.viewed", entity_type="patient", entity_id=patient_id)
    return schemas.page([schemas.EncounterOut.from_orm_encounter(e) for e in items], total, limit, offset)


@router.post("/patients/{patient_id}/encounters", response_model=schemas.EncounterOut, status_code=201)
def create_encounter(
    patient_id: uuid.UUID,
    body: schemas.EncounterInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    _ensure_patient_access(db, user, patient_id)
    try:
        encounter = encounter_service.create_encounter(
            db,
            patient_id=patient_id,
            clinician_id=user.id,
            occurred_at=body.occurred_at,
            encounter_type=body.encounter_type,
            reason=body.reason,
            notes=body.notes,
            observations=[o.model_dump() for o in body.observations],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "encounter.created", entity_type="encounter", entity_id=encounter.id,
          detail={"patientId": str(patient_id), "observations": len(encounter.observations)})
    return schemas.EncounterOut.from_orm_encounter(encounter)


@router.post("/encounters/{encounter_id}/observations", response_model=schemas.EncounterOut)
def add_observation(
    encounter_id: uuid.UUID,
    body: schemas.ObservationInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    encounter = EncounterRepository(db).get(encounter_id)
    if encounter is None:
        raise HTTPException(404, "Encounter not found")
    _ensure_patient_access(db, user, encounter.patient_id)
    try:
        encounter = encounter_service.add_observation(
            db,
            encounter,
            code=body.code,
            value_num=body.value_num,
            value_text=body.value_text,
            taken_at=body.taken_at,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "observation.added", entity_type="encounter", entity_id=encounter.id,
          detail={"code": body.code})
    return schemas.EncounterOut.from_orm_encounter(encounter)
