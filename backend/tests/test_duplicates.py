from datetime import date

from app.db import models
from app.services import duplicates
from tests.conftest import add_observation, make_patient


def test_scan_flags_same_name_and_dob(db):
    a = make_patient(db, first_name="Maria", last_name="Silva", dob=date(1970, 3, 1), source="manual")
    make_patient(db, first_name="Maria", last_name="Silva", dob=date(1970, 3, 1), source="hl7")
    make_patient(db, first_name="Other", last_name="Person", dob=date(1980, 1, 1))

    assert duplicates.scan(db) == 1
    flag = db.query(models.DuplicateFlag).one()
    assert flag.status == "pending"
    assert "across sources" in flag.reason
    assert a.id in (flag.patient_a_id, flag.patient_b_id)


def test_scan_does_not_reflag_reviewed_pairs(db):
    make_patient(db, first_name="Ana", last_name="Costa", dob=date(1960, 5, 5))
    make_patient(db, first_name="Ana", last_name="Costa", dob=date(1960, 5, 5))
    assert duplicates.scan(db) == 1
    flag = db.query(models.DuplicateFlag).one()
    duplicates.dismiss(db, flag)
    assert duplicates.scan(db) == 0  # dismissed pair stays dismissed


def test_merge_moves_data_and_hides_tombstone(db):
    keep = make_patient(db, first_name="Leo", last_name="Kim", dob=date(1955, 2, 2), phone=None)
    dupe = make_patient(db, first_name="Leo", last_name="Kim", dob=date(1955, 2, 2), source="csv")
    dupe.phone = "555-1234"
    add_observation(db, dupe, "glucose", 140)
    db.commit()
    duplicates.scan(db)
    flag = db.query(models.DuplicateFlag).one()
    # normalize direction: merge into `keep`
    if flag.patient_a_id != keep.id:
        flag.patient_a_id, flag.patient_b_id = flag.patient_b_id, flag.patient_a_id
        db.commit()
        flag = db.query(models.DuplicateFlag).one()

    survivor = duplicates.merge(db, flag)

    assert survivor.id == keep.id
    assert survivor.phone == "555-1234"  # missing fields filled from the duplicate
    assert db.query(models.Observation).filter_by(patient_id=keep.id).count() == 1
    absorbed = db.get(models.Patient, flag.patient_b_id)
    assert absorbed.merged_into_id == keep.id
    assert flag.status == "merged"
    # tombstone is excluded from future scans
    assert duplicates.scan(db) == 0


def test_fuzzy_tier_catches_first_letter_typos(db):
    make_patient(db, first_name="Sofia", last_name="Costa", dob=date(1972, 9, 9))
    make_patient(db, first_name="oSfia", last_name="Costa", dob=date(1972, 9, 9), source="csv")

    assert duplicates.scan(db, fuzzy=False, dob_window_days=0) == 0  # baseline misses it
    assert duplicates.scan(db) == 1
    flag = db.query(models.DuplicateFlag).one()
    assert "Nearly identical name" in flag.reason


def test_dob_window_tier_catches_shifted_dates(db):
    make_patient(db, first_name="Victor", last_name="Khan", dob=date(1980, 6, 15))
    make_patient(db, first_name="Victor", last_name="Khan", dob=date(1980, 6, 16), source="hl7")

    assert duplicates.scan(db, fuzzy=False, dob_window_days=0) == 0
    assert duplicates.scan(db) == 1
    flag = db.query(models.DuplicateFlag).one()
    assert "1 day(s) apart" in flag.reason


def test_fuzzy_tier_leaves_distinct_names_alone(db):
    make_patient(db, first_name="Maria", last_name="Silva", dob=date(1970, 1, 1))
    make_patient(db, first_name="Elena", last_name="Nguyen", dob=date(1970, 1, 1))
    assert duplicates.scan(db) == 0


def test_short_names_require_exact_match(db):
    make_patient(db, first_name="Al", last_name="Bo", dob=date(1970, 1, 1))
    make_patient(db, first_name="Al", last_name="Ba", dob=date(1970, 1, 1))
    # 'Al Bo' vs 'Al Ba' would pass an edit-distance check, but short names
    # are held to exact matching to avoid noise.
    assert duplicates.scan(db) == 0


def test_summary_merges_sources(db):
    patient = make_patient(db, source="manual")
    add_observation(db, patient, "heart_rate", 70)
    summary = duplicates.patient_summary(db, patient)
    sources = {s["source"] for s in summary["sources"]}
    assert "manual" in sources
    assert len(summary["latest_observations"]) == 1
