import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.session import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

ROLES = ("admin", "clinician", "front_desk", "manager")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(
    user_id: uuid.UUID, token_type: str, lifetime: timedelta, jti: uuid.UUID | None = None
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + lifetime,
    }
    if jti is not None:
        payload["jti"] = str(jti)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user: models.User) -> str:
    settings = get_settings()
    return _create_token(user.id, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: uuid.UUID, jti: uuid.UUID) -> str:
    settings = get_settings()
    return _create_token(
        user_id, "refresh", timedelta(days=settings.refresh_token_days), jti=jti
    )


def _decode(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")


def decode_token(token: str, expected_type: str) -> uuid.UUID:
    payload = _decode(token)
    if payload.get("type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    return uuid.UUID(payload["sub"])


def decode_refresh_token(token: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Returns (user_id, jti) from a refresh token."""
    payload = _decode(token)
    if payload.get("type") != "refresh" or "jti" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    return uuid.UUID(payload["sub"]), uuid.UUID(payload["jti"])


def _user_from_access_payload(db: Session, payload: dict) -> models.User:
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
    user = db.get(models.User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    if not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "This account has been deactivated")
    if user.sessions_revoked_at is not None:
        issued_at = payload.get("iat")
        # Whole-second comparison: iat carries second precision, and a token
        # minted in the same second as the revocation (e.g. an immediate
        # re-login) must stay valid.
        if issued_at is None or int(issued_at) < int(user.sessions_revoked_at.timestamp()):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "Session revoked; sign in again"
            )
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return _user_from_access_payload(db, _decode(credentials.credentials))


def user_from_token(db: Session, token: str) -> models.User:
    """Authenticate a raw access token (SSE: EventSource can't send headers)."""
    return _user_from_access_payload(db, _decode(token))


def require_roles(*roles: str):
    """Dependency: only these roles (admin always passes) may call the endpoint."""

    def dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role != "admin" and user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return dependency
