import aio_pika
from typing import Optional

from config.settings import settings

_rabbitmq_connection: Optional[aio_pika.abc.AbstractRobustConnection] = None


async def get_rabbitmq_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _rabbitmq_connection
    if _rabbitmq_connection is None or _rabbitmq_connection.is_closed:
        _rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    return _rabbitmq_connection


async def close_rabbitmq() -> None:
    global _rabbitmq_connection
    if _rabbitmq_connection and not _rabbitmq_connection.is_closed:
        await _rabbitmq_connection.close()
        _rabbitmq_connection = None


async def setup_rabbitmq_queues() -> None:
    pass
