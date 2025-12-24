import logging
from datetime import datetime
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name='workers.tasks.dlq_tasks.store_failed_task')
def store_failed_task(task_name: str, task_id: str, args: tuple, kwargs: dict, exception: str, traceback: str):
    logger.critical(
        f"DEAD LETTER: Task {task_name} [{task_id}] failed permanently\n"
        f"Args: {args}\n"
        f"Kwargs: {kwargs}\n"
        f"Exception: {exception}\n"
        f"Traceback: {traceback}\n"
        f"Timestamp: {datetime.utcnow().isoformat()}"
    )

    # TODO: In production, store in database
    return {"status": "logged", "task_id": task_id}
