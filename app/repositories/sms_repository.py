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

    async def list_by_account(
        self,
        account_id: UUID,
        status: Optional[int] = None,
        sms_type: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[SMS], int]:
        query = select(SMS).where(SMS.account_id == account_id)

        if status:
            query = query.where(SMS.status == status)
        if sms_type:
            query = query.where(SMS.sms_type == sms_type)
        if start_date:
            query = query.where(SMS.created_at >= start_date)
        if end_date:
            query = query.where(SMS.created_at <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.order_by(SMS.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total or 0

    async def update_status(
        self,
        sms_id: UUID,
        status: int,
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

    async def batch_update_status(
        self,
        sent_ids: list[UUID],
        failed_ids: list[UUID],
        sent_at: Optional[datetime] = None
    ) -> tuple[int, int]:
        sent_count = 0
        failed_count = 0

        if sent_ids:
            result = await self.db.execute(
                update(SMS)
                .where(SMS.id.in_(sent_ids))
                .values(status=SMSStatus.SENT, sent_at=sent_at)
            )
            sent_count = result.rowcount

        if failed_ids:
            result = await self.db.execute(
                update(SMS)
                .where(SMS.id.in_(failed_ids))
                .values(status=SMSStatus.FAILED)
            )
            failed_count = result.rowcount

        await self.db.commit()
        return sent_count, failed_count
