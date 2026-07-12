import base64

import pytest

from app.repositories.messages import MessageRepository
from app.services import messages
from tests.conftest import make_patient, make_user


def send_simple(db, sender, recipients, **overrides):
    return messages.send(
        db, sender,
        recipient_ids=[r.id for r in recipients],
        subject=overrides.get("subject", "Hello"),
        body=overrides.get("body", "Body"),
        patient_id=overrides.get("patient_id"),
        parent_id=overrides.get("parent_id"),
        attachments=overrides.get("attachments"),
    )


def test_multi_recipient_fan_out(db):
    sender = make_user(db)
    a, b = make_user(db, "front_desk"), make_user(db, "manager")
    sent = send_simple(db, sender, [a, b])
    assert len(sent) == 2
    assert {m.recipient_id for m in sent} == {a.id, b.id}
    # each copy is its own conversation
    assert sent[0].root_id != sent[1].root_id


def test_reply_stays_in_thread_and_inherits_patient(db):
    sender = make_user(db)
    recipient = make_user(db, "front_desk")
    patient = make_patient(db)
    [original] = send_simple(db, sender, [recipient], patient_id=patient.id)

    [reply] = send_simple(db, recipient, [sender], parent_id=original.id)
    assert reply.root_id == original.root_id
    assert reply.patient_id == patient.id

    thread = MessageRepository(db).thread(original.root_id, sender.id)
    assert [m.id for m in thread] == [original.id, reply.id]


def test_open_thread_marks_read_and_unread_count(db):
    sender = make_user(db)
    recipient = make_user(db, "front_desk")
    [message] = send_simple(db, sender, [recipient])
    repo = MessageRepository(db)
    assert repo.unread_count(recipient.id) == 1

    messages.open_thread(db, recipient, message)
    assert repo.unread_count(recipient.id) == 0


def test_outsider_cannot_open_thread(db):
    sender = make_user(db)
    recipient = make_user(db, "front_desk")
    [message] = send_simple(db, sender, [recipient])
    with pytest.raises(PermissionError):
        messages.open_thread(db, make_user(db, "manager"), message)


def test_archive_hides_from_unread_and_only_recipient_may(db):
    sender = make_user(db)
    recipient = make_user(db, "front_desk")
    [message] = send_simple(db, sender, [recipient])

    with pytest.raises(PermissionError):
        messages.set_archived(db, sender, message, True)

    messages.set_archived(db, recipient, message, True)
    repo = MessageRepository(db)
    assert repo.unread_count(recipient.id) == 0
    items, total = repo.inbox(recipient.id, False, archived=True, limit=10, offset=0)
    assert total == 1


def test_attachment_validation(db):
    sender = make_user(db)
    recipient = make_user(db, "front_desk")
    good = {"filename": "n.txt", "content_type": "text/plain",
            "data_base64": base64.b64encode(b"hi").decode()}

    [message] = send_simple(db, sender, [recipient], attachments=[good])
    assert message.attachments[0].size == 2

    with pytest.raises(ValueError, match="Unsupported attachment type"):
        send_simple(db, sender, [recipient],
                    attachments=[{**good, "content_type": "application/x-sh"}])
    with pytest.raises(ValueError, match="not valid base64"):
        send_simple(db, sender, [recipient], attachments=[{**good, "data_base64": "!!!"}])
    with pytest.raises(ValueError, match="At most 3"):
        send_simple(db, sender, [recipient], attachments=[good] * 4)


def test_self_send_rejected(db):
    sender = make_user(db)
    with pytest.raises(ValueError, match="yourself"):
        send_simple(db, sender, [sender])
