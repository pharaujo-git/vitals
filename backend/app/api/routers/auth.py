from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api import schemas
from app.core import security
from app.core.audit import audit
from app.core.config import get_settings
from app.db import models
from app.db.session import get_db
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "vitals_refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.refresh_token_days * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        path="/api/auth",  # only auth endpoints ever see it
    )


def _auth_response(db: Session, response: Response, user: models.User) -> schemas.AuthResponse:
    _set_refresh_cookie(response, auth_service.issue_refresh_token(db, user))
    return schemas.AuthResponse(
        access_token=security.create_access_token(user),
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/register", response_model=schemas.AuthResponse, status_code=201)
def register(body: schemas.RegisterRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = auth_service.register(db, body.email, body.password, body.display_name, body.role)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return _auth_response(db, response, user)


@router.post("/login", response_model=schemas.AuthResponse)
def login(body: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate(db, body.email, body.password)
    except ValueError as exc:
        status = 429 if "Too many failed attempts" in str(exc) else 401
        raise HTTPException(status, str(exc))
    return _auth_response(db, response, user)


@router.post("/refresh", response_model=schemas.AuthResponse)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if refresh_cookie is None:
        raise HTTPException(401, "No refresh token")
    try:
        user, new_refresh = auth_service.rotate_refresh_token(db, refresh_cookie)
    except ValueError as exc:
        response.delete_cookie(REFRESH_COOKIE, path="/api/auth")
        raise HTTPException(401, str(exc))
    _set_refresh_cookie(response, new_refresh)
    return schemas.AuthResponse(
        access_token=security.create_access_token(user),
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if refresh_cookie is not None:
        auth_service.revoke_refresh_token(db, refresh_cookie)
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(security.get_current_user)):
    return user


@router.put("/profile", response_model=schemas.UserOut)
def update_profile(
    body: schemas.ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    try:
        user = auth_service.update_profile(
            db, user, display_name=body.display_name, avatar=body.avatar
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "user.profile_updated", entity_type="user", entity_id=user.id,
          detail={"hasAvatar": user.avatar is not None})
    return user


@router.post("/change-password", status_code=204)
def change_password(
    body: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    try:
        auth_service.change_password(
            db, user,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    audit(db, user, "user.password_changed", entity_type="user", entity_id=user.id)
