"""Consent-based access control on patient records.

A record marked restricted is only readable by admins and the roles/users
its consent grants name. Denials raise ConsentError — the controller maps
it to 403 — and every denial is written to the audit log.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.security import ROLES
from app.db import models
from app.repositories.users import UserRepository


class ConsentError(Exception):
    pass


def grants_for(db: Session, patient_id: uuid.UUID) -> list[models.ConsentGrant]:
    stmt = select(models.ConsentGrant).where(models.ConsentGrant.patient_id == patient_id)
    return list(db.scalars(stmt))


def can_access(db: Session, user: models.User, patient: models.Patient) -> bool:
    if not patient.restricted or user.role == "admin":
        return True
    for grant in grants_for(db, patient.id):
        if grant.grantee_type == "role" and grant.grantee == user.role:
            return True
        if grant.grantee_type == "user" and grant.grantee == str(user.id):
            return True
    return False


def ensure_access(db: Session, user: models.User, patient: models.Patient) -> None:
    """Raise (and audit) when the caller may not open this record."""
    if can_access(db, user, patient):
        return
    audit(db, user, "access.denied", entity_type="patient", entity_id=patient.id)
    raise ConsentError("Access to this record is restricted by consent rules")


def update_rules(
    db: Session,
    patient: models.Patient,
    *,
    restricted: bool,
    grants: list[dict],
) -> None:
    """Replace the record's access rules. User grants arrive as emails."""
    new_grants: list[models.ConsentGrant] = []
    for grant in grants:
        grantee_type = grant["grantee_type"]
        grantee = grant["grantee"].strip()
        if grantee_type == "role":
            if grantee not in ROLES:
                raise ValueError(f"Unknown role: {grantee}")
        elif grantee_type == "user":
            user = UserRepository(db).by_email(grantee.lower())
            if user is None:
                raise ValueError(f"No user with email {grantee}")
            grantee = str(user.id)
        else:
            raise ValueError("Grantee type must be 'role' or 'user'")
        new_grants.append(
            models.ConsentGrant(patient_id=patient.id, grantee_type=grantee_type, grantee=grantee)
        )

    for existing in grants_for(db, patient.id):
        db.delete(existing)
    patient.restricted = restricted
    db.add_all(new_grants)
    db.commit()


def describe_rules(db: Session, patient: models.Patient) -> dict:
    grants = []
    for grant in grants_for(db, patient.id):
        display = grant.grantee
        if grant.grantee_type == "user":
            user = UserRepository(db).get(uuid.UUID(grant.grantee))
            display = user.email if user else "deleted user"
        grants.append(
            {"grantee_type": grant.grantee_type, "grantee": grant.grantee, "display": display}
        )
    return {"restricted": patient.restricted, "grants": grants}
