from fastapi import FastAPI
from contextlib import asynccontextmanager

from config.settings import settings
from config.rabbitmq import setup_rabbitmq_queues, close_rabbitmq
from config.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_rabbitmq_queues()
    yield
    await close_rabbitmq()
    await close_redis()


app = FastAPI(
    title="SMS Gateway",
    description="High-performance SMS Gateway with Express and Regular queues",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "sms_gateway"
    }


@app.get("/")
async def root():
    return {
        "message": "SMS Gateway API",
        "docs": "/docs",
        "health": "/health"
    }
