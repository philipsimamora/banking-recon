import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reconciler import run_reconciliation

# ── Mock Data ─────────────────────────────────────────────
MOCK_TRANSACTIONS = [
    {"id": 1, "reference_number": "TXN-001", "account_number": "ACC-123",
     "amount": 500000.0, "status": "PENDING"},
    {"id": 2, "reference_number": "TXN-002", "account_number": "ACC-123",
     "amount": 250000.0, "status": "PENDING"},
    {"id": 3, "reference_number": "TXN-003", "account_number": "ACC-123",
     "amount": 100000.0, "status": "PENDING"},
]

MOCK_STATEMENTS = [
    {"id": 1, "reference_number": "TXN-001", "account_number": "ACC-123",
     "amount": 500000.0, "status": "PENDING"},
    {"id": 2, "reference_number": "TXN-002", "account_number": "ACC-123",
     "amount": 250000.0, "status": "PENDING"},
    # TXN-003 tidak ada di statement → unmatched
]

# ── Test Cases ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_reconciliation_matched():
    with patch("reconciler.fetch_transactions", new=AsyncMock(return_value=MOCK_TRANSACTIONS)), \
         patch("reconciler.fetch_statements", new=AsyncMock(return_value=MOCK_STATEMENTS)), \
         patch("reconciler.update_transaction_status", new=AsyncMock()), \
         patch("reconciler.update_statement_status", new=AsyncMock()):

        result = await run_reconciliation("ACC-123")

        assert result["summary"]["matched"] == 2
        assert result["summary"]["unmatched_transactions"] == 1
        assert result["summary"]["unmatched_statements"] == 0

@pytest.mark.asyncio
async def test_reconciliation_all_matched():
    statements_full = MOCK_STATEMENTS + [
        {"id": 3, "reference_number": "TXN-003", "account_number": "ACC-123",
         "amount": 100000.0, "status": "PENDING"}
    ]
    with patch("reconciler.fetch_transactions", new=AsyncMock(return_value=MOCK_TRANSACTIONS)), \
         patch("reconciler.fetch_statements", new=AsyncMock(return_value=statements_full)), \
         patch("reconciler.update_transaction_status", new=AsyncMock()), \
         patch("reconciler.update_statement_status", new=AsyncMock()):

        result = await run_reconciliation("ACC-123")

        assert result["summary"]["matched"] == 3
        assert result["summary"]["unmatched_transactions"] == 0
        assert result["summary"]["match_rate"] == "100.0%"

@pytest.mark.asyncio
async def test_reconciliation_empty_data():
    with patch("reconciler.fetch_transactions", new=AsyncMock(return_value=[])), \
         patch("reconciler.fetch_statements", new=AsyncMock(return_value=[])), \
         patch("reconciler.update_transaction_status", new=AsyncMock()), \
         patch("reconciler.update_statement_status", new=AsyncMock()):

        result = await run_reconciliation()

        assert result["summary"]["matched"] == 0
        assert result["summary"]["match_rate"] == "0.0%"

@pytest.mark.asyncio
async def test_reconciliation_amount_mismatch():
    transactions = [
        {"id": 1, "reference_number": "TXN-AMT", "account_number": "ACC-123",
         "amount": 500000.0, "status": "PENDING"}
    ]
    statements = [
        {"id": 1, "reference_number": "TXN-AMT", "account_number": "ACC-123",
         "amount": 499000.0,  # beda amount → tidak match
         "status": "PENDING"}
    ]
    with patch("reconciler.fetch_transactions", new=AsyncMock(return_value=transactions)), \
         patch("reconciler.fetch_statements", new=AsyncMock(return_value=statements)), \
         patch("reconciler.update_transaction_status", new=AsyncMock()), \
         patch("reconciler.update_statement_status", new=AsyncMock()):

        result = await run_reconciliation()
        assert result["summary"]["matched"] == 0
        assert result["summary"]["unmatched_transactions"] == 1