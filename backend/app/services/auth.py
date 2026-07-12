import base64
import binascii
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import get_settings
from app.db import models
from app.repositories.users import UserRepository

# Roles a user may self-select at registration; admin is seeded only.
REGISTERABLE_ROLES = ("clinician", "front_desk", "manager")


def register(db: Session, email: str, password: str, display_name: str, role: str) -> models.User:
    if role not in REGISTERABLE_ROLES:
        raise ValueError(f"Role must be one of: {', '.join(REGISTERABLE_ROLES)}")
    repo = UserRepository(db)
    if repo.by_email(email) is not None:
        raise ValueError("An account with this email already exists")
    user = models.User(
        email=email.lower().strip(),
        password_hash=security.hash_password(password),
        display_name=display_name.strip(),
        role=role,
    )
    return repo.add(user)


MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


def authenticate(db: Session, email: str, password: str) -> models.User:
    user = UserRepository(db).by_email(email.lower().strip())
    if user is None:
        raise ValueError("Invalid email or password")
    now = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now:
        minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        raise ValueError(f"Too many failed attempts; try again in {minutes} minutes")
    if not security.verify_password(password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= MAX_FAILED_LOGINS:
            user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.failed_logins = 0
            db.commit()
            raise ValueError(
                f"Too many failed attempts; account locked for {LOCKOUT_MINUTES} minutes"
            )
        db.commit()
        raise ValueError("Invalid email or password")
    if not user.active:
        raise ValueError("This account has been deactivated")
    if user.failed_logins or user.locked_until:
        user.failed_logins = 0
        user.locked_until = None
        db.commit()
    return user


# --- Profile ---

AVATAR_PREFIXES = ("data:image/png;base64,", "data:image/jpeg;base64,")
MAX_AVATAR_BYTES = 300 * 1024  # decoded


def update_profile(
    db: Session, user: models.User, *, display_name: str, avatar: str | None
) -> models.User:
    if avatar is not None:
        prefix = next((p for p in AVATAR_PREFIXES if avatar.startswith(p)), None)
        if prefix is None:
            raise ValueError("Avatar must be a PNG or JPEG data URL")
        try:
            decoded = base64.b64decode(avatar[len(prefix):], validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Avatar image data is not valid base64")
        if len(decoded) > MAX_AVATAR_BYTES:
            raise ValueError("Avatar exceeds the 300 KB limit — pick a smaller image")
    user.display_name = display_name.strip()
    user.avatar = avatar
    db.commit()
    db.refresh(user)
    return user


def change_password(
    db: Session, user: models.User, *, current_password: str, new_password: str
) -> None:
    if not security.verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")
    if len(new_password) < 8:
        raise ValueError("New password needs at least 8 characters")
    user.password_hash = security.hash_password(new_password)
    # Sign out every other session: revoke all live refresh tokens.
    db.execute(
        update(models.RefreshToken)
        .where(models.RefreshToken.user_id == user.id,
               models.RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()


# --- Password reset (forgot password) ---

RESET_TOKEN_MINUTES = 60
logger = logging.getLogger("vitals.auth")


def request_password_reset(db: Session, email: str, base_url: str) -> None:
    """Create a reset token when the account exists. Always silent to the
    caller (no user enumeration); the link goes to the server log in place
    of an email service."""
    user = UserRepository(db).by_email(email.lower().strip())
    if user is None or not user.active:
        return
    token = models.PasswordResetToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_MINUTES),
    )
    db.add(token)
    db.commit()
    logger.info(
        "Password reset requested for %s — link (valid %d min): %s/reset-password?token=%s",
        user.email, RESET_TOKEN_MINUTES, base_url, token.id,
    )


def reset_password(db: Session, token_id: str, new_password: str) -> models.User:
    try:
        parsed = uuid.UUID(token_id)
    except ValueError:
        raise ValueError("Invalid reset link")
    token = db.get(models.PasswordResetToken, parsed)
    now = datetime.now(timezone.utc)
    if token is None or token.used_at is not None or token.expires_at < now:
        raise ValueError("This reset link is invalid or has expired")
    user = UserRepository(db).get(token.user_id)
    if user is None or not user.active:
        raise ValueError("This reset link is invalid or has expired")
    if len(new_password) < 8:
        raise ValueError("New password needs at least 8 characters")
    user.password_hash = security.hash_password(new_password)
    user.failed_logins = 0
    user.locked_until = None
    token.used_at = now
    # Sign out everywhere: the old credentials may be compromised.
    db.execute(
        update(models.RefreshToken)
        .where(models.RefreshToken.user_id == user.id,
               models.RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()
    return user


# --- Refresh-token rotation ---


def issue_refresh_token(db: Session, user: models.User) -> str:
    """Mint a refresh token with server-side state for rotation/revocation."""
    row = models.RefreshToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=get_settings().refresh_token_days),
    )
    db.add(row)
    db.commit()
    return security.create_refresh_token(user.id, row.id)


def rotate_refresh_token(db: Session, token: str) -> tuple[models.User, str]:
    """Validate + rotate. A revoked token presented again means theft: the
    user's every refresh token is revoked and they must sign in again."""
    user_id, jti = security.decode_refresh_token(token)
    row = db.get(models.RefreshToken, jti)
    now = datetime.now(timezone.utc)
    if row is None or row.user_id != user_id:
        raise ValueError("Unknown refresh token")
    if row.revoked_at is not None:
        if row.replaced_by is None:
            # Plain revocation (logout) — nothing suspicious.
            raise ValueError("Session ended; sign in again")
        # A rotated token came back: treat as theft and kill the whole family.
        db.execute(
            update(models.RefreshToken)
            .where(models.RefreshToken.user_id == user_id,
                   models.RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        raise ValueError("Refresh token reuse detected; all sessions revoked")
    if row.expires_at < now:
        raise ValueError("Refresh token expired")

    user = UserRepository(db).get(user_id)
    if user is None:
        raise ValueError("User no longer exists")

    new_row = models.RefreshToken(user_id=user.id, expires_at=now + timedelta(
        days=get_settings().refresh_token_days))
    db.add(new_row)
    db.flush()
    row.revoked_at = now
    row.replaced_by = new_row.id
    db.commit()
    return user, security.create_refresh_token(user.id, new_row.id)


def revoke_refresh_token(db: Session, token: str) -> None:
    try:
        user_id, jti = security.decode_refresh_token(token)
    except Exception:
        return  # logout is best-effort; an invalid cookie is already useless
    row = db.get(models.RefreshToken, jti)
    if row is not None and row.user_id == user_id and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()
