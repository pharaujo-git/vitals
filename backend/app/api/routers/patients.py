import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.patients import PatientRepository
from app.services import consent as consent_service
from app.services import duplicates as duplicate_service
from app.services import patients as patient_service
from app.services import timeline as timeline_service
from app.services.consent import ConsentError

router = APIRouter(prefix="/patients", tags=["patients"])

can_view = require_roles("clinician", "front_desk")
can_edit = require_roles("clinician")
can_manage_consent = require_roles()


@router.get("", response_model=schemas.Page[schemas.PatientOut])
def list_patients(
    search: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    items, total = PatientRepository(db).page(search, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.post("", response_model=schemas.PatientOut, status_code=201)
def create_patient(
    body: schemas.PatientInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    try:
        patient = patient_service.create_patient(
            db,
            first_name=body.first_name,
            last_name=body.last_name,
            dob=body.dob,
            sex=body.sex,
            phone=body.phone,
            email=body.email,
            address=body.address,
            history=body.history,
            mrn=body.mrn,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "patient.created", entity_type="patient", entity_id=patient.id)
    return patient


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_view),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    audit(db, user, "patient.viewed", entity_type="patient", entity_id=patient.id)
    return patient


@router.get("/{patient_id}/summary", response_model=schemas.PatientSummaryOut)
def patient_summary(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_view),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    summary = duplicate_service.patient_summary(db, patient)
    return schemas.PatientSummaryOut(
        sources=[schemas.SourceContribution(**s) for s in summary["sources"]],
        latest_observations=[
            schemas.ObservationOut.model_validate(o) for o in summary["latest_observations"]
        ],
        pending_duplicates=summary["pending_duplicates"],
    )


@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(
    patient_id: uuid.UUID,
    body: schemas.PatientInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_edit),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    try:
        patient = patient_service.update_patient(
            db,
            patient,
            first_name=body.first_name,
            last_name=body.last_name,
            dob=body.dob,
            sex=body.sex,
            phone=body.phone,
            email=body.email,
            address=body.address,
            history=body.history,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "patient.updated", entity_type="patient", entity_id=patient.id)
    return patient


@router.get("/{patient_id}/timeline", response_model=schemas.Page[schemas.TimelineEventOut])
def patient_timeline(
    patient_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("clinician")),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    events = timeline_service.build(db, patient_id)
    window = events[offset : offset + limit]
    return schemas.page(
        [schemas.TimelineEventOut(**vars(e)) for e in window], len(events), limit, offset
    )


@router.get("/{patient_id}/consent", response_model=schemas.ConsentOut)
def get_consent(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: models.User = Depends(can_manage_consent),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    return consent_service.describe_rules(db, patient)


@router.put("/{patient_id}/consent", response_model=schemas.ConsentOut)
def update_consent(
    patient_id: uuid.UUID,
    body: schemas.ConsentInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage_consent),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.update_rules(
            db,
            patient,
            restricted=body.restricted,
            grants=[g.model_dump() for g in body.grants],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "consent.updated", entity_type="patient", entity_id=patient.id,
          detail={"restricted": body.restricted, "grants": len(body.grants)})
    return consent_service.describe_rules(db, patient)
