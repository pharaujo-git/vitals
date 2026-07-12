import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.duplicates import DuplicateRepository
from app.services import duplicates as duplicate_service

router = APIRouter(prefix="/duplicates", tags=["duplicates"])

can_review = require_roles("clinician")


@router.post("/scan", response_model=schemas.ScanResult)
def scan(
    db: Session = Depends(get_db),
    user: models.User = Depends(can_review),
):
    new_flags = duplicate_service.scan(db)
    audit(db, user, "duplicates.scanned", detail={"newFlags": new_flags})
    return schemas.ScanResult(new_flags=new_flags)


@router.get("", response_model=schemas.Page[schemas.DuplicateFlagOut])
def list_flags(
    status: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_review),
):
    items, total = DuplicateRepository(db).page(status, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.post("/{flag_id}/merge", response_model=schemas.DuplicateFlagOut)
def merge(
    flag_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_review),
):
    flag = DuplicateRepository(db).get(flag_id)
    if flag is None:
        raise HTTPException(404, "Duplicate flag not found")
    absorbed_id = flag.patient_b_id
    try:
        survivor = duplicate_service.merge(db, flag)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "patients.merged", entity_type="patient", entity_id=survivor.id,
          detail={"absorbed": str(absorbed_id)})
    return DuplicateRepository(db).get(flag_id)


@router.post("/{flag_id}/dismiss", response_model=schemas.DuplicateFlagOut)
def dismiss(
    flag_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_review),
):
    flag = DuplicateRepository(db).get(flag_id)
    if flag is None:
        raise HTTPException(404, "Duplicate flag not found")
    try:
        duplicate_service.dismiss(db, flag)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "duplicates.dismissed", entity_type="duplicate", entity_id=flag.id)
    return flag
