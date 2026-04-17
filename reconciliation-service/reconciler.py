import httpx
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

TRANSACTION_SERVICE_URL = "http://localhost:8001"
STATEMENT_SERVICE_URL = "http://localhost:8002"

async def fetch_transactions(account_number: Optional[str] = None) -> List[Dict]:
    params = {}
    if account_number:
        params["account_number"] = account_number
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{TRANSACTION_SERVICE_URL}/transactions/",
                params=params
            )
            print(f"[Transaction Service] Status: {response.status_code}")
            print(f"[Transaction Service] Body: {response.text}")
            
            response.raise_for_status()  # raise error jika status 4xx/5xx
            
            if not response.text.strip():
                return []  # kembalikan list kosong jika response kosong
            
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Transaction Service tidak dapat dihubungi. Pastikan service berjalan di port 8001."
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Transaction Service error: {e.response.status_code} - {e.response.text}"
        )

async def fetch_statements(account_number: Optional[str] = None) -> List[Dict]:
    params = {}
    if account_number:
        params["account_number"] = account_number
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{STATEMENT_SERVICE_URL}/statements/",
                params=params
            )
            print(f"[Statement Service] Status: {response.status_code}")
            print(f"[Statement Service] Body: {response.text}")
            
            response.raise_for_status()
            
            if not response.text.strip():
                return []
            
            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Statement Service tidak dapat dihubungi. Pastikan service berjalan di port 8002."
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Statement Service error: {e.response.status_code} - {e.response.text}"
        )

async def update_transaction_status(tx_id: int, status: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.patch(
            f"{TRANSACTION_SERVICE_URL}/transactions/{tx_id}/status",
            params={"status": status}
        )

async def update_statement_status(stmt_id: int, status: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.patch(
            f"{STATEMENT_SERVICE_URL}/statements/{stmt_id}/status",
            params={"status": status}
        )

async def run_reconciliation(account_number: Optional[str] = None) -> Dict[str, Any]:
    transactions = await fetch_transactions(account_number)
    statements = await fetch_statements(account_number)

    pending_tx = [t for t in transactions if t["status"] == "PENDING"]
    pending_stmt = [s for s in statements if s["status"] == "PENDING"]

    matched = []
    unmatched_transactions = []
    unmatched_statements = []
    used_stmt_ids = set()

    for tx in pending_tx:
        match_found = None
        for stmt in pending_stmt:
            if stmt["id"] in used_stmt_ids:
                continue
            if (
                tx["reference_number"] == stmt["reference_number"]
                and abs(tx["amount"] - stmt["amount"]) < 0.01
            ):
                match_found = stmt
                break

        if match_found:
            used_stmt_ids.add(match_found["id"])
            await update_transaction_status(tx["id"], "MATCHED")
            await update_statement_status(match_found["id"], "MATCHED")
            matched.append({
                "transaction_ref": tx["reference_number"],
                "statement_ref": match_found["reference_number"],
                "amount": tx["amount"],
                "status": "MATCHED"
            })
        else:
            await update_transaction_status(tx["id"], "UNMATCHED")
            unmatched_transactions.append({
                "reference": tx["reference_number"],
                "amount": tx["amount"],
                "reason": "No matching statement found"
            })

    for stmt in pending_stmt:
        if stmt["id"] not in used_stmt_ids:
            await update_statement_status(stmt["id"], "UNMATCHED")
            unmatched_statements.append({
                "reference": stmt["reference_number"],
                "amount": stmt["amount"],
                "reason": "No matching transaction found"
            })

    return {
        "summary": {
            "total_transactions": len(pending_tx),
            "total_statements": len(pending_stmt),
            "matched": len(matched),
            "unmatched_transactions": len(unmatched_transactions),
            "unmatched_statements": len(unmatched_statements),
            "match_rate": f"{(len(matched) / max(len(pending_tx), 1)) * 100:.1f}%"
        },
        "matched": matched,
        "unmatched_transactions": unmatched_transactions,
        "unmatched_statements": unmatched_statements
    }