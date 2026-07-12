import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.patients import PatientRepository
from app.services import patients as patient_service

router = APIRouter(prefix="/patients", tags=["patients"])

can_view = require_roles("clinician", "front_desk")
can_edit = require_roles("clinician")


@router.get("", response_model=schemas.Page[schemas.PatientOut])
def list_patients(
    search: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    items, total = PatientRepository(db).page(search, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.post("", response_model=schemas.PatientOut, status_code=201)
def create_patient(
    body: schemas.PatientInput,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_edit),
):
    try:
        return patient_service.create_patient(
            db,
            first_name=body.first_name,
            last_name=body.last_name,
            dob=body.dob,
            sex=body.sex,
            phone=body.phone,
            email=body.email,
            address=body.address,
            history=body.history,
            mrn=body.mrn,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    return patient


@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(
    patient_id: uuid.UUID,
    body: schemas.PatientInput,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_edit),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        return patient_service.update_patient(
            db,
            patient,
            first_name=body.first_name,
            last_name=body.last_name,
            dob=body.dob,
            sex=body.sex,
            phone=body.phone,
            email=body.email,
            address=body.address,
            history=body.history,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
