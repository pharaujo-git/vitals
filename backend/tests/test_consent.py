import pytest

from app.db import models
from app.services import consent
from tests.conftest import make_patient, make_user


def test_open_record_accessible_to_all(db):
    patient = make_patient(db)
    assert consent.can_access(db, make_user(db, "front_desk"), patient)


def test_restricted_denies_and_audits(db):
    patient = make_patient(db, restricted=True)
    clinician = make_user(db, "clinician")

    with pytest.raises(consent.ConsentError):
        consent.ensure_access(db, clinician, patient)

    denial = db.query(models.AuditLog).filter_by(action="access.denied").one()
    assert denial.entity_id == str(patient.id)
    assert denial.user_email == clinician.email


def test_role_and_user_grants(db):
    patient = make_patient(db, restricted=True)
    clinician = make_user(db, "clinician")
    front = make_user(db, "front_desk")

    consent.update_rules(
        db, patient, restricted=True,
        grants=[{"grantee_type": "role", "grantee": "clinician"},
                {"grantee_type": "user", "grantee": front.email}],
    )

    assert consent.can_access(db, clinician, patient)
    assert consent.can_access(db, front, patient)
    assert not consent.can_access(db, make_user(db, "manager"), patient)


def test_admin_always_allowed(db):
    patient = make_patient(db, restricted=True)
    assert consent.can_access(db, make_user(db, "admin"), patient)


def test_unknown_grant_rejected(db):
    patient = make_patient(db)
    with pytest.raises(ValueError, match="Unknown role"):
        consent.update_rules(db, patient, restricted=True,
                             grants=[{"grantee_type": "role", "grantee": "superuser"}])
    with pytest.raises(ValueError, match="No user with email"):
        consent.update_rules(db, patient, restricted=True,
                             grants=[{"grantee_type": "user", "grantee": "ghost@none.test"}])
