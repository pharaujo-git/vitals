"""The observation catalog: known codes with units and physiologic ranges.

Every observation entering the store — typed in, imported from CSV/HL7 or
FHIR — passes through validate() so type and range errors are caught at the
boundary rather than polluting analytics downstream.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservationType:
    code: str
    label: str
    kind: str  # "numeric" | "text"
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    loinc: str | None = None  # LOINC code used in FHIR import/export


CATALOG: dict[str, ObservationType] = {
    t.code: t
    for t in (
        ObservationType("heart_rate", "Heart rate", "numeric", "bpm", 20, 300, "8867-4"),
        ObservationType("bp_systolic", "Systolic blood pressure", "numeric", "mmHg", 50, 260, "8480-6"),
        ObservationType("bp_diastolic", "Diastolic blood pressure", "numeric", "mmHg", 30, 160, "8462-4"),
        ObservationType("temperature", "Body temperature", "numeric", "°C", 30.0, 45.0, "8310-5"),
        ObservationType("resp_rate", "Respiratory rate", "numeric", "breaths/min", 4, 60, "9279-1"),
        ObservationType("spo2", "Oxygen saturation", "numeric", "%", 50, 100, "59408-5"),
        ObservationType("weight", "Body weight", "numeric", "kg", 1, 400, "29463-7"),
        ObservationType("height", "Body height", "numeric", "cm", 30, 250, "8302-2"),
        ObservationType("bmi", "Body mass index", "numeric", "kg/m²", 8, 80, "39156-5"),
        ObservationType("glucose", "Glucose (fasting)", "numeric", "mg/dL", 20, 600, "1558-6"),
        ObservationType("hba1c", "Hemoglobin A1c", "numeric", "%", 3, 20, "4548-4"),
        ObservationType("note", "Clinical note", "text", None, None, None, "48767-8"),
    )
}

BY_LOINC: dict[str, ObservationType] = {t.loinc: t for t in CATALOG.values() if t.loinc}


def validate(code: str, value_num: float | None, value_text: str | None) -> ObservationType:
    """Check an observation's code, value type and range; return its catalog type."""
    obs_type = CATALOG.get(code)
    if obs_type is None:
        raise ValueError(f"Unknown observation code: {code}")
    if obs_type.kind == "numeric":
        if value_num is None:
            raise ValueError(f"{obs_type.label} requires a numeric value")
        if obs_type.min_value is not None and value_num < obs_type.min_value:
            raise ValueError(
                f"{obs_type.label} of {value_num} {obs_type.unit} is below the "
                f"plausible range ({obs_type.min_value}–{obs_type.max_value})"
            )
        if obs_type.max_value is not None and value_num > obs_type.max_value:
            raise ValueError(
                f"{obs_type.label} of {value_num} {obs_type.unit} is above the "
                f"plausible range ({obs_type.min_value}–{obs_type.max_value})"
            )
    else:
        if not value_text or not value_text.strip():
            raise ValueError(f"{obs_type.label} requires a text value")
        if value_num is not None:
            raise ValueError(f"{obs_type.label} takes text, not a number")
    return obs_type
