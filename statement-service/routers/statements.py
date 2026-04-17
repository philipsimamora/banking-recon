from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import models
from database import get_db
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/statements", tags=["Bank Statements"])

class StatementCreate(BaseModel):
    reference_number: str
    account_number: str
    amount: float
    description: Optional[str] = None
    value_date: datetime

class StatementResponse(StatementCreate):
    id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

@router.post("/", response_model=StatementResponse)
def create_statement(stmt: StatementCreate, db: Session = Depends(get_db)):
    db_stmt = models.BankStatement(**stmt.dict())
    db.add(db_stmt)
    db.commit()
    db.refresh(db_stmt)
    return db_stmt

@router.get("/", response_model=List[StatementResponse])
def get_statements(account_number: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.BankStatement)
    if account_number:
        query = query.filter(models.BankStatement.account_number == account_number)
    return query.all()

@router.patch("/{stmt_id}/status")
def update_status(stmt_id: int, status: str, db: Session = Depends(get_db)):
    stmt = db.query(models.BankStatement).filter(models.BankStatement.id == stmt_id).first()
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    stmt.status = status
    db.commit()
    return {"message": "Updated", "id": stmt_id, "status": status}