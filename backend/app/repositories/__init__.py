from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


class Repository:
    def __init__(self, db: Session):
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def paginate(self, stmt: Select, limit: int, offset: int):
        """Run a list statement returning (items, total) for a Page envelope."""
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(stmt.limit(limit).offset(offset)).all()
        return items, total
