from datetime import date, datetime, time, timedelta

import pytest

from app.db import models
from app.services import appointments
from tests.conftest import make_patient, make_user


def _book(db, patient, clinician, day, start_hour, start_min, minutes):
    start = datetime.combine(day, time(start_hour, start_min)).astimezone()
    db.add(models.Appointment(
        patient_id=patient.id,
        clinician_id=clinician.id,
        start_at=start,
        end_at=start + timedelta(minutes=minutes),
        status="booked",
    ))
    db.commit()


def test_next_free_slot_skips_booked_time(db):
    clinician = make_user(db, "clinician")
    patient = make_patient(db)
    day = date.today() + timedelta(days=3)  # future day: clinic open is free
    _book(db, patient, clinician, day, 8, 0, 60)   # 08:00–09:00
    _book(db, patient, clinician, day, 9, 0, 30)   # 09:00–09:30

    start, end = appointments.find_next_free(
        db, clinician_id=clinician.id, duration_minutes=45, from_day=day
    )
    assert start.astimezone().hour == 9 and start.astimezone().minute == 30
    assert (end - start) == timedelta(minutes=45)


def test_next_free_slot_fits_gap_between_appointments(db):
    clinician = make_user(db, "clinician")
    patient = make_patient(db)
    day = date.today() + timedelta(days=3)
    _book(db, patient, clinician, day, 8, 0, 30)   # 08:00–08:30
    _book(db, patient, clinician, day, 9, 0, 60)   # 09:00–10:00

    start, _ = appointments.find_next_free(
        db, clinician_id=clinician.id, duration_minutes=30, from_day=day
    )
    assert start.astimezone().hour == 8 and start.astimezone().minute == 30  # uses the gap


def test_next_free_slot_rolls_to_next_day_when_full(db):
    clinician = make_user(db, "clinician")
    patient = make_patient(db)
    day = date.today() + timedelta(days=3)
    _book(db, patient, clinician, day, 8, 0, 600)  # 08:00–18:00, fully booked

    start, _ = appointments.find_next_free(
        db, clinician_id=clinician.id, duration_minutes=30, from_day=day
    )
    assert start.astimezone().date() == day + timedelta(days=1)


def test_invalid_duration_rejected(db):
    clinician = make_user(db, "clinician")
    with pytest.raises(ValueError, match="Duration"):
        appointments.find_next_free(
            db, clinician_id=clinician.id, duration_minutes=2, from_day=date.today()
        )
