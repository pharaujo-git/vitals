from datetime import date, datetime, timedelta, timezone

from app.db import models
from app.services import risk
from tests.conftest import add_observation, make_patient


def flags_for(db, patient):
    return [f for f in risk.compute_flags(db) if f.patient.id == patient.id]


def test_hypertension_and_glucose_flag_with_reasons(db):
    patient = make_patient(db, dob=date(1980, 1, 1))
    add_observation(db, patient, "bp_systolic", 165)
    add_observation(db, patient, "glucose", 130)

    [flag] = flags_for(db, patient)
    assert flag.score == 5
    assert flag.level == "moderate"
    assert any("165" in r for r in flag.reasons)  # measured value is explained
    assert any("diabetic range" in r for r in flag.reasons)


def test_healthy_patient_not_flagged(db):
    patient = make_patient(db, dob=date(1990, 1, 1))
    add_observation(db, patient, "heart_rate", 70)
    add_observation(db, patient, "bp_systolic", 118)
    assert flags_for(db, patient) == []


def test_latest_value_wins(db):
    patient = make_patient(db, dob=date(1980, 1, 1))
    now = datetime.now(timezone.utc)
    add_observation(db, patient, "bp_systolic", 170, taken_at=now - timedelta(days=30))
    add_observation(db, patient, "bp_systolic", 120, taken_at=now)  # controlled now
    assert flags_for(db, patient) == []


def test_polypharmacy_and_chronic_condition_rules(db):
    patient = make_patient(db, dob=date(1980, 1, 1))
    add_observation(db, patient, "bp_systolic", 150)  # +2 baseline
    db.add(models.Problem(patient_id=patient.id, description="Type 2 diabetes", status="active"))
    for i in range(5):
        db.add(models.Medication(patient_id=patient.id, name=f"Drug {i}", active=True))
    db.commit()

    [flag] = flags_for(db, patient)
    assert any("Chronic condition" in r for r in flag.reasons)
    assert any("Polypharmacy: 5 active medications" in r for r in flag.reasons)
    assert flag.score == 4


def test_resolved_problems_and_stopped_meds_ignored(db):
    patient = make_patient(db, dob=date(1980, 1, 1))
    add_observation(db, patient, "bp_systolic", 150)
    db.add(models.Problem(patient_id=patient.id, description="Hypertension", status="resolved"))
    for i in range(5):
        db.add(models.Medication(patient_id=patient.id, name=f"Old {i}", active=False))
    db.commit()

    flags = flags_for(db, patient)
    assert flags == [] or all(
        "Chronic" not in r and "Polypharmacy" not in r for f in flags for r in f.reasons
    )
