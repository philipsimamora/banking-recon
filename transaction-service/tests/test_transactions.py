import pytest
import importlib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, os

for mod in ["main", "database", "models", "schemas"]:
    sys.modules.pop(mod, None)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db


# Gunakan database in-memory untuk testing
TEST_DATABASE_URL = "sqlite:///./test_transactions.db"

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
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "transaction-service"

# ── Create Transaction ────────────────────────────────────
def test_create_transaction_success(client):
    payload = {
        "reference_number": "TXN-001",
        "account_number": "ACC-123",
        "amount": 500000.0,
        "transaction_type": "DEBIT",
        "description": "Transfer keluar",
        "transaction_date": "2024-01-15T10:00:00"
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["reference_number"] == "TXN-001"
    assert data["amount"] == 500000
    assert data["status"] == "PENDING"

def test_create_transaction_duplicate_reference(client):
    payload = {
        "reference_number": "TXN-DUPLICATE",
        "account_number": "ACC-123",
        "amount": 100000.0,
        "transaction_type": "CREDIT",
        "description": "Test duplikat",
        "transaction_date": "2024-01-15T10:00:00"
    }
    client.post("/transactions/", json=payload)
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_create_transaction_missing_field(client):
    payload = {
        "account_number": "ACC-123",
        "amount": 100000.0
        # reference_number dan transaction_type tidak diisi
    }
    response = client.post("/transactions/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity

# ── Get Transactions ──────────────────────────────────────
def test_get_all_transactions_empty(client):
    response = client.get("/transactions/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_transactions_after_insert(client):
    payload = {
        "reference_number": "TXN-002",
        "account_number": "ACC-456",
        "amount": 250000.0,
        "transaction_type": "CREDIT",
        "description": "Top up",
        "transaction_date": "2024-01-16T09:00:00"
    }
    client.post("/transactions/", json=payload)
    response = client.get("/transactions/")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_transactions_filter_by_account(client):
    for i, acc in enumerate(["ACC-111", "ACC-222"]):
        client.post("/transactions/", json={
            "reference_number": f"TXN-FILTER-{i}",
            "account_number": acc,
            "amount": 100000.0,
            "transaction_type": "DEBIT",
            "description": "Test filter",
            "transaction_date": "2024-01-15T10:00:00"
        })
    response = client.get("/transactions/?account_number=ACC-111")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["account_number"] == "ACC-111"

# ── Update Status ─────────────────────────────────────────
def test_update_transaction_status(client):
    payload = {
        "reference_number": "TXN-STATUS",
        "account_number": "ACC-789",
        "amount": 75000.0,
        "transaction_type": "DEBIT",
        "description": "Test update status",
        "transaction_date": "2024-01-15T10:00:00"
    }
    create_resp = client.post("/transactions/", json=payload)
    tx_id = create_resp.json()["id"]

    response = client.patch(f"/transactions/{tx_id}/status?status=MATCHED")
    assert response.status_code == 200
    assert response.json()["status"] == "MATCHED"

def test_update_status_not_found(client):
    response = client.patch("/transactions/99999/status?status=MATCHED")
    assert response.status_code == 404