"""Unified patient timeline: one chronological stream merging encounters,
appointments and clinical-list changes (read-model service)."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import models
from app.services.encounters import ENCOUNTER_TYPES  # noqa: F401  (documents the domain)


@dataclass
class TimelineEvent:
    kind: str  # encounter | appointment | problem | medication | allergy
    at: datetime
    title: str
    detail: str | None
    source: str | None


def build(db: Session, patient_id: uuid.UUID) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []

    encounters = db.scalars(
        select(models.Encounter)
        .options(joinedload(models.Encounter.clinician), joinedload(models.Encounter.observations))
        .where(models.Encounter.patient_id == patient_id)
    ).unique()
    for e in encounters:
        pieces = [f"{len(e.observations)} observation{'s' if len(e.observations) != 1 else ''}"]
        if e.clinician:
            pieces.append(e.clinician.display_name)
        events.append(
            TimelineEvent(
                kind="encounter",
                at=e.occurred_at,
                title=e.reason or e.encounter_type.replace("_", " ").capitalize(),
                detail=" · ".join(pieces),
                source=e.source,
            )
        )

    appointments = db.scalars(
        select(models.Appointment)
        .options(joinedload(models.Appointment.clinician))
        .where(models.Appointment.patient_id == patient_id)
    )
    for a in appointments:
        events.append(
            TimelineEvent(
                kind="appointment",
                at=a.start_at,
                title=a.reason or "Appointment",
                detail=f"{a.status} · {a.clinician.display_name}",
                source=None,
            )
        )

    for p in db.scalars(select(models.Problem).where(models.Problem.patient_id == patient_id)):
        events.append(
            TimelineEvent(
                kind="problem",
                at=p.created_at,
                title=p.description,
                detail=f"problem {p.status}" + (f" · ICD-10 {p.icd_code}" if p.icd_code else ""),
                source=None,
            )
        )

    for m in db.scalars(select(models.Medication).where(models.Medication.patient_id == patient_id)):
        detail = " · ".join(filter(None, (m.dose, m.frequency)))
        events.append(
            TimelineEvent(
                kind="medication",
                at=m.created_at,
                title=f"{m.name} {'started' if m.active else '(stopped)'}",
                detail=detail or None,
                source=None,
            )
        )

    for a in db.scalars(select(models.Allergy).where(models.Allergy.patient_id == patient_id)):
        events.append(
            TimelineEvent(
                kind="allergy",
                at=a.created_at,
                title=f"Allergy recorded: {a.substance}",
                detail=f"{a.severity}" + (f" · {a.reaction}" if a.reaction else ""),
                source=None,
            )
        )

    events.sort(key=lambda ev: ev.at, reverse=True)
    return events
