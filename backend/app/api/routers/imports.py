import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.imports import ImportRepository
from app.services import ingestion

router = APIRouter(prefix="/imports", tags=["imports"])

# Data integration is the administrator's job.
can_import = require_roles()


@router.get("", response_model=schemas.Page[schemas.ImportBatchOut])
def list_batches(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_import),
):
    items, total = ImportRepository(db).page(limit, offset)
    return schemas.page(items, total, limit, offset)


@router.get("/{batch_id}/issues", response_model=schemas.Page[schemas.ImportIssueOut])
def list_issues(
    batch_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_import),
):
    if ImportRepository(db).get(batch_id) is None:
        raise HTTPException(404, "Import batch not found")
    items, total = ImportRepository(db).issues_page(batch_id, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.post("/csv", response_model=schemas.ImportBatchOut, status_code=201)
def import_csv(
    body: schemas.ImportTextInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_import),
):
    try:
        batch = ingestion.import_csv(db, user, body.label, body.content)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "import.csv", entity_type="import", entity_id=batch.id,
          detail={"imported": batch.imported_count, "errors": batch.error_count})
    return batch


@router.post("/hl7", response_model=schemas.ImportBatchOut, status_code=201)
def import_hl7(
    body: schemas.ImportTextInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(can_import),
):
    try:
        batch = ingestion.import_hl7(db, user, body.label, body.content)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "import.hl7", entity_type="import", entity_id=batch.id,
          detail={"imported": batch.imported_count, "errors": batch.error_count})
    return batch
