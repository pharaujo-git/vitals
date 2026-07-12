import secrets
from datetime import date

from sqlalchemy.orm import Session

from app.db import models
from app.repositories.patients import PatientRepository

SEXES = ("female", "male", "other", "unknown")


def _generate_mrn(repo: PatientRepository) -> str:
    while True:
        mrn = f"MRN-{secrets.token_hex(4).upper()}"
        if repo.by_mrn(mrn) is None:
            return mrn


def _validate(dob: date, sex: str) -> None:
    if dob > date.today():
        raise ValueError("Date of birth cannot be in the future")
    if sex not in SEXES:
        raise ValueError(f"Sex must be one of: {', '.join(SEXES)}")


def create_patient(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    dob: date,
    sex: str,
    phone: str | None,
    email: str | None,
    address: str | None,
    history: str | None,
    mrn: str | None = None,
    source: str = "manual",
) -> models.Patient:
    _validate(dob, sex)
    repo = PatientRepository(db)
    if mrn:
        if repo.by_mrn(mrn) is not None:
            raise ValueError(f"A patient with identifier {mrn} already exists")
    else:
        mrn = _generate_mrn(repo)
    patient = models.Patient(
        mrn=mrn,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        dob=dob,
        sex=sex,
        phone=phone,
        email=email,
        address=address,
        history=history,
        source=source,
    )
    return repo.add(patient)


def update_patient(
    db: Session,
    patient: models.Patient,
    *,
    first_name: str,
    last_name: str,
    dob: date,
    sex: str,
    phone: str | None,
    email: str | None,
    address: str | None,
    history: str | None,
) -> models.Patient:
    _validate(dob, sex)
    patient.first_name = first_name.strip()
    patient.last_name = last_name.strip()
    patient.dob = dob
    patient.sex = sex
    patient.phone = phone
    patient.email = email
    patient.address = address
    patient.history = history
    return PatientRepository(db).save(patient)
