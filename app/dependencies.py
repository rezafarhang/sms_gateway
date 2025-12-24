import json
from typing import Annotated
from uuid import UUID
from datetime import datetime
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from config.redis import get_redis
from app.repositories.account_repository import AccountRepository
from core.models import Account


async def get_current_account(
    x_api_key: Annotated[str, Header()],
    db: AsyncSession = Depends(get_db)
) -> Account:
    redis = await get_redis()
    cache_key = f"account:apikey:{x_api_key}"
    cached_data = await redis.get(cache_key)

    if cached_data:
        data = json.loads(cached_data)
        account = Account(
            id=UUID(data['id']),
            api_key=data['api_key'],
            balance=data['balance'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        # Use merge to attach existing object to session without INSERT
        return await db.merge(account)

    repo = AccountRepository(db)
    account = await repo.get_by_api_key(x_api_key)

    if not account:
        raise HTTPException(status_code=401, detail="Invalid API key")

    account_data = {
        'id': str(account.id),
        'api_key': account.api_key,
        'balance': account.balance,
        'created_at': account.created_at.isoformat()
    }
    await redis.setex(cache_key, 12 * 60 * 60, json.dumps(account_data))

    return account
