import os
import asyncio
import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_proxiedheadersmiddleware import ProxiedHeadersMiddleware

# Загружаем .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / "env" / ".env")

from api import router as api_router
from websocket import router as ws_router, start_redis_subscriber
from portal import router as portal_router
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

    # Инициализация fastapi-limiter
    await FastAPILimiter.init(redis)

    await rabbit.connect()
    task = asyncio.create_task(start_redis_subscriber())
    
    yield

    # Shutdown
    await redis.close()
    print("🔴 Redis disconnected")
    task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(GZipMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[os.getenv("DOMAIN_NAME"), "localhost"])
app.add_middleware(ProxiedHeadersMiddleware)

app.mount("/static", StaticFiles(directory="public/static"), name="static")

# Подключаем маршруты
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)
app.include_router(portal_router)
