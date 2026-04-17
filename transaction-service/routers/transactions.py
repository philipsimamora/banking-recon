from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import schemas, models
from database import get_db

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=schemas.TransactionResponse)
def create_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Transaction).filter(
        models.Transaction.reference_number == tx.reference_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Reference number already exists")
    
    db_tx = models.Transaction(**tx.dict())
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

@router.get("/", response_model=List[schemas.TransactionResponse])
def get_transactions(
    account_number: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Transaction)
    if account_number:
        query = query.filter(models.Transaction.account_number == account_number)
    if status:
        query = query.filter(models.Transaction.status == status)
    return query.all()

@router.patch("/{tx_id}/status")
def update_status(tx_id: int, status: str, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.status = status
    db.commit()
    return {"message": "Status updated", "id": tx_id, "status": status}