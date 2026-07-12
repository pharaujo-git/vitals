from app.db import models
from app.services import ingestion
from tests.conftest import make_user

CSV_HEADER = "mrn,first_name,last_name,dob,sex,code,value,taken_at"


def test_csv_import_maps_patients_and_observations(db):
    user = make_user(db, "admin")
    content = "\n".join([
        CSV_HEADER,
        "MRN-C1,Jane,Doe,1975-04-02,f,bp_systolic,152,2026-07-01T09:15:00",
        "MRN-C1,Jane,Doe,1975-04-02,f,glucose,131,2026-07-01T09:20:00",
        "MRN-C2,John,Roe,1990-11-23,m,,,",
    ])
    batch = ingestion.import_csv(db, user, "unit test", content)

    assert batch.total_records == 3
    assert batch.imported_count == 3
    assert batch.error_count == 0
    patients = db.query(models.Patient).filter(models.Patient.source == "csv").all()
    assert {p.mrn for p in patients} == {"MRN-C1", "MRN-C2"}
    observations = db.query(models.Observation).filter_by(source="csv").all()
    assert len(observations) == 2


def test_csv_errors_reported_not_dropped(db):
    user = make_user(db, "admin")
    content = "\n".join([
        CSV_HEADER,
        "MRN-E1,Bad,Date,notadate,m,,,",
        "MRN-E2,Jane,Doe,1975-04-02,f,cholesterol,220,",
        "MRN-E3,Jane,Doe,1975-04-02,f,heart_rate,900,",
        ",Missing,Mrn,1980-01-01,f,,,",
    ])
    batch = ingestion.import_csv(db, user, "unit test", content)

    assert batch.total_records == 4
    assert batch.imported_count == 0
    assert batch.error_count == 4
    messages = [issue.message for issue in batch.issues]
    assert any("dob" in m for m in messages)
    assert any("Unknown observation code" in m for m in messages)
    assert any("above the plausible range" in m for m in messages)
    assert any("Missing mrn" in m for m in messages)
    # raw source data is preserved on every issue
    assert all(issue.raw for issue in batch.issues)


def test_csv_upsert_by_mrn_never_duplicates(db):
    user = make_user(db, "admin")
    row = "MRN-U1,Jane,Doe,1975-04-02,f,,,"
    ingestion.import_csv(db, user, "first", f"{CSV_HEADER}\n{row}")
    ingestion.import_csv(db, user, "second", f"{CSV_HEADER}\n{row}")
    assert db.query(models.Patient).filter_by(mrn="MRN-U1").count() == 1


def test_hl7_import_and_unknown_loinc(db):
    user = make_user(db, "admin")
    content = "\n".join([
        "MSH|^~\\&|LAB|20260701120000",
        "PID|MRN-H1|Souza^Carlos|19621108|M",
        "OBX|8867-4|88|bpm|20260701120000",
        "OBX|9999-9|161|mmHg|20260701120000",
    ])
    batch = ingestion.import_hl7(db, user, "unit test", content)

    assert batch.imported_count == 2  # PID + one good OBX
    assert batch.error_count == 1
    assert "Unknown LOINC code" in batch.issues[0].message
    patient = db.query(models.Patient).filter_by(mrn="MRN-H1").one()
    assert patient.first_name == "Carlos"
    assert patient.source == "hl7"


def test_hl7_obx_before_pid_is_an_error(db):
    user = make_user(db, "admin")
    batch = ingestion.import_hl7(db, user, "unit test", "OBX|8867-4|88|bpm")
    assert batch.error_count == 1
    assert "before any PID" in batch.issues[0].message
