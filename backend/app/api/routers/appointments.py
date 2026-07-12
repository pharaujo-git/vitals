import uuid
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import get_current_user, require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.appointments import AppointmentRepository
from app.repositories.users import UserRepository
from app.services import appointments as appointment_service
from app.services.notifications import notify

router = APIRouter(prefix="/appointments", tags=["appointments"])

can_manage = require_roles("front_desk", "clinician")


@router.get("/clinicians", response_model=list[schemas.ClinicianOut])
def list_clinicians(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return UserRepository(db).clinicians()


@router.get("/week", response_model=list[schemas.AppointmentOut])
def week_appointments(
    start: date,
    clinician_id: uuid.UUID | None = Query(None, alias="clinicianId"),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage),
):
    """All appointments in the seven days from `start` (bounded, not a grid feed)."""
    window_start = datetime.combine(start, time.min).astimezone()
    window_end = window_start + timedelta(days=7)
    items = AppointmentRepository(db).between(clinician_id, window_start, window_end)
    return [schemas.AppointmentOut.from_orm_appointment(a) for a in items]


@router.get("/next-free", response_model=schemas.FreeSlotOut)
def next_free_slot(
    clinician_id: uuid.UUID = Query(alias="clinicianId"),
    duration: int = Query(30, ge=5, le=240),
    day: date | None = None,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage),
):
    try:
        start_at, end_at = appointment_service.find_next_free(
            db,
            clinician_id=clinician_id,
            duration_minutes=duration,
            from_day=day or date.today(),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return schemas.FreeSlotOut(start_at=start_at, end_at=end_at)


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
    user: models.User = Depends(can_manage),
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
    audit(db, user, "appointment.booked", entity_type="appointment", entity_id=appointment.id,
          detail={"patientId": str(body.patient_id)})
    _notify_clinician(db, user, appointment, "New appointment booked")
    return schemas.AppointmentOut.from_orm_appointment(appointment)


def _notify_clinician(db: Session, actor: models.User, appointment, title: str) -> None:
    """Tell the clinician when someone else changes their schedule."""
    if appointment.clinician_id == actor.id:
        return
    when = appointment.start_at.strftime("%b %-d, %-I:%M %p")
    patient = appointment.patient
    notify(
        db,
        appointment.clinician_id,
        "appointment",
        title,
        body=f"{patient.first_name} {patient.last_name} · {when}"
             + (f" · {appointment.reason}" if appointment.reason else ""),
        link="/appointments",
    )


@router.put("/{appointment_id}", response_model=schemas.AppointmentOut)
def reschedule_appointment(
    appointment_id: uuid.UUID,
    body: schemas.AppointmentInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage),
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
    audit(db, user, "appointment.moved", entity_type="appointment", entity_id=appointment.id)
    _notify_clinician(db, user, appointment, "Appointment moved")
    return schemas.AppointmentOut.from_orm_appointment(appointment)


@router.post("/{appointment_id}/status", response_model=schemas.AppointmentOut)
def set_appointment_status(
    appointment_id: uuid.UUID,
    body: schemas.AppointmentStatusInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage),
):
    appointment = AppointmentRepository(db).get(appointment_id)
    if appointment is None:
        raise HTTPException(404, "Appointment not found")
    try:
        appointment = appointment_service.set_status(db, appointment, body.status)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, f"appointment.{body.status}", entity_type="appointment", entity_id=appointment.id)
    if body.status == "cancelled":
        _notify_clinician(db, user, appointment, "Appointment cancelled")
    return schemas.AppointmentOut.from_orm_appointment(appointment)
