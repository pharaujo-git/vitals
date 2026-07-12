"""Admin user management: roles, activation, administrative password resets."""

import secrets
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core import security
from app.core.security import ROLES
from app.db import models


def _revoke_sessions(db: Session, user_id) -> None:
    db.execute(
        update(models.RefreshToken)
        .where(models.RefreshToken.user_id == user_id,
               models.RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )


def set_role(db: Session, actor: models.User, target: models.User, role: str) -> models.User:
    if role not in ROLES:
        raise ValueError(f"Role must be one of: {', '.join(ROLES)}")
    if target.id == actor.id:
        raise ValueError("You cannot change your own role")
    target.role = role
    db.commit()
    db.refresh(target)
    return target


def set_active(db: Session, actor: models.User, target: models.User, active: bool) -> models.User:
    if target.id == actor.id and not active:
        raise ValueError("You cannot deactivate your own account")
    target.active = active
    if not active:
        _revoke_sessions(db, target.id)  # kill live sessions immediately
    db.commit()
    db.refresh(target)
    return target


def admin_reset_password(db: Session, actor: models.User, target: models.User) -> str:
    """Set a one-time temporary password (shown to the admin once) and sign
    the target out everywhere."""
    if target.id == actor.id:
        raise ValueError("Use the profile page to change your own password")
    temp_password = secrets.token_urlsafe(9)
    target.password_hash = security.hash_password(temp_password)
    target.failed_logins = 0
    target.locked_until = None
    _revoke_sessions(db, target.id)
    db.commit()
    return temp_password
