from celery import Celery
from config.settings import settings

celery_app = Celery(
    "sms_gateway",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.config_from_object("config.celery")

celery_app.autodiscover_tasks(['workers.tasks.sms_tasks'])
