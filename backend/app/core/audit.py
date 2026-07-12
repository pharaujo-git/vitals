"""Cross-cutting audit trail: call audit(...) from controllers after a
sensitive view or change. Inserts are committed immediately so the trail
survives later request failures."""

import uuid

from sqlalchemy.orm import Session

from app.db import models


def audit(
    db: Session,
    user: models.User,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    detail: dict | None = None,
) -> None:
    entry = models.AuditLog(
        user_id=user.id,
        user_email=user.email,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        detail=detail,
    )
    db.add(entry)
    db.commit()
