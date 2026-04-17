from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class StatementStatus(str, enum.Enum):
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"

class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String, unique=True, index=True)
    account_number = Column(String, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String)
    value_date = Column(DateTime)
    status = Column(Enum(StatementStatus), default=StatementStatus.PENDING)
    created_at = Column(DateTime, server_default=func.now())