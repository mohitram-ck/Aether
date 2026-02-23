from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TransactionCreate(BaseModel):
    amount: float
    currency: str = "USD"
    merchant: str
    location: Optional[str] = None

class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount: float
    currency: str
    merchant: str
    location: Optional[str]
    status: str
    is_flagged: bool
    created_at: datetime

    class Config:
        from_attributes = True