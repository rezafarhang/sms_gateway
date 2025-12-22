from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    account_id: UUID = Field(..., description="Unique account identifier from main service")


class AccountResponse(BaseModel):
    id: UUID
    api_key: str
    balance: int
    created_at: datetime

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    balance: int


class ChargeRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount to charge (must be positive)")
