from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from app.repositories.sms_repository import SMSRepository
from app.repositories.account_repository import AccountRepository
from app.schemas.sms_schema import SMSSendRequest, SMSResponse, SMSListResponse
from app.dependencies import get_current_account
from app.services.sms_service import SMSService
from core.models import Account, SMS


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

    SMSService.publish_to_queue(
        sms_id=sms.id,
        account_id=sms.account_id,
        phone_number=sms.phone_number,
        message=sms.message,
        sms_type=sms.sms_type
    )

    return sms


@router.get("", response_model=SMSListResponse)
async def list_sms(
    account: Annotated[Account, Depends(get_current_account)],
    db: AsyncSession = Depends(get_db),
    status: Optional[int] = Query(None, description="Filter by status (1=pending, 2=sent, 3=failed)"),
    sms_type: Optional[int] = Query(None, description="Filter by type (1=regular, 2=express)"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
) -> SMSListResponse:

    sms_repo = SMSRepository(db)
    skip = (page - 1) * page_size

    items, total = await sms_repo.list_by_account(
        account_id=account.id,
        status=status,
        sms_type=sms_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size
    )

    return SMSListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


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
