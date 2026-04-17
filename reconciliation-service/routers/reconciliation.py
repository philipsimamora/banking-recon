from fastapi import APIRouter
from reconciler import run_reconciliation
from typing import Optional

router = APIRouter(prefix="/reconcile", tags=["Reconciliation"])

@router.post("/run")
async def run(account_number: Optional[str] = None):
    result = await run_reconciliation(account_number)
    return result

@router.get("/summary")
async def summary(account_number: Optional[str] = None):
    result = await run_reconciliation(account_number)
    return result["summary"]