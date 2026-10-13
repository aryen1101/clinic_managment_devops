"""Shared pytest fixtures.

Tests NEVER touch the real PostgreSQL database: DATABASE_URL is pointed at a
throw-away SQLite file *before* the app is imported, and every test starts
with freshly created, empty tables.
"""
import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "clinic_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def doctor(client):
    response = client.post("/api/doctors", json={
        "full_name": "Dr. Test Doctor",
        "specialization": "Cardiology",
        "phone": "+91 98100 00000",
        "email": "test.doctor@clinic.local",
        "consultation_fee": 700,
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def patient(client):
    response = client.post("/api/patients", json={
        "full_name": "Test Patient",
        "date_of_birth": "1990-05-20",
        "gender": "FEMALE",
        "phone": "+91 90000 00000",
        "blood_group": "O+",
    })
    assert response.status_code == 201
    return response.json()
