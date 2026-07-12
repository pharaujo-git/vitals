from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.services import dashboard as dashboard_service
from app.services import risk as risk_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

can_view = require_roles("manager")


def _age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


@router.get("", response_model=schemas.DashboardOut)
def dashboard(
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    return dashboard_service.summary(db)


@router.get("/risk-flags", response_model=schemas.Page[schemas.RiskFlagOut])
def risk_flags(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(can_view),
):
    flags = risk_service.compute_flags(db)
    window = flags[offset : offset + limit]
    items = [
        schemas.RiskFlagOut(
            patient_id=f.patient.id,
            patient_name=f"{f.patient.first_name} {f.patient.last_name}",
            mrn=f.patient.mrn,
            age=_age(f.patient.dob),
            score=f.score,
            level=f.level,
            reasons=f.reasons,
        )
        for f in window
    ]
    return schemas.page(items, len(flags), limit, offset)
