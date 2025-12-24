from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class SMSSendRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=70)
    sms_type: int = Field(default=1, ge=1, le=2, description="1=regular, 2=express")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        if not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('phone_number must contain only digits, spaces, hyphens, or plus sign')
        return v


class SMSResponse(BaseModel):
    id: UUID
    account_id: UUID
    phone_number: str
    message: str
    sms_type: int
    status: int
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SMSListResponse(BaseModel):
    items: list[SMSResponse]
    total: int
    page: int
    page_size: int
