import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db import models
from app.repositories.appointments import AppointmentRepository
from app.repositories.patients import PatientRepository
from app.repositories.users import UserRepository

STATUSES = ("booked", "cancelled", "completed")


def _validate_slot(
    repo: AppointmentRepository,
    clinician_id: uuid.UUID,
    start_at: datetime,
    end_at: datetime,
    exclude_id: uuid.UUID | None = None,
) -> None:
    if end_at <= start_at:
        raise ValueError("End time must be after the start time")
    clash = repo.overlapping(clinician_id, start_at, end_at, exclude_id)
    if clash is not None:
        raise ValueError("The clinician already has an appointment in that time slot")


def book(
    db: Session,
    *,
    patient_id: uuid.UUID,
    clinician_id: uuid.UUID,
    start_at: datetime,
    end_at: datetime,
    reason: str | None,
) -> models.Appointment:
    if PatientRepository(db).get(patient_id) is None:
        raise ValueError("Patient not found")
    clinician = UserRepository(db).get(clinician_id)
    if clinician is None or clinician.role not in ("clinician", "admin"):
        raise ValueError("Clinician not found")
    repo = AppointmentRepository(db)
    _validate_slot(repo, clinician_id, start_at, end_at)
    appointment = models.Appointment(
        patient_id=patient_id,
        clinician_id=clinician_id,
        start_at=start_at,
        end_at=end_at,
        reason=reason,
    )
    return repo.add(appointment)


def reschedule(
    db: Session,
    appointment: models.Appointment,
    *,
    clinician_id: uuid.UUID,
    start_at: datetime,
    end_at: datetime,
    reason: str | None,
) -> models.Appointment:
    if appointment.status == "cancelled":
        raise ValueError("A cancelled appointment cannot be moved; book a new one")
    clinician = UserRepository(db).get(clinician_id)
    if clinician is None or clinician.role not in ("clinician", "admin"):
        raise ValueError("Clinician not found")
    repo = AppointmentRepository(db)
    _validate_slot(repo, clinician_id, start_at, end_at, exclude_id=appointment.id)
    appointment.clinician_id = clinician_id
    appointment.start_at = start_at
    appointment.end_at = end_at
    appointment.reason = reason
    return repo.save(appointment)


def set_status(db: Session, appointment: models.Appointment, status: str) -> models.Appointment:
    if status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")
    appointment.status = status
    return AppointmentRepository(db).save(appointment)
