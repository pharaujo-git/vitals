"""Seed the database with synthetic demo data. No real patient data.

Usage:
    .venv/bin/python seed.py           # add users + synthetic population
    .venv/bin/python seed.py --fresh   # wipe clinical data first
"""

import random
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone

from app.core import security
from app.db import models
from app.db.session import SessionLocal

random.seed(42)

USERS = [
    ("admin@vitals.test", "Ada Admin", "admin"),
    ("chen@vitals.test", "Dr. Sarah Chen", "clinician"),
    ("okafor@vitals.test", "Dr. James Okafor", "clinician"),
    ("front@vitals.test", "Fran Alvarez", "front_desk"),
    ("manager@vitals.test", "Mia Manager", "manager"),
]
PASSWORD = "password123"

FIRST_F = ["Maria", "Ana", "Sofia", "Emma", "Olivia", "Ava", "Lena", "Rosa", "Nina", "Clara",
           "Lucia", "Elena", "Grace", "Ruth", "Vera", "Iris"]
FIRST_M = ["Carlos", "Joao", "Miguel", "James", "Liam", "Noah", "Oscar", "Hugo", "Leo", "Marco",
           "Pedro", "Andre", "Felix", "Victor", "Omar", "Ivan"]
LAST = ["Silva", "Santos", "Oliveira", "Souza", "Costa", "Pereira", "Almeida", "Nguyen", "Chen",
        "Garcia", "Martinez", "Johnson", "Smith", "Brown", "Miller", "Davis", "Khan", "Patel",
        "Kim", "Sato"]
REASONS = ["Annual physical", "Follow-up", "Hypertension check", "Diabetes management",
           "Medication review", "Chest pain evaluation", "Fatigue", "Back pain", "Headache",
           "Wellness visit"]
HISTORIES = [
    "Type 2 diabetes diagnosed 2019. Metformin 500mg.",
    "Essential hypertension. Lisinopril 10mg daily.",
    "Asthma since childhood; albuterol as needed.",
    "Hyperlipidemia. Statin therapy.",
    "No significant past medical history.",
    "Osteoarthritis of the knee. Prior appendectomy (2005).",
    "Seasonal allergies. No chronic medication.",
    "GERD, managed with omeprazole.",
]


def wipe(db):
    for table in (models.ImportIssue, models.ImportBatch, models.DuplicateFlag,
                  models.ConsentGrant, models.Observation, models.Encounter,
                  models.Appointment, models.Message, models.Problem,
                  models.Medication, models.Allergy, models.AuditLog):
        db.query(table).delete()
    db.query(models.Patient).delete()
    db.commit()
    print("clinical data wiped")


