import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

mods_to_delete = [
    mod for mod in sys.modules
    if mod in ("main", "database", "models", "schemas", "routers")
    or mod.startswith("routers.")
]
for mod in mods_to_delete:
    del sys.modules[mod]
    
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_statements.db"

@pytest.fixture(autouse=True)
def setup_database():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Register override SEBELUM test berjalan
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    yield

    # Cleanup SETELAH test selesai
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture
def client():
    return TestClient(app)

# ── Health Check ──────────────────────────────────────────
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "statement-service"

# ── Create Statement ──────────────────────────────────────
def test_create_statement_success(client):
    payload = {
        "reference_number": "STM-001",
        "account_number": "ACC-123",
        "amount": 500000.0,
        "description": "Transfer masuk",
        "value_date": "2024-01-15T10:00:00"
    }
    response = client.post("/statements/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["reference_number"] == "STM-001"
    assert data["status"] == "PENDING"

def test_create_statement_missing_field(client):
    payload = {
        "account_number": "ACC-123"
        # amount dan reference_number tidak diisi
    }
    response = client.post("/statements/", json=payload)
    assert response.status_code == 422

# ── Get Statements ────────────────────────────────────────
def test_get_all_statements_empty(client):
    response = client.get("/statements/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_statements_filter_by_account(client):
    for i, acc in enumerate(["ACC-AAA", "ACC-BBB"]):
        client.post("/statements/", json={
            "reference_number": f"STM-FILTER-{i}",
            "account_number": acc,
            "amount": 100000.0,
            "description": "Test",
            "value_date": "2024-01-15T10:00:00"
        })
    response = client.get("/statements/?account_number=ACC-AAA")
    assert response.status_code == 200
    assert len(response.json()) == 1

# ── Update Status ─────────────────────────────────────────
def test_update_statement_status(client):
    payload = {
        "reference_number": "STM-STATUS",
        "account_number": "ACC-123",
        "amount": 200000.0,
        "description": "Test status",
        "value_date": "2024-01-15T10:00:00"
    }
    create_resp = client.post("/statements/", json=payload)
    stmt_id = create_resp.json()["id"]

    response = client.patch(f"/statements/{stmt_id}/status?status=MATCHED")
    assert response.status_code == 200
    assert response.json()["status"] == "MATCHED"

def test_update_status_not_found(client):
    response = client.patch("/statements/99999/status?status=MATCHED")
    assert response.status_code == 404