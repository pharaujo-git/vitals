import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models
from app.repositories.messages import MessageRepository
from app.repositories.patients import PatientRepository
from app.repositories.users import UserRepository


def send(
    db: Session,
    sender: models.User,
    *,
    recipient_id: uuid.UUID,
    subject: str,
    body: str,
    patient_id: uuid.UUID | None,
    parent_id: uuid.UUID | None,
) -> models.Message:
    repo = MessageRepository(db)
    recipient = UserRepository(db).get(recipient_id)
    if recipient is None:
        raise ValueError("Recipient not found")
    if recipient.id == sender.id:
        raise ValueError("You cannot send a message to yourself")
    if patient_id is not None and PatientRepository(db).get(patient_id) is None:
        raise ValueError("Linked patient not found")

    root_id = None
    if parent_id is not None:
        parent = repo.get(parent_id)
        if parent is None:
            raise ValueError("Message being replied to was not found")
        if sender.id not in (parent.sender_id, parent.recipient_id):
            raise ValueError("You are not part of that conversation")
        root_id = parent.root_id
        # A reply inherits the conversation's patient link unless overridden.
        if patient_id is None:
            patient_id = parent.patient_id

    message_id = uuid.uuid4()
    message = models.Message(
        id=message_id,
        sender_id=sender.id,
        recipient_id=recipient_id,
        patient_id=patient_id,
        parent_id=parent_id,
        root_id=root_id or message_id,
        subject=subject.strip(),
        body=body,
    )
    return repo.add(message)


def open_thread(db: Session, user: models.User, message: models.Message) -> list[models.Message]:
    """Return the conversation and mark the user's unread messages in it read."""
    if user.id not in (message.sender_id, message.recipient_id):
        raise PermissionError("You are not part of that conversation")
    thread = MessageRepository(db).thread(message.root_id, user.id)
    now = datetime.now(timezone.utc)
    dirty = False
    for item in thread:
        if item.recipient_id == user.id and item.read_at is None:
            item.read_at = now
            dirty = True
    if dirty:
        db.commit()
    return thread
