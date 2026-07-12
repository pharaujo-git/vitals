import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.clinical import ClinicalListRepository
from app.repositories.patients import PatientRepository
from app.services import consent as consent_service
from app.services.consent import ConsentError

router = APIRouter(tags=["clinical-lists"])

can_edit = require_roles("clinician")

PROBLEM_STATUSES = ("active", "resolved")
ALLERGY_SEVERITIES = ("mild", "moderate", "severe")


def _checked_patient(db: Session, user: models.User, patient_id: uuid.UUID) -> models.Patient:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    return patient


@router.get("/patients/{patient_id}/clinical-lists", response_model=schemas.ClinicalListsOut)
def clinical_lists(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    _checked_patient(db, user, patient_id)
    repo = ClinicalListRepository(db)
    return schemas.ClinicalListsOut(
        problems=[schemas.ProblemOut.model_validate(p) for p in repo.problems(patient_id)],
        medications=[schemas.MedicationOut.model_validate(m) for m in repo.medications(patient_id)],
        allergies=[schemas.AllergyOut.model_validate(a) for a in repo.allergies(patient_id)],
    )


@router.post("/patients/{patient_id}/problems", response_model=schemas.ProblemOut, status_code=201)
def add_problem(
    patient_id: uuid.UUID,
    body: schemas.ProblemInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    _checked_patient(db, user, patient_id)
    if body.status not in PROBLEM_STATUSES:
        raise HTTPException(400, f"Status must be one of: {', '.join(PROBLEM_STATUSES)}")
    problem = ClinicalListRepository(db).add(
        models.Problem(patient_id=patient_id, **body.model_dump())
    )
    audit(db, user, "problem.added", entity_type="patient", entity_id=patient_id,
          detail={"description": body.description})
    return problem


@router.put("/problems/{problem_id}", response_model=schemas.ProblemOut)
def update_problem(
    problem_id: uuid.UUID,
    body: schemas.ProblemInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    repo = ClinicalListRepository(db)
    problem = repo.get_problem(problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    _checked_patient(db, user, problem.patient_id)
    if body.status not in PROBLEM_STATUSES:
        raise HTTPException(400, f"Status must be one of: {', '.join(PROBLEM_STATUSES)}")
    problem.description = body.description
    problem.icd_code = body.icd_code
    problem.status = body.status
    problem.onset_date = body.onset_date
    repo.save(problem)
    audit(db, user, "problem.updated", entity_type="patient", entity_id=problem.patient_id,
          detail={"description": body.description, "status": body.status})
    return problem


@router.delete("/problems/{problem_id}", status_code=204)
def delete_problem(
    problem_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    repo = ClinicalListRepository(db)
    problem = repo.get_problem(problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    _checked_patient(db, user, problem.patient_id)
    audit(db, user, "problem.removed", entity_type="patient", entity_id=problem.patient_id,
          detail={"description": problem.description})
    repo.delete(problem)


@router.post(
    "/patients/{patient_id}/medications", response_model=schemas.MedicationOut, status_code=201
)
def add_medication(
    patient_id: uuid.UUID,
    body: schemas.MedicationInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    _checked_patient(db, user, patient_id)
    medication = ClinicalListRepository(db).add(
        models.Medication(patient_id=patient_id, **body.model_dump())
    )
    audit(db, user, "medication.added", entity_type="patient", entity_id=patient_id,
          detail={"name": body.name})
    return medication


@router.put("/medications/{medication_id}", response_model=schemas.MedicationOut)
def update_medication(
    medication_id: uuid.UUID,
    body: schemas.MedicationInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    repo = ClinicalListRepository(db)
    medication = repo.get_medication(medication_id)
    if medication is None:
        raise HTTPException(404, "Medication not found")
    _checked_patient(db, user, medication.patient_id)
    medication.name = body.name
    medication.dose = body.dose
    medication.frequency = body.frequency
    medication.active = body.active
    medication.started_date = body.started_date
    repo.save(medication)
    audit(db, user, "medication.updated", entity_type="patient", entity_id=medication.patient_id,
          detail={"name": body.name, "active": body.active})
    return medication


@router.delete("/medications/{medication_id}", status_code=204)
def delete_medication(
    medication_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    repo = ClinicalListRepository(db)
    medication = repo.get_medication(medication_id)
    if medication is None:
        raise HTTPException(404, "Medication not found")
    _checked_patient(db, user, medication.patient_id)
    audit(db, user, "medication.removed", entity_type="patient", entity_id=medication.patient_id,
          detail={"name": medication.name})
    repo.delete(medication)


@router.post("/patients/{patient_id}/allergies", response_model=schemas.AllergyOut, status_code=201)
def add_allergy(
    patient_id: uuid.UUID,
    body: schemas.AllergyInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    _checked_patient(db, user, patient_id)
    if body.severity not in ALLERGY_SEVERITIES:
        raise HTTPException(400, f"Severity must be one of: {', '.join(ALLERGY_SEVERITIES)}")
    allergy = ClinicalListRepository(db).add(
        models.Allergy(patient_id=patient_id, **body.model_dump())
    )
    audit(db, user, "allergy.added", entity_type="patient", entity_id=patient_id,
          detail={"substance": body.substance, "severity": body.severity})
    return allergy


@router.delete("/allergies/{allergy_id}", status_code=204)
def delete_allergy(
    allergy_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    repo = ClinicalListRepository(db)
    allergy = repo.get_allergy(allergy_id)
    if allergy is None:
        raise HTTPException(404, "Allergy not found")
    _checked_patient(db, user, allergy.patient_id)
    audit(db, user, "allergy.removed", entity_type="patient", entity_id=allergy.patient_id,
          detail={"substance": allergy.substance})
    repo.delete(allergy)
