from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import SMS
from core.consts import SMSStatus


class SMSRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        account_id: UUID,
        phone_number: str,
        message: str,
        sms_type: int
    ) -> SMS:
        sms = SMS(
            account_id=account_id,
            phone_number=phone_number,
            message=message,
            sms_type=sms_type,
            status=SMSStatus.PENDING
        )
        self.db.add(sms)
        await self.db.commit()
        await self.db.refresh(sms)
        return sms

    async def get_by_id(self, sms_id: UUID) -> Optional[SMS]:
        result = await self.db.execute(
            select(SMS).where(SMS.id == sms_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        sms_id: UUID,
        status: str,
        sent_at: Optional[datetime] = None
    ) -> Optional[SMS]:
        values = {"status": status}
        if sent_at:
            values["sent_at"] = sent_at

        await self.db.execute(
            update(SMS)
            .where(SMS.id == sms_id)
            .values(**values)
        )
        await self.db.commit()
        return await self.get_by_id(sms_id)
