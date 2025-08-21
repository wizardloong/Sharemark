from pathlib import Path
from fastapi import FastAPI
from contextlib import asynccontextmanager
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis = get_redis()
    await redis.ping()
    print("✅ Redis connected")
    await rabbit.connect()
    task = asyncio.create_task(start_redis_subscriber())
    yield
    # Shutdown
    await redis.close()
    print("🔴 Redis disconnected")
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Подключаем маршруты
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)