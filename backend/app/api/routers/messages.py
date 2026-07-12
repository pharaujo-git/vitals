import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
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
    archived: bool = False,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    items, total = MessageRepository(db).inbox(user.id, unread, archived, limit, offset)
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


@router.post("", response_model=list[schemas.MessageOut], status_code=201)
def send_message(
    body: schemas.MessageInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    try:
        messages = message_service.send(
            db,
            user,
            recipient_ids=body.recipient_ids,
            subject=body.subject,
            body=body.body,
            patient_id=body.patient_id,
            parent_id=body.parent_id,
            attachments=[a.model_dump() for a in body.attachments],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    for message in messages:
        audit(db, user, "message.sent", entity_type="message", entity_id=message.id,
              detail={"recipientId": str(message.recipient_id),
                      **({"patientId": str(message.patient_id)} if message.patient_id else {}),
                      **({"attachments": len(message.attachments)} if message.attachments else {})})
    return [schemas.MessageOut.from_orm_message(m) for m in messages]


@router.post("/{message_id}/archive", status_code=204)
def archive_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _set_archived(db, user, message_id, True)


@router.post("/{message_id}/unarchive", status_code=204)
def unarchive_message(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    _set_archived(db, user, message_id, False)


def _set_archived(db: Session, user: models.User, message_id: uuid.UUID, archived: bool) -> None:
    message = MessageRepository(db).get(message_id)
    if message is None:
        raise HTTPException(404, "Message not found")
    try:
        message_service.set_archived(db, user, message, archived)
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.get("/attachments/{attachment_id}/content")
def message_attachment_content(
    attachment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    attachment = MessageRepository(db).get_attachment(attachment_id)
    if attachment is None:
        raise HTTPException(404, "Attachment not found")
    if user.id not in (attachment.message.sender_id, attachment.message.recipient_id):
        raise HTTPException(403, "You are not part of that conversation")
    return Response(
        attachment.data,
        media_type=attachment.content_type,
        headers={"Content-Disposition": f'inline; filename="{attachment.filename}"'},
    )


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
