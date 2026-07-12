import uuid

from sqlalchemy import select

from app.db import models
from app.repositories import Repository


class UserRepository(Repository):
    def get(self, user_id: uuid.UUID) -> models.User | None:
        return self.db.get(models.User, user_id)

    def by_email(self, email: str) -> models.User | None:
        return self.db.scalar(select(models.User).where(models.User.email == email))

    def add(self, user: models.User) -> models.User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
