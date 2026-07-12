import pytest

from app.services import observations


def test_valid_numeric_observation_passes():
    obs_type = observations.validate("heart_rate", 72, None)
    assert obs_type.unit == "bpm"


def test_value_above_range_rejected():
    with pytest.raises(ValueError, match="above the plausible range"):
        observations.validate("heart_rate", 900, None)


def test_value_below_range_rejected():
    with pytest.raises(ValueError, match="below the plausible range"):
        observations.validate("bp_systolic", 10, None)


def test_unknown_code_rejected():
    with pytest.raises(ValueError, match="Unknown observation code"):
        observations.validate("cholesterol", 200, None)


def test_numeric_code_requires_number():
    with pytest.raises(ValueError, match="requires a numeric value"):
        observations.validate("glucose", None, "high")


def test_text_observation_requires_text():
    with pytest.raises(ValueError, match="requires a text value"):
        observations.validate("note", None, "  ")
    obs_type = observations.validate("note", None, "Patient doing well.")
    assert obs_type.kind == "text"


def test_loinc_index_covers_catalog():
    assert observations.BY_LOINC["8867-4"].code == "heart_rate"
