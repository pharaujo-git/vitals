import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload, load_only

from app.db import models
from app.repositories import Repository

_META = load_only(
    models.Attachment.id,
    models.Attachment.patient_id,
    models.Attachment.kind,
    models.Attachment.filename,
    models.Attachment.content_type,
    models.Attachment.description,
    models.Attachment.size,
    models.Attachment.created_at,
)


class AttachmentRepository(Repository):
    def get(self, attachment_id: uuid.UUID) -> models.Attachment | None:
        return self.db.get(models.Attachment, attachment_id)

    def for_patient(self, patient_id: uuid.UUID) -> list[models.Attachment]:
        """Metadata only — the bytes column stays unloaded for listings."""
        stmt = (
            select(models.Attachment)
            .options(_META, joinedload(models.Attachment.uploader))
            .where(models.Attachment.patient_id == patient_id)
            .order_by(models.Attachment.created_at.desc())
            .limit(200)
        )
        return list(self.db.scalars(stmt))

    def add(self, attachment: models.Attachment) -> models.Attachment:
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def delete(self, attachment: models.Attachment) -> None:
        self.db.delete(attachment)
        self.db.commit()
