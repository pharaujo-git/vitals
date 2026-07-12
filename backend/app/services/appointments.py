import uuid
from datetime import date, datetime, time, timedelta

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


CLINIC_OPEN = time(8, 0)
CLINIC_CLOSE = time(18, 0)
SLOT_GRANULARITY_MINUTES = 15
SEARCH_DAYS = 14


def find_next_free(
    db: Session,
    *,
    clinician_id: uuid.UUID,
    duration_minutes: int,
    from_day: date,
) -> tuple[datetime, datetime]:
    """First gap of the requested length in the clinician's booked schedule,
    within clinic hours, scanning up to two weeks ahead."""
    if not 5 <= duration_minutes <= 240:
        raise ValueError("Duration must be between 5 and 240 minutes")
    repo = AppointmentRepository(db)
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=SLOT_GRANULARITY_MINUTES)
    now = datetime.now().astimezone()

    for offset in range(SEARCH_DAYS):
        day = from_day + timedelta(days=offset)
        open_at = datetime.combine(day, CLINIC_OPEN).astimezone()
        close_at = datetime.combine(day, CLINIC_CLOSE).astimezone()
        cursor = open_at
        if now > cursor:
            # Round the current time up to the next slot boundary.
            minutes_past = (now - open_at).total_seconds() / 60
            steps = int(minutes_past // SLOT_GRANULARITY_MINUTES) + 1
            cursor = open_at + steps * step
        booked = repo.booked_on_day(clinician_id, day)
        for appointment in booked:
            if cursor + duration <= appointment.start_at:
                return cursor, cursor + duration
            cursor = max(cursor, appointment.end_at)
        if cursor + duration <= close_at:
            return cursor, cursor + duration
    raise ValueError(f"No free slot of {duration_minutes} minutes in the next {SEARCH_DAYS} days")


def set_status(db: Session, appointment: models.Appointment, status: str) -> models.Appointment:
    if status not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")
    appointment.status = status
    return AppointmentRepository(db).save(appointment)
