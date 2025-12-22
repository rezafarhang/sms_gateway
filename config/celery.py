from kombu import Queue
from config.settings import settings

broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

task_routes = {
    'workers.tasks.sms_tasks.send_sms_express': {'queue': 'express'},
    'workers.tasks.sms_tasks.send_sms_regular': {'queue': 'regular'},
}

task_queues = (
    Queue('express'),
    Queue('regular'),
)

task_default_queue = 'regular'

worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

task_acks_late = True
task_reject_on_worker_lost = True

broker_connection_retry_on_startup = True
