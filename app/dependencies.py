from typing import Annotated
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from app.repositories.account_repository import AccountRepository
from core.models import Account


async def get_current_account(
    x_api_key: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db)
) -> Account:
    repo = AccountRepository(db)
    account = await repo.get_by_api_key(x_api_key)

    if not account:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return account
