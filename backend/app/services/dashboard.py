"""Population health measures for the dashboard (read-model service)."""

from datetime import date, datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.services import risk

AGE_BANDS = ((0, 17, "0–17"), (18, 39, "18–39"), (40, 64, "40–64"), (65, 200, "65+"))


def _month_trend(db: Session, column, months: int = 6) -> list[dict]:
    """Counts per calendar month for the trailing window, zero-filled."""
    start = (datetime.now(timezone.utc) - timedelta(days=31 * months)).replace(day=1)
    rows = db.execute(
        select(column).where(column >= start)
    ).scalars().all()
    counts: dict[tuple[int, int], int] = {}
    for value in rows:
        counts[(value.year, value.month)] = counts.get((value.year, value.month), 0) + 1

    trend = []
    cursor = date(start.year, start.month, 1)
    today = date.today()
    while cursor <= today:
        trend.append(
            {"year": cursor.year, "month": cursor.month, "count": counts.get((cursor.year, cursor.month), 0)}
        )
        cursor = date(cursor.year + (cursor.month // 12), (cursor.month % 12) + 1, 1)
    return trend


def summary(db: Session) -> dict:
    active = models.Patient.merged_into_id.is_(None)
    total_patients = db.scalar(select(func.count(models.Patient.id)).where(active)) or 0
    total_encounters = db.scalar(select(func.count(models.Encounter.id))) or 0
    total_observations = db.scalar(select(func.count(models.Observation.id))) or 0
    upcoming = (
        db.scalar(
            select(func.count(models.Appointment.id)).where(
                models.Appointment.status == "booked",
                models.Appointment.start_at >= datetime.now(timezone.utc),
            )
        )
        or 0
    )

    patients = db.execute(select(models.Patient.sex, models.Patient.dob, models.Patient.source).where(active)).all()
    sex_counts: dict[str, int] = {}
    band_counts: dict[str, int] = {label: 0 for _, _, label in AGE_BANDS}
    source_counts: dict[str, int] = {}
    if patients:
        df = pd.DataFrame(patients, columns=["sex", "dob", "source"])
        today = date.today()
        df["age"] = df["dob"].map(
            lambda dob: today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        )
        sex_counts = df["sex"].value_counts().to_dict()
        source_counts = df["source"].value_counts().to_dict()
        for low, high, label in AGE_BANDS:
            band_counts[label] = int(((df["age"] >= low) & (df["age"] <= high)).sum())

    flags = risk.compute_flags(db)
    return {
        "totals": {
            "patients": total_patients,
            "encounters": total_encounters,
            "observations": total_observations,
            "upcoming_appointments": upcoming,
        },
        "sex_breakdown": [{"label": k, "count": v} for k, v in sorted(sex_counts.items())],
        "age_bands": [{"label": label, "count": band_counts[label]} for _, _, label in AGE_BANDS],
        "source_breakdown": [{"label": k, "count": v} for k, v in sorted(source_counts.items())],
        "encounter_trend": _month_trend(db, models.Encounter.occurred_at),
        "observation_trend": _month_trend(db, models.Observation.taken_at),
        "risk_summary": {
            "high": sum(1 for f in flags if f.level == "high"),
            "moderate": sum(1 for f in flags if f.level == "moderate"),
            "flagged": len(flags),
        },
    }
