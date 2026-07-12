import pytest

from app.db import models
from app.services import auth
from tests.conftest import make_user


def test_register_and_authenticate(db):
    user = auth.register(db, "new@test.local", "password123", "New User", "clinician")
    assert auth.authenticate(db, "NEW@test.local", "password123").id == user.id


def test_wrong_password_rejected(db):
    auth.register(db, "wrong@test.local", "password123", "User", "clinician")
    with pytest.raises(ValueError, match="Invalid email or password"):
        auth.authenticate(db, "wrong@test.local", "nope")


def test_admin_not_self_registerable(db):
    with pytest.raises(ValueError, match="Role must be one of"):
        auth.register(db, "evil@test.local", "password123", "Evil", "admin")


def test_refresh_rotation_happy_path(db):
    user = make_user(db)
    first = auth.issue_refresh_token(db, user)
    rotated_user, second = auth.rotate_refresh_token(db, first)
    assert rotated_user.id == user.id
    assert second != first
    # the new token keeps working
    _, third = auth.rotate_refresh_token(db, second)
    assert third != second


def test_reuse_detection_revokes_family(db):
    user = make_user(db)
    first = auth.issue_refresh_token(db, user)
    _, second = auth.rotate_refresh_token(db, first)

    with pytest.raises(ValueError, match="reuse detected"):
        auth.rotate_refresh_token(db, first)  # replaying the rotated token

    # collateral: the legitimate successor died with the family
    with pytest.raises(ValueError):
        auth.rotate_refresh_token(db, second)
    live = db.query(models.RefreshToken).filter_by(user_id=user.id, revoked_at=None).count()
    assert live == 0


def test_logout_revokes_without_theft_response(db):
    user = make_user(db)
    token = auth.issue_refresh_token(db, user)
    auth.revoke_refresh_token(db, token)
    with pytest.raises(ValueError, match="Session ended"):
        auth.rotate_refresh_token(db, token)
