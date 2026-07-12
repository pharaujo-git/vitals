import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.db.session import get_db
from app.main import app
from tests.conftest import make_user


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_header(user):
    return {"Authorization": f"Bearer {security.create_access_token(user)}"}


def test_unauthenticated_requests_rejected(client):
    assert client.get("/api/patients").status_code == 401
    assert client.get("/api/audit").status_code == 401


def test_front_desk_cannot_create_patients(client, db):
    front = make_user(db, "front_desk")
    response = client.post(
        "/api/patients",
        headers=auth_header(front),
        json={"firstName": "No", "lastName": "Access", "dob": "1990-01-01"},
    )
    assert response.status_code == 403


def test_manager_cannot_read_patient_list(client, db):
    manager = make_user(db, "manager")
    assert client.get("/api/patients", headers=auth_header(manager)).status_code == 403


def test_manager_reads_dashboard_front_desk_does_not(client, db):
    manager = make_user(db, "manager")
    front = make_user(db, "front_desk")
    assert client.get("/api/dashboard", headers=auth_header(manager)).status_code == 200
    assert client.get("/api/dashboard", headers=auth_header(front)).status_code == 403


def test_audit_log_is_admin_only(client, db):
    clinician = make_user(db, "clinician")
    admin = make_user(db, "admin")
    assert client.get("/api/audit", headers=auth_header(clinician)).status_code == 403
    assert client.get("/api/audit", headers=auth_header(admin)).status_code == 200


def test_manager_cohort_is_deidentified(client, db):
    manager = make_user(db, "manager")
    admin = make_user(db, "admin")
    manager_columns = client.get(
        "/api/reports/cohort", headers=auth_header(manager)
    ).json()["columns"]
    admin_columns = client.get("/api/reports/cohort", headers=auth_header(admin)).json()["columns"]
    assert "mrn" not in manager_columns
    assert "first_name" not in manager_columns
    assert "mrn" in admin_columns
