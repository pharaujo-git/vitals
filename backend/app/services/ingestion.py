"""Multi-source clinical data ingestion.

Two source formats map into the common model:

- CSV: one row per record, columns
  mrn,first_name,last_name,dob,sex,code,value,taken_at
  (code/value/taken_at optional — a row without them upserts the patient only)

- HL7v2-style pipe-delimited messages:
  MSH|^~\\&|SENDING_APP|20260701120000
  PID|<mrn>|<Family^Given>|<YYYYMMDD>|<F/M/O/U>
  OBX|<loinc>|<value>|<unit>|<YYYYMMDDHHMMSS>

Records that fail mapping become ImportIssue rows on the batch — reported,
never silently dropped. Patients are matched by MRN; existing demographics
are never overwritten by an import, only missing patients are created and
observations appended under a new 'imported' encounter tagged with the
source system.
"""

import csv
import io
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.db import models
from app.repositories.imports import ImportRepository
from app.repositories.patients import PatientRepository
from app.services import patients as patient_service
from app.services.encounters import build_observation
from app.services.observations import BY_LOINC, CATALOG

SEX_MAP = {"f": "female", "m": "male", "o": "other", "u": "unknown"}


class RecordError(Exception):
    pass


def _parse_date(value: str, field: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise RecordError(f"Could not parse {field} date: {value!r}")


def _parse_datetime(value: str, field: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S", "%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise RecordError(f"Could not parse {field} timestamp: {value!r}")


def _upsert_patient(
    db: Session,
    *,
    mrn: str,
    first_name: str,
    last_name: str,
    dob: date,
    sex: str,
    source: str,
) -> models.Patient:
    existing = PatientRepository(db).by_mrn(mrn)
    if existing is not None:
        return existing
    return patient_service.create_patient(
        db,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        sex=sex,
        phone=None,
        email=None,
        address=None,
        history=None,
        mrn=mrn,
        source=source,
    )


def _imported_encounter(
    db: Session,
    encounters: dict[uuid.UUID, models.Encounter],
    patient: models.Patient,
    label: str,
    source: str,
) -> models.Encounter:
    """One encounter per patient per batch collects that batch's observations."""
    if patient.id not in encounters:
        encounter = models.Encounter(
            patient_id=patient.id,
            occurred_at=datetime.now(timezone.utc),
            encounter_type="imported",
            reason=label,
            source=source,
        )
        db.add(encounter)
        db.flush()
        encounters[patient.id] = encounter
    return encounters[patient.id]


def import_csv(db: Session, user: models.User, label: str, content: str) -> models.ImportBatch:
    batch = models.ImportBatch(
        label=label, format="csv", created_by=user.id,
        total_records=0, imported_count=0, error_count=0,
    )
    encounters: dict[uuid.UUID, models.Encounter] = {}

    reader = csv.DictReader(io.StringIO(content))
    required = {"mrn", "first_name", "last_name", "dob"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError(
            f"CSV must have a header row with at least: {', '.join(sorted(required))}"
        )

    for number, row in enumerate(reader, start=2):  # header is line 1
        batch.total_records += 1
        raw = ",".join((row.get(k) or "") for k in reader.fieldnames)
        try:
            mrn = (row.get("mrn") or "").strip()
            if not mrn:
                raise RecordError("Missing mrn")
            first = (row.get("first_name") or "").strip()
            last = (row.get("last_name") or "").strip()
            if not first or not last:
                raise RecordError("Missing first_name or last_name")
            dob = _parse_date(row.get("dob") or "", "dob")
            sex = SEX_MAP.get((row.get("sex") or "u").strip().lower()[:1], "unknown")
            try:
                patient = _upsert_patient(
                    db, mrn=mrn, first_name=first, last_name=last, dob=dob, sex=sex, source="csv"
                )
            except ValueError as exc:
                raise RecordError(str(exc))

            code = (row.get("code") or "").strip()
            value = (row.get("value") or "").strip()
            if code or value:
                if code not in CATALOG:
                    raise RecordError(f"Unknown observation code: {code!r}")
                taken_at = (
                    _parse_datetime(row["taken_at"], "taken_at")
                    if (row.get("taken_at") or "").strip()
                    else datetime.now(timezone.utc)
                )
                kind = CATALOG[code].kind
                value_num: float | None = None
                value_text: str | None = None
                if kind == "numeric":
                    try:
                        value_num = float(value)
                    except ValueError:
                        raise RecordError(f"{code} needs a numeric value, got {value!r}")
                else:
                    value_text = value
                try:
                    observation = build_observation(
                        patient_id=patient.id,
                        code=code,
                        value_num=value_num,
                        value_text=value_text,
                        taken_at=taken_at,
                        source="csv",
                    )
                except ValueError as exc:
                    raise RecordError(str(exc))
                encounter = _imported_encounter(db, encounters, patient, label, "csv")
                encounter.observations.append(observation)
                db.flush()
            batch.imported_count += 1
        except RecordError as exc:
            batch.error_count += 1
            batch.issues.append(
                models.ImportIssue(record_number=number, message=str(exc), raw=raw[:2000])
            )

    return ImportRepository(db).add(batch)


def import_hl7(db: Session, user: models.User, label: str, content: str) -> models.ImportBatch:
    batch = models.ImportBatch(
        label=label, format="hl7", created_by=user.id,
        total_records=0, imported_count=0, error_count=0,
    )
    encounters: dict[uuid.UUID, models.Encounter] = {}

    patient: models.Patient | None = None
    for number, line in enumerate(
        (line.strip() for line in content.strip().splitlines()), start=1
    ):
        if not line:
            continue
        fields = line.split("|")
        segment = fields[0].upper()
        if segment == "MSH":
            continue
        batch.total_records += 1
        try:
            if segment == "PID":
                if len(fields) < 4:
                    raise RecordError("PID segment needs at least mrn, name and dob")
                mrn = fields[1].strip()
                if not mrn:
                    raise RecordError("PID segment missing MRN")
                name_parts = fields[2].split("^")
                last = name_parts[0].strip()
                first = name_parts[1].strip() if len(name_parts) > 1 else ""
                if not first or not last:
                    raise RecordError(f"Could not parse patient name: {fields[2]!r}")
                dob = _parse_date(fields[3], "dob")
                sex = SEX_MAP.get(fields[4].strip().lower()[:1] if len(fields) > 4 else "u", "unknown")
                try:
                    patient = _upsert_patient(
                        db, mrn=mrn, first_name=first, last_name=last, dob=dob, sex=sex, source="hl7"
                    )
                except ValueError as exc:
                    raise RecordError(str(exc))
                batch.imported_count += 1
            elif segment == "OBX":
                if patient is None:
                    raise RecordError("OBX segment before any PID segment")
                if len(fields) < 3:
                    raise RecordError("OBX segment needs a code and a value")
                loinc = fields[1].strip()
                obs_type = BY_LOINC.get(loinc)
                if obs_type is None:
                    raise RecordError(f"Unknown LOINC code: {loinc!r}")
                value = fields[2].strip()
                value_num: float | None = None
                value_text: str | None = None
                if obs_type.kind == "numeric":
                    try:
                        value_num = float(value)
                    except ValueError:
                        raise RecordError(f"{obs_type.code} needs a numeric value, got {value!r}")
                else:
                    value_text = value
                taken_at = (
                    _parse_datetime(fields[4], "taken_at")
                    if len(fields) > 4 and fields[4].strip()
                    else datetime.now(timezone.utc)
                )
                try:
                    observation = build_observation(
                        patient_id=patient.id,
                        code=obs_type.code,
                        value_num=value_num,
                        value_text=value_text,
                        taken_at=taken_at,
                        source="hl7",
                    )
                except ValueError as exc:
                    raise RecordError(str(exc))
                encounter = _imported_encounter(db, encounters, patient, label, "hl7")
                encounter.observations.append(observation)
                db.flush()
                batch.imported_count += 1
            else:
                raise RecordError(f"Unknown segment type: {segment!r}")
        except RecordError as exc:
            batch.error_count += 1
            batch.issues.append(
                models.ImportIssue(record_number=number, message=str(exc), raw=line[:2000])
            )

    return ImportRepository(db).add(batch)
