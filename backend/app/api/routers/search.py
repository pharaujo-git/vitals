from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.services import search as search_service

router = APIRouter(prefix="/search", tags=["search"])

can_search = require_roles("clinician", "front_desk")


@router.get("", response_model=schemas.SearchResults)
def search(
    q: str = Query(min_length=2, max_length=100),
    db: Session = Depends(get_db),
    user: models.User = Depends(can_search),
):
    results = search_service.search(db, user, q)
    return schemas.SearchResults(
        patients=[schemas.PatientHit.model_validate(p) for p in results["patients"]],
        encounters=[
            schemas.EncounterHit(
                id=e.id,
                patient_id=e.patient_id,
                patient_name=f"{e.patient.first_name} {e.patient.last_name}",
                reason=e.reason,
                occurred_at=e.occurred_at,
            )
            for e in results["encounters"]
        ],
    )
