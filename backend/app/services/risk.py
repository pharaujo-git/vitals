"""Explainable, rule-based patient risk flags.

Deliberately a transparent scoring model rather than a black box: each
rule contributes points and a human-readable reason carrying the measured
value, so every flag can be explained to the clinician reviewing it.
Rules run over each patient's latest value per observation code.
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

FLAG_THRESHOLD = 3
HIGH_THRESHOLD = 6


@dataclass
class RiskFlag:
    patient: models.Patient
    score: int
    level: str
    reasons: list[str]


def _age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _score_rules(age: int, latest: dict[str, float]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    def hit(points: int, reason: str) -> None:
        nonlocal score
        score += points
        reasons.append(f"{reason} (+{points})")

    systolic = latest.get("bp_systolic")
    if systolic is not None:
        if systolic >= 160:
            hit(3, f"Severely elevated systolic blood pressure: {systolic:g} mmHg")
        elif systolic >= 140:
            hit(2, f"Elevated systolic blood pressure: {systolic:g} mmHg")

    diastolic = latest.get("bp_diastolic")
    if diastolic is not None:
        if diastolic >= 100:
            hit(2, f"Severely elevated diastolic blood pressure: {diastolic:g} mmHg")
        elif diastolic >= 90:
            hit(1, f"Elevated diastolic blood pressure: {diastolic:g} mmHg")

    glucose = latest.get("glucose")
    if glucose is not None:
        if glucose >= 126:
            hit(2, f"Fasting glucose in diabetic range: {glucose:g} mg/dL")
        elif glucose >= 100:
            hit(1, f"Fasting glucose in prediabetic range: {glucose:g} mg/dL")

    hba1c = latest.get("hba1c")
    if hba1c is not None:
        if hba1c >= 8:
            hit(3, f"Poorly controlled HbA1c: {hba1c:g}%")
        elif hba1c >= 6.5:
            hit(2, f"HbA1c in diabetic range: {hba1c:g}%")
        elif hba1c >= 5.7:
            hit(1, f"HbA1c in prediabetic range: {hba1c:g}%")

    bmi = latest.get("bmi")
    if bmi is not None:
        if bmi >= 35:
            hit(2, f"BMI in obesity class II+: {bmi:g} kg/m²")
        elif bmi >= 30:
            hit(1, f"BMI in obesity range: {bmi:g} kg/m²")

    spo2 = latest.get("spo2")
    if spo2 is not None and spo2 < 92:
        hit(3, f"Low oxygen saturation: {spo2:g}%")

    heart_rate = latest.get("heart_rate")
    if heart_rate is not None:
        if heart_rate > 100:
            hit(1, f"Resting tachycardia: {heart_rate:g} bpm")
        elif heart_rate < 50:
            hit(1, f"Bradycardia: {heart_rate:g} bpm")

    if age >= 65:
        hit(1, f"Age {age}")

    return score, reasons


CHRONIC_KEYWORDS = (
    "diabetes", "hypertension", "copd", "heart failure", "coronary",
    "chronic kidney", "ckd", "asthma", "stroke", "atrial fibrillation",
)
POLYPHARMACY_THRESHOLD = 5


def _score_history(
    problems: list[models.Problem], medications: list[models.Medication]
) -> tuple[int, list[str]]:
    """History-based rules: chronic conditions on the problem list, polypharmacy."""
    score = 0
    reasons: list[str] = []

    chronic_hits = [
        p.description
        for p in problems
        if p.status == "active" and any(k in p.description.lower() for k in CHRONIC_KEYWORDS)
    ]
    for description in chronic_hits[:2]:  # capped so a long list can't dominate
        score += 1
        reasons.append(f"Chronic condition on problem list: {description} (+1)")

    active_meds = sum(1 for m in medications if m.active)
    if active_meds >= POLYPHARMACY_THRESHOLD:
        score += 1
        reasons.append(f"Polypharmacy: {active_meds} active medications (+1)")

    return score, reasons


def score_patient(db: Session, patient: models.Patient) -> tuple[int, str, list[str]]:
    """Score one patient (same rules as the population sweep). Returns
    (score, level, reasons) where level is none/moderate/high."""
    latest: dict[str, float] = {}
    observations = db.scalars(
        select(models.Observation)
        .where(
            models.Observation.patient_id == patient.id,
            models.Observation.value_num.is_not(None),
        )
        .order_by(models.Observation.taken_at)
    )
    for obs in observations:
        latest[obs.code] = float(obs.value_num)

    score, reasons = _score_rules(_age(patient.dob), latest)
    problems = list(db.scalars(select(models.Problem).where(models.Problem.patient_id == patient.id)))
    medications = list(
        db.scalars(select(models.Medication).where(models.Medication.patient_id == patient.id))
    )
    history_score, history_reasons = _score_history(problems, medications)
    score += history_score
    reasons.extend(history_reasons)

    level = "none"
    if score >= HIGH_THRESHOLD:
        level = "high"
    elif score >= FLAG_THRESHOLD:
        level = "moderate"
    return score, level, reasons


def compute_flags(db: Session) -> list[RiskFlag]:
    """Score every active patient; returns flags at or above the threshold,
    highest risk first."""
    obs_rows = db.execute(
        select(
            models.Observation.patient_id,
            models.Observation.code,
            models.Observation.value_num,
            models.Observation.taken_at,
        ).where(models.Observation.value_num.is_not(None))
    ).all()
    patients = {
        p.id: p
        for p in db.scalars(
            select(models.Patient).where(models.Patient.merged_into_id.is_(None))
        )
    }

    latest_by_patient: dict = {}
    if obs_rows:
        df = pd.DataFrame(obs_rows, columns=["patient_id", "code", "value", "taken_at"])
        df = df.sort_values("taken_at").groupby(["patient_id", "code"], sort=False).last()
        for (patient_id, code), row in df.iterrows():
            latest_by_patient.setdefault(patient_id, {})[code] = float(row["value"])

    problems_by_patient: dict = {}
    for problem in db.scalars(select(models.Problem)):
        problems_by_patient.setdefault(problem.patient_id, []).append(problem)
    medications_by_patient: dict = {}
    for medication in db.scalars(select(models.Medication)):
        medications_by_patient.setdefault(medication.patient_id, []).append(medication)

    flags: list[RiskFlag] = []
    for patient_id, patient in patients.items():
        latest = latest_by_patient.get(patient_id, {})
        score, reasons = _score_rules(_age(patient.dob), latest)
        history_score, history_reasons = _score_history(
            problems_by_patient.get(patient_id, []), medications_by_patient.get(patient_id, [])
        )
        score += history_score
        reasons.extend(history_reasons)
        if score >= FLAG_THRESHOLD:
            level = "high" if score >= HIGH_THRESHOLD else "moderate"
            flags.append(RiskFlag(patient=patient, score=score, level=level, reasons=reasons))

    flags.sort(key=lambda f: f.score, reverse=True)
    return flags
