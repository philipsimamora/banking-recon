from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"

class TransactionCreate(BaseModel):
    reference_number: str
    account_number: str
    amount: float
    transaction_type: TransactionType
    description: Optional[str] = None
    transaction_date: datetime

class TransactionResponse(TransactionCreate):
    id: int
    status: TransactionStatus
    created_at: datetime

    class Config:
        from_attributes = True