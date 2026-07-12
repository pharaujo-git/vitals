import uuid
from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base DTO: camelCase over the wire, ORM-attribute loading enabled."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


T = TypeVar("T")


class Page(ApiModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


def page(items, total: int, limit: int, offset: int) -> dict:
    return {"items": items, "total": total, "limit": limit, "offset": offset}


# --- Auth ---


class UserOut(ApiModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str


class RegisterRequest(ApiModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    role: str = "clinician"


class LoginRequest(ApiModel):
    email: str
    password: str


class RefreshRequest(ApiModel):
    refresh_token: str


class AuthResponse(ApiModel):
    access_token: str
    refresh_token: str
    user: UserOut


# --- Patients ---


class PatientInput(ApiModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    dob: date
    sex: str = "unknown"
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    history: str | None = None
    mrn: str | None = Field(default=None, max_length=40)


class PatientOut(ApiModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str
    dob: date
    sex: str
    phone: str | None
    email: str | None
    address: str | None
    history: str | None
    source: str
    created_at: datetime
    updated_at: datetime


# --- Appointments ---


class ClinicianOut(ApiModel):
    id: uuid.UUID
    display_name: str


class AppointmentInput(ApiModel):
    patient_id: uuid.UUID
    clinician_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    reason: str | None = Field(default=None, max_length=255)


class AppointmentStatusInput(ApiModel):
    status: str


class AppointmentOut(ApiModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    patient_mrn: str
    clinician_id: uuid.UUID
    clinician_name: str
    start_at: datetime
    end_at: datetime
    reason: str | None
    status: str

    @classmethod
    def from_orm_appointment(cls, a) -> "AppointmentOut":
        return cls(
            id=a.id,
            patient_id=a.patient_id,
            patient_name=f"{a.patient.first_name} {a.patient.last_name}",
            patient_mrn=a.patient.mrn,
            clinician_id=a.clinician_id,
            clinician_name=a.clinician.display_name,
            start_at=a.start_at,
            end_at=a.end_at,
            reason=a.reason,
            status=a.status,
        )
