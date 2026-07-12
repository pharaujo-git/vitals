import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import get_current_user
from app.db import models
from app.db.session import get_db
from app.repositories.messages import MessageRepository
from app.repositories.users import UserRepository
from app.services import messages as message_service

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/recipients", response_model=list[schemas.RecipientOut])
def recipients(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return [u for u in UserRepository(db).all_users() if u.id != user.id]


@router.get("/unread-count", response_model=schemas.UnreadCount)
def unread_count(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return schemas.UnreadCount(count=MessageRepository(db).unread_count(user.id))


@router.get("/inbox", response_model=schemas.Page[schemas.MessageOut])
def inbox(
    unread: bool = False,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    items, total = MessageRepository(db).inbox(user.id, unread, limit, offset)
    return schemas.page([schemas.MessageOut.from_orm_message(m) for m in items], total, limit, offset)


@router.get("/sent", response_model=schemas.Page[schemas.MessageOut])
def sent(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    items, total = MessageRepository(db).sent(user.id, limit, offset)
    return schemas.page([schemas.MessageOut.from_orm_message(m) for m in items], total, limit, offset)


@router.post("", response_model=schemas.MessageOut, status_code=201)
def send_message(
    body: schemas.MessageInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    try:
        message = message_service.send(
            db,
            user,
            recipient_id=body.recipient_id,
            subject=body.subject,
            body=body.body,
            patient_id=body.patient_id,
            parent_id=body.parent_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "message.sent", entity_type="message", entity_id=message.id,
          detail={"recipientId": str(body.recipient_id),
                  **({"patientId": str(message.patient_id)} if message.patient_id else {})})
    return schemas.MessageOut.from_orm_message(message)


@router.get("/{message_id}/thread", response_model=list[schemas.MessageOut])
def thread(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    message = MessageRepository(db).get(message_id)
    if message is None:
        raise HTTPException(404, "Message not found")
    try:
        messages = message_service.open_thread(db, user, message)
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
    return [schemas.MessageOut.from_orm_message(m) for m in messages]
