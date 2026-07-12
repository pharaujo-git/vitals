import uuid

from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class UserRepository(Repository):
    def get(self, user_id: uuid.UUID) -> models.User | None:
        return self.db.get(models.User, user_id)

    def by_email(self, email: str) -> models.User | None:
        return self.db.scalar(select(models.User).where(models.User.email == email))

    def clinicians(self) -> list[models.User]:
        stmt = (
            select(models.User)
            .where(models.User.role.in_(("clinician", "admin")))
            .order_by(models.User.display_name)
            .limit(200)
        )
        return list(self.db.scalars(stmt))

    def add(self, user: models.User) -> models.User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
