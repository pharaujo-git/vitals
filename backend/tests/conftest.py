import os
import subprocess
import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core import security
from app.db import models
from app.db.session import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/vitals_test"
)


@pytest.fixture(scope="session")
def engine():
    subprocess.run(["createdb", "vitals_test"], capture_output=True)
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """Each test runs inside an outer transaction that is always rolled back;
    service-layer commits land on savepoints."""
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    outer.rollback()
    connection.close()


def make_user(db: Session, role: str = "clinician", **overrides) -> models.User:
    user = models.User(
        email=overrides.get("email", f"{uuid.uuid4().hex[:10]}@test.local"),
        password_hash=security.hash_password(overrides.get("password", "password123")),
        display_name=overrides.get("display_name", f"Test {role.title()}"),
        role=role,
    )
    db.add(user)
    db.commit()
    return user


def make_patient(db: Session, **overrides) -> models.Patient:
    patient = models.Patient(
        mrn=overrides.get("mrn", f"MRN-T{uuid.uuid4().hex[:8].upper()}"),
        first_name=overrides.get("first_name", "Pat"),
        last_name=overrides.get("last_name", "Tester"),
        dob=overrides.get("dob", date(1970, 1, 1)),
        sex=overrides.get("sex", "female"),
        source=overrides.get("source", "manual"),
        restricted=overrides.get("restricted", False),
    )
    db.add(patient)
    db.commit()
    return patient


def add_observation(
    db: Session, patient: models.Patient, code: str, value: float, **overrides
) -> models.Observation:
    encounter = models.Encounter(
        patient_id=patient.id,
        occurred_at=overrides.get("taken_at", datetime.now(timezone.utc)),
        encounter_type="visit",
        source="manual",
    )
    db.add(encounter)
    db.flush()
    observation = models.Observation(
        patient_id=patient.id,
        encounter_id=encounter.id,
        code=code,
        value_num=value,
        taken_at=overrides.get("taken_at", datetime.now(timezone.utc)),
        source="manual",
    )
    db.add(observation)
    db.commit()
    return observation
