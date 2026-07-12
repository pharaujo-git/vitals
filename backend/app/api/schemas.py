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


# --- Encounters & observations ---


class ObservationInput(ApiModel):
    code: str
    value_num: float | None = None
    value_text: str | None = None
    taken_at: datetime | None = None


class ObservationOut(ApiModel):
    id: uuid.UUID
    code: str
    value_num: float | None
    value_text: str | None
    unit: str | None
    taken_at: datetime
    source: str


class EncounterInput(ApiModel):
    occurred_at: datetime
    encounter_type: str = "visit"
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    observations: list[ObservationInput] = []


class EncounterOut(ApiModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    clinician_name: str | None
    occurred_at: datetime
    encounter_type: str
    reason: str | None
    notes: str | None
    source: str
    observations: list[ObservationOut]

    @classmethod
    def from_orm_encounter(cls, e) -> "EncounterOut":
        return cls(
            id=e.id,
            patient_id=e.patient_id,
            clinician_name=e.clinician.display_name if e.clinician else None,
            occurred_at=e.occurred_at,
            encounter_type=e.encounter_type,
            reason=e.reason,
            notes=e.notes,
            source=e.source,
            observations=[ObservationOut.model_validate(o) for o in e.observations],
        )


class ObservationTypeOut(ApiModel):
    code: str
    label: str
    kind: str
    unit: str | None
    min_value: float | None
    max_value: float | None


# --- Search ---


class PatientHit(ApiModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str
    dob: date


class EncounterHit(ApiModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    reason: str | None
    occurred_at: datetime


class SearchResults(ApiModel):
    patients: list[PatientHit]
    encounters: list[EncounterHit]


# --- Audit ---


class AuditEntryOut(ApiModel):
    id: uuid.UUID
    user_email: str
    action: str
    entity_type: str | None
    entity_id: str | None
    detail: dict | None
    created_at: datetime
