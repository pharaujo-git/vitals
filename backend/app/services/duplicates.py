"""Duplicate detection and resolution across source systems.

Heuristics stay deliberately simple and explainable: two records are
candidates when their normalized name and date of birth line up. Review is
human — a flag is merged or dismissed, never auto-resolved.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.repositories.duplicates import DuplicateRepository


def scan(db: Session) -> int:
    """Flag patient pairs that look like the same person. Returns new flag count."""
    repo = DuplicateRepository(db)
    patients = list(
        db.scalars(select(models.Patient).where(models.Patient.merged_into_id.is_(None)))
    )

    def norm(s: str) -> str:
        return s.strip().lower()

    created = 0
    by_key: dict[tuple, list[models.Patient]] = {}
    for p in patients:
        exact = ("exact", norm(p.first_name), norm(p.last_name), p.dob)
        initial = ("initial", norm(p.first_name)[:1], norm(p.last_name), p.dob)
        for key in (exact, initial):
            by_key.setdefault(key, []).append(p)

    seen_pairs: set[tuple] = set()
    for key, group in by_key.items():
        if len(group) < 2:
            continue
        kind = key[0]
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if a.id == b.id:
                    continue
                pair = tuple(sorted((str(a.id), str(b.id))))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                if repo.existing_pair(a.id, b.id) is not None:
                    continue
                reason = (
                    "Same name and date of birth"
                    if kind == "exact"
                    else "Same last name, first initial and date of birth"
                )
                if a.source != b.source:
                    reason += f" across sources ({a.source} / {b.source})"
                db.add(models.DuplicateFlag(patient_a_id=a.id, patient_b_id=b.id, reason=reason))
                created += 1
    db.commit()
    return created


def merge(db: Session, flag: models.DuplicateFlag) -> models.Patient:
    """Merge patient B into patient A: move clinical data, fill missing
    demographics, delete the duplicate record."""
    if flag.status != "pending":
        raise ValueError("This duplicate flag was already resolved")
    a, b = flag.patient_a, flag.patient_b

    db.execute(
        models.Encounter.__table__.update()
        .where(models.Encounter.patient_id == b.id)
        .values(patient_id=a.id)
    )
    db.execute(
        models.Observation.__table__.update()
        .where(models.Observation.patient_id == b.id)
        .values(patient_id=a.id)
    )
    db.execute(
        models.Appointment.__table__.update()
        .where(models.Appointment.patient_id == b.id)
        .values(patient_id=a.id)
    )

    for field in ("phone", "email", "address", "history"):
        if getattr(a, field) is None and getattr(b, field) is not None:
            setattr(a, field, getattr(b, field))

    # Resolve every other flag touching the absorbed record.
    others = db.scalars(
        select(models.DuplicateFlag).where(
            models.DuplicateFlag.id != flag.id,
            (models.DuplicateFlag.patient_a_id == b.id)
            | (models.DuplicateFlag.patient_b_id == b.id),
        )
    )
    now = datetime.now(timezone.utc)
    for other in others:
        other.status = "dismissed"
        other.resolved_at = now

    flag.status = "merged"
    flag.resolved_at = now
    b.merged_into_id = a.id
    db.commit()
    db.refresh(a)
    return a


def dismiss(db: Session, flag: models.DuplicateFlag) -> None:
    if flag.status != "pending":
        raise ValueError("This duplicate flag was already resolved")
    flag.status = "dismissed"
    flag.resolved_at = datetime.now(timezone.utc)
    db.commit()


def patient_summary(db: Session, patient: models.Patient) -> dict:
    """Consolidated view: which sources contributed, and the latest value
    of each observation across all of them."""
    source_rows = db.execute(
        select(models.Encounter.source, func.count(models.Encounter.id))
        .where(models.Encounter.patient_id == patient.id)
        .group_by(models.Encounter.source)
    ).all()
    obs_rows = db.execute(
        select(models.Observation.source, func.count(models.Observation.id))
        .where(models.Observation.patient_id == patient.id)
        .group_by(models.Observation.source)
    ).all()

    sources: dict[str, dict] = {}
    sources.setdefault(patient.source, {"encounters": 0, "observations": 0})
    for source, count in source_rows:
        sources.setdefault(source, {"encounters": 0, "observations": 0})["encounters"] = count
    for source, count in obs_rows:
        sources.setdefault(source, {"encounters": 0, "observations": 0})["observations"] = count

    latest: dict[str, models.Observation] = {}
    for obs in db.scalars(
        select(models.Observation)
        .where(models.Observation.patient_id == patient.id)
        .order_by(models.Observation.taken_at.desc())
    ):
        if obs.code not in latest:
            latest[obs.code] = obs

    return {
        "sources": [
            {"source": source, **counts} for source, counts in sorted(sources.items())
        ],
        "latest_observations": list(latest.values()),
        "pending_duplicates": DuplicateRepository(db).pending_for_patient(patient.id),
    }
