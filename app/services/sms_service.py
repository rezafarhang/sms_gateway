from uuid import UUID
from workers.celery_app import celery_app
from core.consts import SMSType, QueueName


class SMSService:
    @staticmethod
    def publish_to_queue(
        sms_id: UUID,
        account_id: UUID,
        phone_number: str,
        message: str,
        sms_type: int
    ) -> None:
        queue = QueueName.EXPRESS if sms_type == SMSType.EXPRESS else QueueName.REGULAR

        celery_app.send_task(
            "workers.tasks.sms_tasks.process_sms",
            kwargs={
                "sms_id": str(sms_id),
                "account_id": str(account_id),
                "phone_number": phone_number,
                "message": message,
                "sms_type": sms_type
            },
            queue=queue
        )
