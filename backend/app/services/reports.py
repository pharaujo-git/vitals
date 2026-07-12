"""Cohort reports: filter the population, preview it, export it as CSV.

Column sets depend on the caller's role: administrators receive the
identified export; managers receive a de-identified one (no name, MRN,
date of birth or contact fields) — excluded fields are simply never
emitted.
"""

import csv
import io
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.services import risk

IDENTIFIED_COLUMNS = [
    "mrn", "first_name", "last_name", "dob", "age", "sex", "source",
    "phone", "email", "encounters", "risk_score", "risk_level", "risk_reasons",
]
DEIDENTIFIED_COLUMNS = [
    "age", "sex", "source", "encounters", "risk_score", "risk_level", "risk_reasons",
]


def columns_for(user: models.User) -> list[str]:
    return IDENTIFIED_COLUMNS if user.role == "admin" else DEIDENTIFIED_COLUMNS


def _age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def build_cohort(
    db: Session,
    *,
    min_age: int | None,
    max_age: int | None,
    sex: str | None,
    source: str | None,
    risk_level: str | None,
) -> list[dict]:
    stmt = select(models.Patient).where(models.Patient.merged_into_id.is_(None))
    today = date.today()
    if min_age is not None:
        stmt = stmt.where(models.Patient.dob <= today - timedelta(days=365.25 * min_age))
    if max_age is not None:
        stmt = stmt.where(models.Patient.dob > today - timedelta(days=365.25 * (max_age + 1)))
    if sex:
        stmt = stmt.where(models.Patient.sex == sex)
    if source:
        stmt = stmt.where(models.Patient.source == source)
    patients = list(db.scalars(stmt.order_by(models.Patient.last_name, models.Patient.first_name)))

    encounter_counts = dict(
        db.execute(
            select(models.Encounter.patient_id, func.count(models.Encounter.id)).group_by(
                models.Encounter.patient_id
            )
        ).all()
    )
    flags = {f.patient.id: f for f in risk.compute_flags(db)}

    rows = []
    for p in patients:
        flag = flags.get(p.id)
        if risk_level == "flagged" and flag is None:
            continue
        if risk_level in ("high", "moderate") and (flag is None or flag.level != risk_level):
            continue
        rows.append(
            {
                "patient_id": str(p.id),
                "mrn": p.mrn,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "dob": p.dob.isoformat(),
                "age": _age(p.dob),
                "sex": p.sex,
                "source": p.source,
                "phone": p.phone or "",
                "email": p.email or "",
                "encounters": encounter_counts.get(p.id, 0),
                "risk_score": flag.score if flag else 0,
                "risk_level": flag.level if flag else "none",
                "risk_reasons": "; ".join(flag.reasons) if flag else "",
            }
        )
    return rows


def to_csv(rows: list[dict], columns: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row[c] for c in columns])
    return buffer.getvalue()
