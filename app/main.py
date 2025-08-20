from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import asyncio
import sentry_sdk

# Загружаем .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / 'env' / '.env')

from api import router as api_router
from websocket import router as ws_router, start_redis_subscriber
from storage.redis import get_redis
from infrastructure.rabbitmq import rabbit

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
)

app = FastAPI()

# Подключаем маршруты
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.on_event("startup")
async def startup_event():
    redis = get_redis()
    await redis.ping()
    print("✅ Redis connected")
    # Подключаемся к RabbitMQ при старте приложения
    await rabbit.connect()
    asyncio.create_task(start_redis_subscriber())

@app.on_event("shutdown")
async def shutdown_event():
    redis = get_redis()
    await redis.close()
    print("🔴 Redis disconnected")