import logging
from datetime import datetime
from uuid import UUID
from celery import Task
from workers.celery_app import celery_app
from workers.operator_client import OperatorClient
from core.consts import SMSStatus

logger = logging.getLogger(__name__)


class SMSTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@celery_app.task(base=SMSTask, name="workers.tasks.sms_tasks.process_sms")
def process_sms(sms_id: str, account_id: str, phone_number: str, message: str, sms_type: int):
    """
    Process SMS by sending to operator and updating status.
    Runs asynchronously in Celery worker.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from config.settings import settings
    from app.repositories.sms_repository import SMSRepository

    async def _process():
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            repo = SMSRepository(session)

            # Send SMS through operators with failover
            success, message_id, error = await OperatorClient.send_sms(phone_number, message)

            if success:
                await repo.update_status(
                    sms_id=UUID(sms_id),
                    status=SMSStatus.SENT,
                    sent_at=datetime.utcnow()
                )
                logger.info(f"SMS {sms_id} sent successfully, message_id: {message_id}")
            else:
                await repo.update_status(
                    sms_id=UUID(sms_id),
                    status=SMSStatus.FAILED
                )
                logger.error(f"SMS {sms_id} failed: {error}")

        await engine.dispose()

    asyncio.run(_process())
