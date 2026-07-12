"""Duplicate detection and resolution across source systems.

Heuristics stay deliberately explainable. Two exact tiers (name+DOB, and
first-initial+surname+DOB) are joined by two approximate tiers measured in
docs/EVALUATION.md: near-identical names on the same DOB (bounded edit
distance, catching typos that break the first initial) and identical names
with DOBs a few days apart (catching off-by-one date-of-birth keying).
Review is human — a flag is merged or dismissed, never auto-resolved.
"""

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.repositories.duplicates import DuplicateRepository
from app.services.matching import full_name_similar

DOB_WINDOW_DAYS = 31


def scan(db: Session, *, fuzzy: bool = True, dob_window_days: int = DOB_WINDOW_DAYS) -> int:
    """Flag patient pairs that look like the same person. Returns new flag
    count. `fuzzy` and `dob_window_days` gate the approximate tiers (the
    evaluation harness runs the baseline by turning them off)."""
    repo = DuplicateRepository(db)
    patients = list(
        db.scalars(select(models.Patient).where(models.Patient.merged_into_id.is_(None)))
    )

    def norm(s: str) -> str:
        return s.strip().lower()

    created = 0
    seen_pairs: set[tuple] = set()

    def flag(a: models.Patient, b: models.Patient, reason: str) -> None:
        nonlocal created
        pair = tuple(sorted((str(a.id), str(b.id))))
        if pair in seen_pairs:
            return
        seen_pairs.add(pair)
        if repo.existing_pair(a.id, b.id) is not None:
            return
        if a.source != b.source:
            reason += f" across sources ({a.source} / {b.source})"
        db.add(models.DuplicateFlag(patient_a_id=a.id, patient_b_id=b.id, reason=reason))
        created += 1

    # Tiers 1 & 2: exact keys.
    by_key: dict[tuple, list[models.Patient]] = {}
    for p in patients:
        exact = ("exact", norm(p.first_name), norm(p.last_name), p.dob)
        initial = ("initial", norm(p.first_name)[:1], norm(p.last_name), p.dob)
        for key in (exact, initial):
            by_key.setdefault(key, []).append(p)

    for key, group in by_key.items():
        if len(group) < 2:
            continue
        kind = key[0]
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if a.id == b.id:
                    continue
                flag(
                    a,
                    b,
                    "Same name and date of birth"
                    if kind == "exact"
                    else "Same last name, first initial and date of birth",
                )

    # Tier 3: near-identical full names on the same DOB (typos incl. first letter).
    if fuzzy:
        by_dob: dict[date, list[models.Patient]] = {}
        for p in patients:
            by_dob.setdefault(p.dob, []).append(p)
        for group in by_dob.values():
            if len(group) < 2:
                continue
            for i, a in enumerate(group):
                for b in group[i + 1 :]:
                    if full_name_similar(a.first_name, a.last_name, b.first_name, b.last_name):
                        flag(a, b, "Nearly identical name and same date of birth")

    # Tier 4: identical names with DOBs a few days apart (keying errors).
    if dob_window_days > 0:
        by_name: dict[tuple, list[models.Patient]] = {}
        for p in patients:
            by_name.setdefault((norm(p.first_name), norm(p.last_name)), []).append(p)
        for group in by_name.values():
            if len(group) < 2:
                continue
            for i, a in enumerate(group):
                for b in group[i + 1 :]:
                    delta = abs((a.dob - b.dob).days)
                    if 0 < delta <= dob_window_days:
                        flag(a, b, f"Same name with dates of birth {delta} day(s) apart")

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
