import base64
import binascii
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models
from app.repositories.messages import MessageRepository
from app.repositories.patients import PatientRepository
from app.repositories.users import UserRepository

ATTACHMENT_TYPES = {
    "image/png",
    "image/jpeg",
    "application/pdf",
    "text/plain",
    "text/csv",
}
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_ATTACHMENTS = 3


def _build_attachments(attachments: list[dict]) -> list[models.MessageAttachment]:
    if len(attachments) > MAX_ATTACHMENTS:
        raise ValueError(f"At most {MAX_ATTACHMENTS} attachments per message")
    built = []
    for spec in attachments:
        content_type = spec["content_type"]
        if content_type not in ATTACHMENT_TYPES:
            raise ValueError(f"Unsupported attachment type: {content_type}")
        try:
            data = base64.b64decode(spec["data_base64"], validate=True)
        except (binascii.Error, ValueError):
            raise ValueError(f"Attachment {spec['filename']} is not valid base64")
        if not data:
            raise ValueError(f"Attachment {spec['filename']} is empty")
        if len(data) > MAX_ATTACHMENT_SIZE:
            raise ValueError(f"Attachment {spec['filename']} exceeds the 5 MB limit")
        built.append(
            models.MessageAttachment(
                filename=spec["filename"],
                content_type=content_type,
                size=len(data),
                data=data,
            )
        )
    return built


def send(
    db: Session,
    sender: models.User,
    *,
    recipient_ids: list[uuid.UUID],
    subject: str,
    body: str,
    patient_id: uuid.UUID | None,
    parent_id: uuid.UUID | None,
    attachments: list[dict] | None = None,
) -> list[models.Message]:
    """Send to one or more recipients; each recipient gets their own copy and
    conversation (like BCC), except replies which stay in the parent thread."""
    repo = MessageRepository(db)
    if not recipient_ids:
        raise ValueError("Pick at least one recipient")
    if parent_id is not None and len(recipient_ids) > 1:
        raise ValueError("A reply goes to one recipient")

    recipients = []
    for recipient_id in dict.fromkeys(recipient_ids):  # dedupe, keep order
        recipient = UserRepository(db).get(recipient_id)
        if recipient is None:
            raise ValueError("Recipient not found")
        if recipient.id == sender.id:
            raise ValueError("You cannot send a message to yourself")
        recipients.append(recipient)

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

    sent = []
    for recipient in recipients:
        message_id = uuid.uuid4()
        message = models.Message(
            id=message_id,
            sender_id=sender.id,
            recipient_id=recipient.id,
            patient_id=patient_id,
            parent_id=parent_id,
            root_id=root_id or message_id,
            subject=subject.strip(),
            body=body,
            attachments=_build_attachments(attachments or []),
        )
        sent.append(repo.add(message))
    return sent


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


def set_archived(db: Session, user: models.User, message: models.Message, archived: bool) -> None:
    if message.recipient_id != user.id:
        raise PermissionError("Only the recipient can archive a message")
    message.archived_at = datetime.now(timezone.utc) if archived else None
    db.commit()
