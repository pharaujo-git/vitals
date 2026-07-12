import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db import models
from app.repositories import Repository


class AppointmentRepository(Repository):
    def get(self, appointment_id: uuid.UUID) -> models.Appointment | None:
        return self.db.get(models.Appointment, appointment_id)

    def page(
        self,
        day: date | None,
        clinician_id: uuid.UUID | None,
        patient_id: uuid.UUID | None,
        status: str | None,
        limit: int,
        offset: int,
    ):
        stmt = (
            select(models.Appointment)
            .options(joinedload(models.Appointment.patient), joinedload(models.Appointment.clinician))
            .order_by(models.Appointment.start_at)
        )
        if day is not None:
            start = datetime.combine(day, time.min).astimezone()
            end = datetime.combine(day, time.max).astimezone()
            stmt = stmt.where(models.Appointment.start_at >= start, models.Appointment.start_at <= end)
        if clinician_id is not None:
            stmt = stmt.where(models.Appointment.clinician_id == clinician_id)
        if patient_id is not None:
            stmt = stmt.where(models.Appointment.patient_id == patient_id)
        if status:
            stmt = stmt.where(models.Appointment.status == status)
        return self.paginate(stmt, limit, offset)

    def between(
        self, clinician_id: uuid.UUID | None, start: datetime, end: datetime
    ) -> list[models.Appointment]:
        stmt = (
            select(models.Appointment)
            .options(joinedload(models.Appointment.patient), joinedload(models.Appointment.clinician))
            .where(models.Appointment.start_at >= start, models.Appointment.start_at < end)
            .order_by(models.Appointment.start_at)
            .limit(500)
        )
        if clinician_id is not None:
            stmt = stmt.where(models.Appointment.clinician_id == clinician_id)
        return list(self.db.scalars(stmt))

    def booked_on_day(self, clinician_id: uuid.UUID, day: date) -> list[models.Appointment]:
        start = datetime.combine(day, time.min).astimezone()
        end = datetime.combine(day, time.max).astimezone()
        stmt = (
            select(models.Appointment)
            .where(
                models.Appointment.clinician_id == clinician_id,
                models.Appointment.status == "booked",
                models.Appointment.start_at >= start,
                models.Appointment.start_at <= end,
            )
            .order_by(models.Appointment.start_at)
        )
        return list(self.db.scalars(stmt))

    def overlapping(
        self,
        clinician_id: uuid.UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_id: uuid.UUID | None = None,
    ) -> models.Appointment | None:
        stmt = select(models.Appointment).where(
            models.Appointment.clinician_id == clinician_id,
            models.Appointment.status == "booked",
            models.Appointment.start_at < end_at,
            models.Appointment.end_at > start_at,
        )
        if exclude_id is not None:
            stmt = stmt.where(models.Appointment.id != exclude_id)
        return self.db.scalars(stmt).first()

    def add(self, appointment: models.Appointment) -> models.Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def save(self, appointment: models.Appointment) -> models.Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
