from sqlalchemy.orm import Session

from app.core import security
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


def authenticate(db: Session, email: str, password: str) -> models.User:
    user = UserRepository(db).by_email(email.lower().strip())
    if user is None or not security.verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    return user
