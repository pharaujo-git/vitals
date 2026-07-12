from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import get_current_user
from app.db import models
from app.db.session import get_db
from app.repositories.notifications import NotificationRepository

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=schemas.Page[schemas.NotificationOut])
def list_notifications(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    items, total = NotificationRepository(db).page(user.id, limit, offset)
    return schemas.page(items, total, limit, offset)


@router.get("/unread-count", response_model=schemas.UnreadCount)
def unread_count(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return schemas.UnreadCount(count=NotificationRepository(db).unread_count(user.id))


@router.post("/read-all", status_code=204)
def mark_all_read(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    NotificationRepository(db).mark_all_read(user.id)
