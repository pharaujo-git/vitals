from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import schemas
from app.core import security
from app.db import models
from app.db.session import get_db
from app.repositories.users import UserRepository
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_response(user: models.User) -> schemas.AuthResponse:
    access, refresh = security.create_token_pair(user)
    return schemas.AuthResponse(
        access_token=access,
        refresh_token=refresh,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/register", response_model=schemas.AuthResponse, status_code=201)
def register(body: schemas.RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.register(db, body.email, body.password, body.display_name, body.role)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return _auth_response(user)


@router.post("/login", response_model=schemas.AuthResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate(db, body.email, body.password)
    except ValueError:
        raise HTTPException(401, "Invalid email or password")
    return _auth_response(user)


@router.post("/refresh", response_model=schemas.AuthResponse)
def refresh(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    user_id = security.decode_token(body.refresh_token, "refresh")
    user = UserRepository(db).get(user_id)
    if user is None:
        raise HTTPException(401, "User no longer exists")
    return _auth_response(user)


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(security.get_current_user)):
    return user
