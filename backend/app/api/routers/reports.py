from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api import schemas
from app.core.audit import audit
from app.core.security import require_roles
from app.db import models
from app.db.session import get_db
from app.services import reports as report_service

router = APIRouter(prefix="/reports", tags=["reports"])

can_view = require_roles("manager")

IDENTIFYING = ("mrn", "first_name", "last_name", "dob", "phone", "email")


def _row_for(user: models.User, row: dict) -> schemas.CohortRow:
    allowed = set(report_service.columns_for(user))
    cleaned = {
        key: (value if key in allowed or key not in IDENTIFYING else None)
        for key, value in row.items()
    }
    return schemas.CohortRow(**cleaned)


@router.get("/cohort", response_model=schemas.CohortPreview)
def cohort_preview(
    min_age: int | None = Query(None, alias="minAge", ge=0, le=150),
    max_age: int | None = Query(None, alias="maxAge", ge=0, le=150),
    sex: str | None = None,
    source: str | None = None,
    risk_level: str | None = Query(None, alias="riskLevel"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(can_view),
):
    rows = report_service.build_cohort(
        db, min_age=min_age, max_age=max_age, sex=sex, source=source, risk_level=risk_level
    )
    window = rows[offset : offset + limit]
    return schemas.CohortPreview(
        items=[_row_for(user, row) for row in window],
        total=len(rows),
        limit=limit,
        offset=offset,
        columns=report_service.columns_for(user),
    )


@router.get("/cohort/export")
def cohort_export(
    min_age: int | None = Query(None, alias="minAge", ge=0, le=150),
    max_age: int | None = Query(None, alias="maxAge", ge=0, le=150),
    sex: str | None = None,
    source: str | None = None,
    risk_level: str | None = Query(None, alias="riskLevel"),
    db: Session = Depends(get_db),
    user: models.User = Depends(can_view),
):
    rows = report_service.build_cohort(
        db, min_age=min_age, max_age=max_age, sex=sex, source=source, risk_level=risk_level
    )
    columns = report_service.columns_for(user)
    content = report_service.to_csv(rows, columns)
    audit(db, user, "report.exported", detail={
        "rows": len(rows),
        "deidentified": user.role != "admin",
        "filters": {"minAge": min_age, "maxAge": max_age, "sex": sex, "source": source, "riskLevel": risk_level},
    })
    filename = f"vitals-cohort-{date.today().isoformat()}.csv"
    return Response(
        content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
