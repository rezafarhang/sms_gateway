import logging
import asyncio
import json
import redis.asyncio as redis
from celery import Task
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import UUID
from workers.celery_app import celery_app
from workers.operator_client import OperatorClient
from core.consts import SMSStatus
from config.settings import settings
from app.repositories.sms_repository import SMSRepository

logger = logging.getLogger(__name__)


class SMSTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):

        celery_app.send_task(
            'workers.tasks.dlq_tasks.store_failed_task',
            kwargs={
                'task_name': self.name,
                'task_id': task_id,
                'args': args,
                'kwargs': kwargs,
                'exception': str(exc),
                'traceback': str(einfo)
            },
            queue='dlq'
        )


@celery_app.task(base=SMSTask, name="workers.tasks.sms_tasks.process_sms")
def process_sms(sms_id: str, phone_number: str, message: str):
    async def _process():
        success, message_id, error = await OperatorClient.send_sms(phone_number, message)

        status = SMSStatus.SENT if success else SMSStatus.FAILED
        sent_at = datetime.utcnow() if success else None

        redis_client = None
        engine = None

        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            result_data = {
                "sms_id": sms_id,
                "status": status,
                "sent_at": sent_at.isoformat() if sent_at else None
            }
            await redis_client.lpush("sms_results", json.dumps(result_data))

            if success:
                logger.info(f"SMS {sms_id} sent successfully, queued for batch update")
            else:
                logger.error(f"SMS {sms_id} failed: {error}, queued for batch update")

        except Exception as redis_error:
            logger.warning(f"Redis failed, falling back to direct DB update: {redis_error}")

            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with async_session() as session:
                repo = SMSRepository(session)
                await repo.update_status(
                    sms_id=UUID(sms_id),
                    status=status,
                    sent_at=sent_at
                )

            if success:
                logger.info(f"SMS {sms_id} sent successfully, updated DB directly")
            else:
                logger.error(f"SMS {sms_id} failed: {error}, updated DB directly")

        finally:
            if redis_client:
                await redis_client.aclose()
            if engine:
                await engine.dispose()

    asyncio.run(_process())


@celery_app.task(name="workers.tasks.sms_tasks.messages_satus_batch_update")
def messages_satus_batch_update():
    async def _process():
        redis_client = None
        engine = None

        try:
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

            results = []
            for _ in range(10000):
                result_json = await redis_client.rpop("sms_results")
                if not result_json:
                    break
                results.append(json.loads(result_json))

            if not results:
                logger.debug("No SMS results to batch update")
                return

            sent_ids = []
            failed_ids = []
            sent_at = None

            for result in results:
                sms_id = UUID(result["sms_id"])
                status = result["status"]

                if status == SMSStatus.SENT:
                    sent_ids.append(sms_id)
                    if not sent_at and result["sent_at"]:
                        sent_at = datetime.fromisoformat(result["sent_at"])
                elif status == SMSStatus.FAILED:
                    failed_ids.append(sms_id)

            engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with async_session() as session:
                repo = SMSRepository(session)

                sent_count, failed_count = await repo.batch_update_status(
                    sent_ids=sent_ids,
                    failed_ids=failed_ids,
                    sent_at=sent_at
                )

                logger.info(f"Batch updated {sent_count} SMS to SENT, {failed_count} to FAILED in single transaction")

        except Exception as e:
            logger.error(f"Error in messages_satus_batch_update: {e}")
            raise

        finally:
            if redis_client:
                await redis_client.aclose()
            if engine:
                await engine.dispose()

    asyncio.run(_process())
