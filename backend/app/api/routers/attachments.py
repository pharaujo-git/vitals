import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.attachments import AttachmentRepository
from app.repositories.patients import PatientRepository
from app.services import consent as consent_service
from app.services.consent import ConsentError

router = APIRouter(tags=["attachments"])

can_manage = require_roles("clinician")

ALLOWED_TYPES = {
    "image/png",
    "image/jpeg",
    "application/pdf",
    "application/dicom",
}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
KINDS = ("imaging", "document")


def _checked_patient(db: Session, user: models.User, patient_id: uuid.UUID) -> models.Patient:
    patient = PatientRepository(db).get(patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    try:
        consent_service.ensure_access(db, user, patient)
    except ConsentError as exc:
        raise HTTPException(403, str(exc))
    return patient


def _to_out(a: models.Attachment) -> schemas.AttachmentOut:
    return schemas.AttachmentOut(
        id=a.id,
        kind=a.kind,
        filename=a.filename,
        content_type=a.content_type,
        description=a.description,
        size=a.size,
        uploaded_by_name=a.uploader.display_name if a.uploader else None,
        created_at=a.created_at,
    )


@router.get("/patients/{patient_id}/attachments", response_model=list[schemas.AttachmentOut])
def list_attachments(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage),
):
    _checked_patient(db, user, patient_id)
    return [_to_out(a) for a in AttachmentRepository(db).for_patient(patient_id)]


@router.post(
    "/patients/{patient_id}/attachments", response_model=schemas.AttachmentOut, status_code=201
)
async def upload_attachment(
    patient_id: uuid.UUID,
    file: UploadFile = File(...),
    kind: str = Form("document"),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage),
):
    _checked_patient(db, user, patient_id)
    if kind not in KINDS:
        raise HTTPException(400, f"Kind must be one of: {', '.join(KINDS)}")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {content_type}. "
                                 f"Allowed: {', '.join(sorted(ALLOWED_TYPES))}")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "File exceeds the 10 MB limit")
    if not data:
        raise HTTPException(400, "File is empty")

    attachment = AttachmentRepository(db).add(
        models.Attachment(
            patient_id=patient_id,
            uploaded_by=user.id,
            kind=kind,
            filename=file.filename or "upload",
            content_type=content_type,
            description=description,
            size=len(data),
            data=data,
        )
    )
    audit(db, user, "attachment.uploaded", entity_type="patient", entity_id=patient_id,
          detail={"filename": attachment.filename, "kind": kind, "size": len(data)})
    return _to_out(attachment)


@router.get("/attachments/{attachment_id}/content")
def attachment_content(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage),
):
    attachment = AttachmentRepository(db).get(attachment_id)
    if attachment is None:
        raise HTTPException(404, "Attachment not found")
    _checked_patient(db, user, attachment.patient_id)
    audit(db, user, "attachment.viewed", entity_type="patient", entity_id=attachment.patient_id,
          detail={"filename": attachment.filename})
    return Response(
        attachment.data,
        media_type=attachment.content_type,
        headers={"Content-Disposition": f'inline; filename="{attachment.filename}"'},
    )


@router.delete("/attachments/{attachment_id}", status_code=204)
def delete_attachment(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_manage),
):
    repo = AttachmentRepository(db)
    attachment = repo.get(attachment_id)
    if attachment is None:
        raise HTTPException(404, "Attachment not found")
    _checked_patient(db, user, attachment.patient_id)
    audit(db, user, "attachment.removed", entity_type="patient", entity_id=attachment.patient_id,
          detail={"filename": attachment.filename})
    repo.delete(attachment)
