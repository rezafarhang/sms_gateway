from fastapi import FastAPI
from contextlib import asynccontextmanager

from config.settings import settings
from config.rabbitmq import setup_rabbitmq_queues, close_rabbitmq
from config.redis import close_redis
from app.routers import accounts_router, sms_router


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

app.include_router(accounts_router, prefix=settings.API_V1_PREFIX)
app.include_router(sms_router, prefix=settings.API_V1_PREFIX)


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
