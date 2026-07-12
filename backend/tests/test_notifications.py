from app.repositories.notifications import NotificationRepository
from app.services.notifications import notify
from app.services import risk
from tests.conftest import add_observation, make_patient, make_user


def test_notify_and_read_lifecycle(db):
    user = make_user(db)
    notify(db, user.id, "appointment", "New appointment booked", body="Jane · 9:00", link="/appointments")
    repo = NotificationRepository(db)
    assert repo.unread_count(user.id) == 1
    items, total = repo.page(user.id, limit=10, offset=0)
    assert total == 1
    assert items[0].link == "/appointments"

    repo.mark_all_read(user.id)
    assert repo.unread_count(user.id) == 0


def test_fingerprint_moves_on_new_notification(db):
    user = make_user(db)
    repo = NotificationRepository(db)
    before = repo.fingerprint(user.id)
    notify(db, user.id, "risk", "High risk: Test")
    assert repo.fingerprint(user.id) != before


def test_score_patient_matches_rule_engine(db):
    patient = make_patient(db)
    add_observation(db, patient, "bp_systolic", 185)
    add_observation(db, patient, "bp_diastolic", 110)
    add_observation(db, patient, "spo2", 90)

    score, level, reasons = risk.score_patient(db, patient)
    assert level == "high"
    assert score >= 6
    assert any("185" in reason for reason in reasons)
