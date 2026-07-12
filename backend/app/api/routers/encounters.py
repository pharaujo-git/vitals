import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.encounters import EncounterRepository
from app.services import encounters as encounter_service
from app.services.observations import CATALOG

router = APIRouter(tags=["encounters"])

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
    _: models.User = Depends(can_view),
):
    items, total = EncounterRepository(db).page_for_patient(patient_id, limit, offset)
    return schemas.page([schemas.EncounterOut.from_orm_encounter(e) for e in items], total, limit, offset)


@router.post("/patients/{patient_id}/encounters", response_model=schemas.EncounterOut, status_code=201)
def create_encounter(
    patient_id: uuid.UUID,
    body: schemas.EncounterInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
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
    return schemas.EncounterOut.from_orm_encounter(encounter)


@router.post("/encounters/{encounter_id}/observations", response_model=schemas.EncounterOut)
def add_observation(
    encounter_id: uuid.UUID,
    body: schemas.ObservationInput,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_edit),
):
    encounter = EncounterRepository(db).get(encounter_id)
    if encounter is None:
        raise HTTPException(404, "Encounter not found")
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
    return schemas.EncounterOut.from_orm_encounter(encounter)
