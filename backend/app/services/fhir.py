"""FHIR R4 import and export.

Export builds a collection Bundle of the Patient and their Observations
(LOINC-coded, via the fhir.resources models so output is schema-valid).
Import accepts a Bundle or single resource, validates it with the same
models, and maps it into the common store through the shared ingestion
rules: patients match by MRN identifier, observations validate against
the catalog, and unmappable resources become batch issues.
"""

import json
import uuid
from datetime import datetime, timezone

from fhir.resources.R4B.allergyintolerance import AllergyIntolerance as FhirAllergy
from fhir.resources.R4B.bundle import Bundle
from fhir.resources.R4B.condition import Condition as FhirCondition
from fhir.resources.R4B.medicationstatement import MedicationStatement as FhirMedication
from fhir.resources.R4B.observation import Observation as FhirObservation
from fhir.resources.R4B.patient import Patient as FhirPatient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import models
from app.repositories.imports import ImportRepository
from app.repositories.patients import PatientRepository
from app.services import patients as patient_service
from app.services.encounters import build_observation
from app.services.observations import BY_LOINC, CATALOG

MRN_SYSTEM = "urn:vitals:mrn"
LOINC_SYSTEM = "http://loinc.org"


def export_patient(
    patient: models.Patient,
    observations: list[models.Observation],
    problems: list[models.Problem] = (),
    medications: list[models.Medication] = (),
    allergies: list[models.Allergy] = (),
) -> dict:
    fhir_patient = FhirPatient(
        id=str(patient.id),
        identifier=[{"system": MRN_SYSTEM, "value": patient.mrn}],
        name=[{"family": patient.last_name, "given": [patient.first_name]}],
        birthDate=patient.dob.isoformat(),
        gender=patient.sex,
        telecom=(
            [{"system": "phone", "value": patient.phone}] if patient.phone else None
        ),
        address=([{"text": patient.address}] if patient.address else None),
    )

    entries = [
        {"fullUrl": f"urn:uuid:{patient.id}", "resource": fhir_patient.model_dump(mode="json", exclude_none=True)}
    ]
    for obs in observations:
        obs_type = CATALOG.get(obs.code)
        resource = FhirObservation(
            id=str(obs.id),
            status="final",
            code={
                "coding": [
                    {
                        "system": LOINC_SYSTEM,
                        "code": obs_type.loinc if obs_type else obs.code,
                        "display": obs_type.label if obs_type else obs.code,
                    }
                ],
                "text": obs_type.label if obs_type else obs.code,
            },
            subject={"reference": f"urn:uuid:{patient.id}"},
            effectiveDateTime=obs.taken_at.isoformat(),
            valueQuantity=(
                {"value": obs.value_num, "unit": obs.unit} if obs.value_num is not None else None
            ),
            valueString=obs.value_text if obs.value_num is None else None,
        )
        entries.append(
            {"fullUrl": f"urn:uuid:{obs.id}", "resource": resource.model_dump(mode="json", exclude_none=True)}
        )

    subject = {"reference": f"urn:uuid:{patient.id}"}
    for problem in problems:
        resource = FhirCondition(
            id=str(problem.id),
            clinicalStatus={
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active" if problem.status == "active" else "resolved",
                    }
                ]
            },
            code={
                "text": problem.description,
                **(
                    {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": problem.icd_code}]}
                    if problem.icd_code
                    else {}
                ),
            },
            subject=subject,
            onsetDateTime=problem.onset_date.isoformat() if problem.onset_date else None,
        )
        entries.append(
            {"fullUrl": f"urn:uuid:{problem.id}", "resource": resource.model_dump(mode="json", exclude_none=True)}
        )

    for medication in medications:
        dosage_text = " ".join(filter(None, (medication.dose, medication.frequency)))
        resource = FhirMedication(
            id=str(medication.id),
            status="active" if medication.active else "stopped",
            medicationCodeableConcept={"text": medication.name},
            subject=subject,
            dosage=[{"text": dosage_text}] if dosage_text else None,
            effectiveDateTime=(
                medication.started_date.isoformat() if medication.started_date else None
            ),
        )
        entries.append(
            {"fullUrl": f"urn:uuid:{medication.id}", "resource": resource.model_dump(mode="json", exclude_none=True)}
        )

    for allergy in allergies:
        resource = FhirAllergy(
            id=str(allergy.id),
            code={"text": allergy.substance},
            patient=subject,
            reaction=(
                [{"manifestation": [{"text": allergy.reaction}], "severity": allergy.severity}]
                if allergy.reaction
                else None
            ),
        )
        entries.append(
            {"fullUrl": f"urn:uuid:{allergy.id}", "resource": resource.model_dump(mode="json", exclude_none=True)}
        )

    bundle = Bundle(type="collection", timestamp=datetime.now(timezone.utc).isoformat(), entry=entries)
    return bundle.model_dump(mode="json", exclude_none=True)


