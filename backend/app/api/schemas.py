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
    avatar: str | None = None


class ProfileUpdateRequest(ApiModel):
    display_name: str = Field(min_length=1, max_length=120)
    avatar: str | None = None


class ChangePasswordRequest(ApiModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserAdminOut(ApiModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    active: bool
    created_at: datetime


class RoleInput(ApiModel):
    role: str


class ActiveInput(ApiModel):
    active: bool


class TempPasswordOut(ApiModel):
    temp_password: str


class RegisterRequest(ApiModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    role: str = "clinician"


class LoginRequest(ApiModel):
    email: str
    password: str


class AuthResponse(ApiModel):
    access_token: str
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
    restricted: bool
    created_at: datetime
    updated_at: datetime


class ConsentGrantInput(ApiModel):
    grantee_type: str
    grantee: str  # role name, or user email (resolved server-side)


class ConsentGrantOut(ApiModel):
    grantee_type: str
    grantee: str
    display: str


class ConsentOut(ApiModel):
    restricted: bool
    grants: list[ConsentGrantOut]


class ConsentInput(ApiModel):
    restricted: bool
    grants: list[ConsentGrantInput] = []


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


# --- Consolidated view & duplicates ---


class SourceContribution(ApiModel):
    source: str
    encounters: int
    observations: int


class PatientSummaryOut(ApiModel):
    sources: list[SourceContribution]
    latest_observations: list[ObservationOut]
    pending_duplicates: int


class DuplicatePatientOut(ApiModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str
    dob: date
    sex: str
    source: str


class DuplicateFlagOut(ApiModel):
    id: uuid.UUID
    patient_a: DuplicatePatientOut
    patient_b: DuplicatePatientOut
    reason: str
    status: str
    created_at: datetime
    resolved_at: datetime | None


class ScanResult(ApiModel):
    new_flags: int


# --- Imports ---


class ImportTextInput(ApiModel):
    label: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class ImportBatchOut(ApiModel):
    id: uuid.UUID
    label: str
    format: str
    total_records: int
    imported_count: int
    error_count: int
    created_at: datetime


class ImportIssueOut(ApiModel):
    id: uuid.UUID
    record_number: int
    message: str
    raw: str | None


# --- Dashboard & risk flags ---


class DashboardTotals(ApiModel):
    patients: int
    encounters: int
    observations: int
    upcoming_appointments: int


class LabeledCount(ApiModel):
    label: str
    count: int


class MonthCount(ApiModel):
    year: int
    month: int
    count: int


class RiskSummary(ApiModel):
    high: int
    moderate: int
    flagged: int


class DashboardOut(ApiModel):
    totals: DashboardTotals
    sex_breakdown: list[LabeledCount]
    age_bands: list[LabeledCount]
    source_breakdown: list[LabeledCount]
    encounter_trend: list[MonthCount]
    observation_trend: list[MonthCount]
    risk_summary: RiskSummary


class RiskFlagOut(ApiModel):
    patient_id: uuid.UUID
    patient_name: str
    mrn: str
    age: int
    score: int
    level: str
    reasons: list[str]


# --- Attachments ---


class AttachmentOut(ApiModel):
    id: uuid.UUID
    kind: str
    filename: str
    content_type: str
    description: str | None
    size: int
    uploaded_by_name: str | None
    created_at: datetime


# --- Observation trends ---


class TrendPoint(ApiModel):
    taken_at: datetime
    value: float


class TrendSeries(ApiModel):
    code: str
    label: str
    unit: str | None
    points: list[TrendPoint]


# --- Timeline ---


class TimelineEventOut(ApiModel):
    kind: str
    at: datetime
    title: str
    detail: str | None
    source: str | None


# --- Clinical lists: problems, medications, allergies ---


class ProblemInput(ApiModel):
    description: str = Field(min_length=1, max_length=255)
    icd_code: str | None = Field(default=None, max_length=20)
    status: str = "active"
    onset_date: date | None = None


class ProblemOut(ApiModel):
    id: uuid.UUID
    description: str
    icd_code: str | None
    status: str
    onset_date: date | None


class MedicationInput(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    dose: str | None = Field(default=None, max_length=80)
    frequency: str | None = Field(default=None, max_length=80)
    active: bool = True
    started_date: date | None = None


class MedicationOut(ApiModel):
    id: uuid.UUID
    name: str
    dose: str | None
    frequency: str | None
    active: bool
    started_date: date | None


class AllergyInput(ApiModel):
    substance: str = Field(min_length=1, max_length=120)
    reaction: str | None = Field(default=None, max_length=255)
    severity: str = "moderate"


class AllergyOut(ApiModel):
    id: uuid.UUID
    substance: str
    reaction: str | None
    severity: str


class ClinicalListsOut(ApiModel):
    problems: list[ProblemOut]
    medications: list[MedicationOut]
    allergies: list[AllergyOut]


# --- Messages ---


class MessageAttachmentInput(ApiModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    data_base64: str


class MessageAttachmentOut(ApiModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size: int


class MessageInput(ApiModel):
    recipient_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    patient_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    attachments: list[MessageAttachmentInput] = []


class MessageOut(ApiModel):
    id: uuid.UUID
    root_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    recipient_id: uuid.UUID
    recipient_name: str
    patient_id: uuid.UUID | None
    patient_name: str | None
    subject: str
    body: str
    read_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    attachments: list[MessageAttachmentOut]

    @classmethod
    def from_orm_message(cls, m) -> "MessageOut":
        return cls(
            id=m.id,
            root_id=m.root_id,
            sender_id=m.sender_id,
            sender_name=m.sender.display_name,
            recipient_id=m.recipient_id,
            recipient_name=m.recipient.display_name,
            patient_id=m.patient_id,
            patient_name=f"{m.patient.first_name} {m.patient.last_name}" if m.patient else None,
            subject=m.subject,
            body=m.body,
            read_at=m.read_at,
            archived_at=m.archived_at,
            created_at=m.created_at,
            attachments=[MessageAttachmentOut.model_validate(a) for a in m.attachments],
        )


class RecipientOut(ApiModel):
    id: uuid.UUID
    display_name: str
    role: str


class UnreadCount(ApiModel):
    count: int


# --- Reports ---


class CohortRow(ApiModel):
    """A cohort preview row; identifying fields are None for de-identified callers."""

    patient_id: uuid.UUID
    mrn: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    dob: str | None = None
    age: int
    sex: str
    source: str
    encounters: int
    risk_score: int
    risk_level: str
    risk_reasons: str


class CohortPreview(ApiModel):
    items: list[CohortRow]
    total: int
    limit: int
    offset: int
    columns: list[str]


# --- Audit ---


class AuditEntryOut(ApiModel):
    id: uuid.UUID
    user_email: str
    action: str
    entity_type: str | None
    entity_id: str | None
    detail: dict | None
    created_at: datetime
