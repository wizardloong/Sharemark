from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Загружаем .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / 'env' / '.env')

from api import router as api_router
from websocket import router as ws_router
from storage.redis import get_redis

app = FastAPI()

# Подключаем маршруты
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.on_event("startup")
async def startup_event():
    redis = get_redis()
    await redis.ping()
    print("✅ Redis connected")

@app.on_event("shutdown")
async def shutdown_event():
    redis = get_redis()
    await redis.close()
    print("🔴 Redis disconnected")