class _ResourceError(Exception):
    pass


def _map_patient(db: Session, resource: dict) -> models.Patient:
    try:
        fhir_patient = FhirPatient.model_validate(resource)
    except ValidationError as exc:
        raise _ResourceError(f"Invalid FHIR Patient: {exc.errors()[0]['msg']}")
    mrn = next(
        (i.value for i in (fhir_patient.identifier or []) if i.value),
        None,
    )
    if mrn is None:
        raise _ResourceError("Patient has no usable identifier (MRN)")
    if not fhir_patient.name:
        raise _ResourceError("Patient has no name")
    name = fhir_patient.name[0]
    first = (name.given or [""])[0]
    last = name.family or ""
    if not first or not last:
        raise _ResourceError("Patient name needs both given and family parts")
    if fhir_patient.birthDate is None:
        raise _ResourceError("Patient has no birthDate")
    sex = fhir_patient.gender or "unknown"

    existing = PatientRepository(db).by_mrn(mrn)
    if existing is not None:
        return existing
    return patient_service.create_patient(
        db,
        first_name=first,
        last_name=last,
        dob=fhir_patient.birthDate,
        sex=sex,
        phone=next((t.value for t in (fhir_patient.telecom or []) if t.value), None),
        email=None,
        address=(fhir_patient.address or [None])[0].text if fhir_patient.address else None,
        history=None,
        mrn=mrn,
        source="fhir",
    )


def _map_observation(
    db: Session,
    resource: dict,
    patient: models.Patient | None,
    encounters: dict[uuid.UUID, models.Encounter],
    label: str,
) -> None:
    try:
        fhir_obs = FhirObservation.model_validate(resource)
    except ValidationError as exc:
        raise _ResourceError(f"Invalid FHIR Observation: {exc.errors()[0]['msg']}")
    if patient is None:
        raise _ResourceError("Observation arrived before any Patient resource")
    coding = (fhir_obs.code.coding or []) if fhir_obs.code else []
    loinc = next((c.code for c in coding if c.code), None)
    obs_type = BY_LOINC.get(loinc) if loinc else None
    if obs_type is None:
        raise _ResourceError(f"Unknown or missing LOINC code: {loinc!r}")

    value_num = None
    value_text = None
    if fhir_obs.valueQuantity is not None and fhir_obs.valueQuantity.value is not None:
        value_num = float(fhir_obs.valueQuantity.value)
    elif fhir_obs.valueString is not None:
        value_text = str(fhir_obs.valueString)
    else:
        raise _ResourceError(f"Observation {obs_type.code} has no valueQuantity or valueString")

    taken_at = fhir_obs.effectiveDateTime or datetime.now(timezone.utc)
    try:
        observation = build_observation(
            patient_id=patient.id,
            code=obs_type.code,
            value_num=value_num,
            value_text=value_text,
            taken_at=taken_at,
            source="fhir",
        )
    except ValueError as exc:
        raise _ResourceError(str(exc))

    if patient.id not in encounters:
        encounter = models.Encounter(
            patient_id=patient.id,
            occurred_at=datetime.now(timezone.utc),
            encounter_type="imported",
            reason=label,
            source="fhir",
        )
        db.add(encounter)
        db.flush()
        encounters[patient.id] = encounter
    encounters[patient.id].observations.append(observation)
    db.flush()


def import_resources(db: Session, user: models.User, label: str, content: str) -> models.ImportBatch:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Not valid JSON: {exc}")

    if payload.get("resourceType") == "Bundle":
        try:
            Bundle.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid FHIR Bundle: {exc.errors()[0]['msg']}")
        resources = [e.get("resource") or {} for e in payload.get("entry") or []]
    else:
        resources = [payload]

    batch = models.ImportBatch(
        label=label, format="fhir", created_by=user.id,
        total_records=0, imported_count=0, error_count=0,
    )
    encounters: dict[uuid.UUID, models.Encounter] = {}
    patient: models.Patient | None = None

    for number, resource in enumerate(resources, start=1):
        batch.total_records += 1
        raw = json.dumps(resource)[:2000]
        try:
            resource_type = resource.get("resourceType")
            if resource_type == "Patient":
                patient = _map_patient(db, resource)
            elif resource_type == "Observation":
                _map_observation(db, resource, patient, encounters, label)
            else:
                raise _ResourceError(f"Unsupported resource type: {resource_type!r}")
            batch.imported_count += 1
        except _ResourceError as exc:
            batch.error_count += 1
            batch.issues.append(
                models.ImportIssue(record_number=number, message=str(exc), raw=raw)
            )

    return ImportRepository(db).add(batch)
