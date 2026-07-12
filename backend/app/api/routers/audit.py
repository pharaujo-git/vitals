from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.audit import AuditRepository

router = APIRouter(prefix="/audit", tags=["audit"])

# The audit trail itself is admin-only (acting privacy officer).
can_view = require_roles()


@router.get("", response_model=schemas.Page[schemas.AuditEntryOut])
def list_audit_entries(
    action: str | None = None,
    entity_id: str | None = Query(None, alias="entityId"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    items, total = AuditRepository(db).page(action, entity_id, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.get("/actions", response_model=list[str])
def list_actions(
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    return AuditRepository(db).actions()
