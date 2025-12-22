from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from app.repositories.sms_repository import SMSRepository
from app.repositories.account_repository import AccountRepository
from app.schemas.sms_schema import SMSSendRequest, SMSResponse
from app.dependencies import get_current_account
from core.models import Account, SMS
from core.publisher import SMSPublisher


router = APIRouter(prefix="/sms", tags=["sms"])


@router.post("/send", response_model=SMSResponse, status_code=201)
async def send_sms(
    sms_data: SMSSendRequest,
    account: Annotated[Account, Depends(get_current_account)],
    db: AsyncSession = Depends(get_db)
) -> SMS:
    account_repo = AccountRepository(db)
    sms_repo = SMSRepository(db)

    if account.balance < 1:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    success = await account_repo.deduct_balance(account.id, 1)
    if not success:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    sms = await sms_repo.create(
        account_id=account.id,
        phone_number=sms_data.phone_number,
        message=sms_data.message,
        sms_type=sms_data.sms_type
    )

    SMSPublisher.publish_sms(
        sms_id=sms.id,
        account_id=sms.account_id,
        phone_number=sms.phone_number,
        message=sms.message,
        sms_type=sms.sms_type
    )

    return sms


@router.get("/{sms_id}", response_model=SMSResponse)
async def get_sms(
    sms_id: UUID,
    account: Annotated[Account, Depends(get_current_account)],
    db: AsyncSession = Depends(get_db)
) -> SMS:
    sms_repo = SMSRepository(db)
    sms = await sms_repo.get_by_id(sms_id)

    if not sms:
        raise HTTPException(status_code=404, detail="SMS not found")

    if sms.account_id != account.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return sms