def get_or_create_users(db):
    users = {}
    for email, name, role in USERS:
        user = db.query(models.User).filter_by(email=email).first()
        if user is None:
            user = models.User(
                email=email,
                password_hash=security.hash_password(PASSWORD),
                display_name=name,
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        users[email] = user
    return users


def vitals_for(profile: str) -> dict[str, float]:
    """Plausible observation values by patient profile."""
    base = {
        "heart_rate": random.gauss(74, 9),
        "bp_systolic": random.gauss(121, 9),
        "bp_diastolic": random.gauss(78, 7),
        "temperature": round(random.gauss(36.7, 0.3), 1),
        "resp_rate": random.gauss(15, 2),
        "spo2": min(100, random.gauss(97.5, 1.2)),
        "bmi": random.gauss(25, 3),
        "glucose": random.gauss(92, 8),
    }
    if profile == "hypertensive":
        base["bp_systolic"] = random.gauss(155, 10)
        base["bp_diastolic"] = random.gauss(96, 6)
    elif profile == "diabetic":
        base["glucose"] = random.gauss(150, 20)
        base["hba1c"] = round(random.gauss(7.8, 0.9), 1)
        base["bmi"] = random.gauss(31, 3)
    elif profile == "copd":
        base["spo2"] = random.gauss(91, 2)
        base["resp_rate"] = random.gauss(21, 2)
    return {k: round(max(v, 1), 1) for k, v in base.items()}


def seed(db):
    users = get_or_create_users(db)
    clinicians = [users["chen@vitals.test"], users["okafor@vitals.test"]]
    now = datetime.now(timezone.utc)

    profiles = ["healthy"] * 30 + ["hypertensive"] * 12 + ["diabetic"] * 12 + ["copd"] * 6
    random.shuffle(profiles)

    patients = []
    for i, profile in enumerate(profiles):
        sex = random.choice(["female", "male"])
        first = random.choice(FIRST_F if sex == "female" else FIRST_M)
        last = random.choice(LAST)
        age = random.randint(19, 88) if profile != "healthy" else random.randint(5, 75)
        dob = date.today() - timedelta(days=int(age * 365.25 + random.randint(0, 300)))
        source = random.choices(["manual", "csv", "hl7"], weights=[70, 15, 15])[0]
        patient = models.Patient(
            mrn=f"MRN-{1000 + i}",
            first_name=first,
            last_name=last,
            dob=dob,
            sex=sex,
            phone=f"555-{random.randint(1000, 9999)}",
            email=f"{first.lower()}.{last.lower()}{i}@example.test",
            address=f"{random.randint(10, 999)} {random.choice(['Oak', 'Maple', 'Cedar', 'Palm', 'Pine'])} St",
            history=random.choice(HISTORIES),
            source=source,
        )
        db.add(patient)
        db.flush()
        patients.append((patient, profile))

        # Encounters with observations over the trailing six months.
        for _ in range(random.randint(1, 5)):
            occurred = now - timedelta(days=random.randint(0, 180), hours=random.randint(0, 8))
            encounter = models.Encounter(
                patient_id=patient.id,
                clinician_id=random.choice(clinicians).id if source == "manual" else None,
                occurred_at=occurred,
                encounter_type="visit" if source == "manual" else "imported",
                reason=random.choice(REASONS),
                source=source,
            )
            db.add(encounter)
            db.flush()
            for code, value in vitals_for(profile).items():
                db.add(models.Observation(
                    patient_id=patient.id,
                    encounter_id=encounter.id,
                    code=code,
                    value_num=value,
                    unit={"heart_rate": "bpm", "bp_systolic": "mmHg", "bp_diastolic": "mmHg",
                          "temperature": "°C", "resp_rate": "breaths/min", "spo2": "%",
                          "bmi": "kg/m²", "glucose": "mg/dL", "hba1c": "%"}[code],
                    taken_at=occurred,
                    source=source,
                ))

    # Clinical lists matching each patient's profile.
    profile_problems = {
        "hypertensive": ("Essential hypertension", "I10", ["Lisinopril 10 mg", "Amlodipine 5 mg"]),
        "diabetic": ("Type 2 diabetes mellitus", "E11.9", ["Metformin 500 mg", "Empagliflozin 10 mg"]),
        "copd": ("Chronic obstructive pulmonary disease", "J44.9", ["Tiotropium inhaler"]),
    }
    allergens = [("Penicillin", "Hives", "severe"), ("Sulfa drugs", "Rash", "moderate"),
                 ("Latex", "Contact dermatitis", "mild"), ("Peanuts", "Anaphylaxis", "severe")]
    for patient, profile in patients:
        if profile in profile_problems:
            description, icd, meds = profile_problems[profile]
            db.add(models.Problem(
                patient_id=patient.id, description=description, icd_code=icd,
                status="active", onset_date=date.today() - timedelta(days=random.randint(200, 3000)),
            ))
            for med in meds:
                parts = med.split(" ")
                db.add(models.Medication(
                    patient_id=patient.id, name=parts[0],
                    dose=" ".join(parts[1:]) or None, frequency="daily", active=True,
                    started_date=date.today() - timedelta(days=random.randint(30, 1000)),
                ))
        if random.random() < 0.25:
            substance, reaction, severity = random.choice(allergens)
            db.add(models.Allergy(
                patient_id=patient.id, substance=substance, reaction=reaction, severity=severity,
            ))
    # A few polypharmacy cases to exercise that risk rule.
    for patient, _ in random.sample(patients, 4):
        for med_name in ("Atorvastatin", "Omeprazole", "Aspirin", "Levothyroxine", "Sertraline"):
            db.add(models.Medication(
                patient_id=patient.id, name=med_name, dose="1 tab", frequency="daily", active=True,
            ))

    # Internal messages, including a patient-linked thread with a reply.
    def message(sender, recipient, subject, body, patient=None, parent=None, read=False):
        message_id = uuid.uuid4()
        msg = models.Message(
            id=message_id,
            sender_id=sender.id,
            recipient_id=recipient.id,
            patient_id=patient.id if patient else None,
            parent_id=parent.id if parent else None,
            root_id=parent.root_id if parent else message_id,
            subject=subject,
            body=body,
            read_at=now if read else None,
        )
        db.add(msg)
        db.flush()
        return msg

    front, manager = users["front@vitals.test"], users["manager@vitals.test"]
    chen, okafor, admin = users["chen@vitals.test"], users["okafor@vitals.test"], users["admin@vitals.test"]
    linked_patient = patients[1][0]
    first_message = message(
        front, chen, "Reschedule request",
        f"{linked_patient.first_name} {linked_patient.last_name} asked to move Friday's visit to next week — any slot preference?",
        patient=linked_patient, read=True,
    )
    message(chen, front, "Re: Reschedule request",
            "Tuesday morning works, anything before 11.", patient=linked_patient,
            parent=first_message)
    message(manager, chen, "Monthly population review",
            "Could you glance at the new high-risk flags before Thursday's meeting?")
    message(admin, okafor, "HL7 feed cutover",
            "The external lab switches endpoints this weekend; expect a test batch on Monday.")
    message(okafor, front, "Out Thursday afternoon",
            "Please avoid booking me after 1pm this Thursday.")

    # A couple of cross-source duplicate candidates for the review workflow.
    for patient, _ in random.sample(patients, 2):
        twin = models.Patient(
            mrn=f"MRN-X{random.randint(100, 999)}",
            first_name=patient.first_name,
            last_name=patient.last_name,
            dob=patient.dob,
            sex=patient.sex,
            source="hl7" if patient.source != "hl7" else "csv",
        )
        db.add(twin)
        db.flush()
        encounter = models.Encounter(
            patient_id=twin.id,
            occurred_at=now - timedelta(days=random.randint(1, 30)),
            encounter_type="imported",
            reason="External lab feed",
            source=twin.source,
        )
        db.add(encounter)
        db.flush()
        db.add(models.Observation(
            patient_id=twin.id, encounter_id=encounter.id, code="glucose",
            value_num=round(random.gauss(120, 15), 1), unit="mg/dL",
            taken_at=encounter.occurred_at, source=twin.source,
        ))

    # One restricted record to demo consent rules.
    restricted_patient = patients[0][0]
    restricted_patient.restricted = True
    db.add(models.ConsentGrant(
        patient_id=restricted_patient.id, grantee_type="role", grantee="clinician",
    ))

    # Appointments: today through next week, sequential slots per clinician.
    for clinician in clinicians:
        for day_offset in range(0, 7):
            day = date.today() + timedelta(days=day_offset)
            slot = datetime.combine(day, time(9, 0)).astimezone()
            for _ in range(random.randint(2, 5)):
                patient, _profile = random.choice(patients)
                duration = random.choice([30, 30, 45, 60])
                db.add(models.Appointment(
                    patient_id=patient.id,
                    clinician_id=clinician.id,
                    start_at=slot,
                    end_at=slot + timedelta(minutes=duration),
                    reason=random.choice(REASONS),
                    status="completed" if day_offset == 0 and slot.hour < 10 else "booked",
                ))
                slot += timedelta(minutes=duration + random.choice([0, 15, 30]))

    db.commit()
    print(f"seeded {len(patients)} patients (+2 duplicate twins), users:")
    for email, _, role in USERS:
        print(f"  {email} / {PASSWORD}  ({role})")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        if "--fresh" in sys.argv:
            wipe(session)
        seed(session)
    finally:
        session.close()
