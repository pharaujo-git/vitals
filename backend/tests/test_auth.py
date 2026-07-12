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


def test_update_profile_validates_avatar(db):
    user = make_user(db)
    # 1x1 png
    png = ("data:image/png;base64,"
           "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
    updated = auth.update_profile(db, user, display_name="Renamed", avatar=png)
    assert updated.display_name == "Renamed"
    assert updated.avatar == png

    with pytest.raises(ValueError, match="PNG or JPEG data URL"):
        auth.update_profile(db, user, display_name="X", avatar="data:image/gif;base64,AAAA")
    with pytest.raises(ValueError, match="not valid base64"):
        auth.update_profile(db, user, display_name="X", avatar="data:image/png;base64,@@@@")


def test_change_password_revokes_sessions(db):
    user = make_user(db, password="password123")
    token = auth.issue_refresh_token(db, user)

    with pytest.raises(ValueError, match="Current password is incorrect"):
        auth.change_password(db, user, current_password="wrong", new_password="newpassword1")

    auth.change_password(db, user, current_password="password123", new_password="newpassword1")
    assert auth.authenticate(db, user.email, "newpassword1").id == user.id
    with pytest.raises(ValueError):  # old refresh token died with the change
        auth.rotate_refresh_token(db, token)


def test_logout_revokes_without_theft_response(db):
    user = make_user(db)
    token = auth.issue_refresh_token(db, user)
    auth.revoke_refresh_token(db, token)
    with pytest.raises(ValueError, match="Session ended"):
        auth.rotate_refresh_token(db, token)


def test_lockout_after_repeated_failures(db):
    user = make_user(db, password="password123")
    for _ in range(4):
        with pytest.raises(ValueError, match="Invalid email or password"):
            auth.authenticate(db, user.email, "wrong")
    with pytest.raises(ValueError, match="account locked"):
        auth.authenticate(db, user.email, "wrong")  # 5th failure locks
    with pytest.raises(ValueError, match="Too many failed attempts"):
        auth.authenticate(db, user.email, "password123")  # even the right password waits


def test_successful_login_resets_failure_counter(db):
    user = make_user(db, password="password123")
    for _ in range(3):
        with pytest.raises(ValueError):
            auth.authenticate(db, user.email, "wrong")
    auth.authenticate(db, user.email, "password123")
    db.refresh(user)
    assert user.failed_logins == 0


def test_deactivated_account_cannot_login(db):
    user = make_user(db, password="password123")
    user.active = False
    db.commit()
    with pytest.raises(ValueError, match="deactivated"):
        auth.authenticate(db, user.email, "password123")


def test_password_reset_flow(db):
    user = make_user(db, password="password123")
    auth.request_password_reset(db, user.email, base_url="http://test")
    token = db.query(models.PasswordResetToken).filter_by(user_id=user.id).one()

    auth.reset_password(db, str(token.id), "brand-new-pass1")
    assert auth.authenticate(db, user.email, "brand-new-pass1").id == user.id
    # single use
    with pytest.raises(ValueError, match="invalid or has expired"):
        auth.reset_password(db, str(token.id), "another-pass1")


def test_reset_request_is_silent_for_unknown_email(db):
    auth.request_password_reset(db, "ghost@nowhere.test", base_url="http://test")
    assert db.query(models.PasswordResetToken).count() == 0
