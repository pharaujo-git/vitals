import uuid

from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class UserRepository(Repository):
    def get(self, user_id: uuid.UUID) -> models.User | None:
        return self.db.get(models.User, user_id)

    def by_email(self, email: str) -> models.User | None:
        return self.db.scalar(select(models.User).where(models.User.email == email))

    def all_users(self, limit: int = 200) -> list[models.User]:
        stmt = (
            select(models.User)
            .where(models.User.active.is_(True))
            .order_by(models.User.display_name)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def clinicians(self) -> list[models.User]:
        stmt = (
            select(models.User)
            .where(models.User.role.in_(("clinician", "admin")), models.User.active.is_(True))
            .order_by(models.User.display_name)
            .limit(200)
        )
        return list(self.db.scalars(stmt))

    def page(self, search: str | None, limit: int, offset: int):
        stmt = select(models.User).order_by(models.User.display_name)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                models.User.display_name.ilike(like) | models.User.email.ilike(like)
            )
        return self.paginate(stmt, limit, offset)

    def add(self, user: models.User) -> models.User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
