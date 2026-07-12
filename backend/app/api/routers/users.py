import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.repositories.users import UserRepository
from app.services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])

admin_only = require_roles()


def _get_target(db: Session, user_id: uuid.UUID) -> models.User:
    target = UserRepository(db).get(user_id)
    if target is None:
        raise HTTPException(404, "User not found")
    return target


@router.get("", response_model=schemas.Page[schemas.UserAdminOut])
def list_users(
    search: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(admin_only),
):
    items, total = UserRepository(db).page(search, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.post("/{user_id}/role", response_model=schemas.UserAdminOut)
def set_role(
    user_id: uuid.UUID,
    body: schemas.RoleInput,
    db: Session = Depends(get_db),
    actor: models.User = Depends(admin_only),
):
    target = _get_target(db, user_id)
    try:
        target = user_service.set_role(db, actor, target, body.role)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, actor, "user.role_changed", entity_type="user", entity_id=target.id,
          detail={"role": body.role})
    return target


@router.post("/{user_id}/active", response_model=schemas.UserAdminOut)
def set_active(
    user_id: uuid.UUID,
    body: schemas.ActiveInput,
    db: Session = Depends(get_db),
    actor: models.User = Depends(admin_only),
):
    target = _get_target(db, user_id)
    try:
        target = user_service.set_active(db, actor, target, body.active)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, actor, "user.activated" if body.active else "user.deactivated",
          entity_type="user", entity_id=target.id)
    return target


@router.post("/{user_id}/reset-password", response_model=schemas.TempPasswordOut)
def reset_password(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: models.User = Depends(admin_only),
):
    target = _get_target(db, user_id)
    try:
        temp_password = user_service.admin_reset_password(db, actor, target)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, actor, "user.password_reset_by_admin", entity_type="user", entity_id=target.id)
    return schemas.TempPasswordOut(temp_password=temp_password)
