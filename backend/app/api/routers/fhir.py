import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.clinical import ClinicalListRepository
from app.repositories.observations import ObservationRepository
from app.repositories.patients import PatientRepository
from app.services import consent as consent_service
from app.services import fhir as fhir_service
from app.services.consent import ConsentError

router = APIRouter(tags=["fhir"])

can_export = require_roles("clinician")
can_import = require_roles()


@router.get("/patients/{patient_id}/fhir")
def export_patient_fhir(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_export),
):
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    observations = ObservationRepository(db).for_patient(patient_id)
    clinical = ClinicalListRepository(db)
    bundle = fhir_service.export_patient(
        patient,
        observations,
        problems=clinical.problems(patient_id),
        medications=clinical.medications(patient_id),
        allergies=clinical.allergies(patient_id),
    )
    audit(db, user, "patient.fhir_exported", entity_type="patient", entity_id=patient.id,
          detail={"observations": len(observations)})
    return bundle


@router.post("/fhir/import", response_model=schemas.ImportBatchOut, status_code=201)
def import_fhir(
    body: schemas.ImportTextInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_import),
):
    try:
        batch = fhir_service.import_resources(db, user, body.label, body.content)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "import.fhir", entity_type="import", entity_id=batch.id,
          detail={"imported": batch.imported_count, "errors": batch.error_count})
    return batch
