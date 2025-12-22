from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from config.database import get_db
from app.repositories.account_repository import AccountRepository
from app.schemas.account_schema import AccountCreate, AccountResponse, BalanceResponse, ChargeRequest
from app.dependencies import get_current_account
from core.models import Account


router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db)
) -> Account:
    repo = AccountRepository(db)

    existing = await repo.get_by_id(account_data.account_id)
    if existing:
        raise HTTPException(status_code=409, detail="Account already exists")

    try:
        account = await repo.create_with_generated_key(account_data.account_id)
        return account
    except IntegrityError:
        raise HTTPException(status_code=500, detail="Failed to generate unique API key")


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    account: Annotated[Account, Depends(get_current_account)]
) -> BalanceResponse:
    return BalanceResponse(balance=account.balance)


@router.post("/charge", response_model=BalanceResponse)
async def charge_balance(
    charge_data: ChargeRequest,
    account: Annotated[Account, Depends(get_current_account)],
    db: AsyncSession = Depends(get_db)
) -> BalanceResponse:
    repo = AccountRepository(db)
    updated_account = await repo.charge_balance(account.id, charge_data.amount)

    if not updated_account:
        raise HTTPException(status_code=404, detail="Account not found")

    return BalanceResponse(balance=updated_account.balance)
