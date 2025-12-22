import secrets
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.models import Account


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_with_generated_key(self, account_id: UUID) -> Account:
        # Generate unique API key with retry logic to handle race conditions
        # Database UNIQUE constraint on api_key prevents concurrent creation conflicts
        max_retries = 5
        for attempt in range(max_retries):
            api_key = secrets.token_urlsafe(32)
            try:
                account = Account(id=account_id, api_key=api_key)
                self.db.add(account)
                await self.db.commit()
                await self.db.refresh(account)
                return account
            except IntegrityError:
                # Extremely rare: UNIQUE constraint violation on api_key, retry with new key
                await self.db.rollback()
                if attempt == max_retries - 1:
                    raise

        raise Exception("Failed to create account after retries")

    async def get_by_api_key(self, api_key: str) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(Account.api_key == api_key)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, account_id: UUID) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()

    async def charge_balance(self, account_id: UUID, amount: int) -> Optional[Account]:
        # Atomic update: Account.balance + amount generates SQL "SET balance = balance + amount"
        # This prevents race conditions during concurrent balance updates
        await self.db.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(balance=Account.balance + amount)
        )
        await self.db.commit()
        return await self.get_by_id(account_id)

    async def deduct_balance(self, account_id: UUID, amount: int) -> bool:
        # Atomic compare-and-swap: checks balance >= amount and deducts in single SQL operation
        # This prevents race conditions and ensures balance never goes negative
        result = await self.db.execute(
            update(Account)
            .where(Account.id == account_id, Account.balance >= amount)
            .values(balance=Account.balance - amount)
        )
        await self.db.commit()
        return result.rowcount > 0
