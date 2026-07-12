import pytest

from app.db import models
from app.services import auth
from app.services import users as user_service
from tests.conftest import make_user


def test_set_role_and_self_guard(db):
    admin = make_user(db, "admin")
    target = make_user(db, "front_desk")
    assert user_service.set_role(db, admin, target, "manager").role == "manager"
    with pytest.raises(ValueError, match="own role"):
        user_service.set_role(db, admin, admin, "clinician")
    with pytest.raises(ValueError, match="Role must be one of"):
        user_service.set_role(db, admin, target, "superuser")


def test_deactivation_revokes_sessions_and_blocks_self(db):
    admin = make_user(db, "admin")
    target = make_user(db, "clinician")
    token = auth.issue_refresh_token(db, target)

    user_service.set_active(db, admin, target, False)
    assert target.active is False
    live = db.query(models.RefreshToken).filter_by(user_id=target.id, revoked_at=None).count()
    assert live == 0

    with pytest.raises(ValueError, match="own account"):
        user_service.set_active(db, admin, admin, False)
    # reactivation restores login
    user_service.set_active(db, admin, target, True)
    assert target.active is True
    with pytest.raises(ValueError):  # old session stays dead
        auth.rotate_refresh_token(db, token)


def test_admin_password_reset(db):
    admin = make_user(db, "admin")
    target = make_user(db, "clinician", password="password123")
    temp_password = user_service.admin_reset_password(db, admin, target)
    assert auth.authenticate(db, target.email, temp_password).id == target.id
    with pytest.raises(ValueError):
        auth.authenticate(db, target.email, "password123")
    with pytest.raises(ValueError, match="profile page"):
        user_service.admin_reset_password(db, admin, admin)
