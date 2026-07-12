import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import get_current_user, require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.appointments import AppointmentRepository
from app.repositories.users import UserRepository
from app.services import appointments as appointment_service

router = APIRouter(prefix="/appointments", tags=["appointments"])

can_manage = require_roles("front_desk", "clinician")


@router.get("/clinicians", response_model=list[schemas.ClinicianOut])
def list_clinicians(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return UserRepository(db).clinicians()


@router.get("", response_model=schemas.Page[schemas.AppointmentOut])
def list_appointments(
    day: date | None = None,
    clinician_id: uuid.UUID | None = Query(None, alias="clinicianId"),
    patient_id: uuid.UUID | None = Query(None, alias="patientId"),
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage),
):
    items, total = AppointmentRepository(db).page(day, clinician_id, patient_id, status, limit, offset)
    return schemas.page([schemas.AppointmentOut.from_orm_appointment(a) for a in items], total, limit, offset)


@router.post("", response_model=schemas.AppointmentOut, status_code=201)
def book_appointment(
    body: schemas.AppointmentInput,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage),
):
    try:
        appointment = appointment_service.book(
            db,
            patient_id=body.patient_id,
            clinician_id=body.clinician_id,
            start_at=body.start_at,
            end_at=body.end_at,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return schemas.AppointmentOut.from_orm_appointment(appointment)


@router.put("/{appointment_id}", response_model=schemas.AppointmentOut)
def reschedule_appointment(
    appointment_id: uuid.UUID,
    body: schemas.AppointmentInput,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage),
):
    appointment = AppointmentRepository(db).get(appointment_id)
    if appointment is None:
        raise HTTPException(404, "Appointment not found")
    try:
        appointment = appointment_service.reschedule(
            db,
            appointment,
            clinician_id=body.clinician_id,
            start_at=body.start_at,
            end_at=body.end_at,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return schemas.AppointmentOut.from_orm_appointment(appointment)


@router.post("/{appointment_id}/status", response_model=schemas.AppointmentOut)
def set_appointment_status(
    appointment_id: uuid.UUID,
    body: schemas.AppointmentStatusInput,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage),
):
    appointment = AppointmentRepository(db).get(appointment_id)
    if appointment is None:
        raise HTTPException(404, "Appointment not found")
    try:
        appointment = appointment_service.set_status(db, appointment, body.status)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return schemas.AppointmentOut.from_orm_appointment(appointment)
