import os
import redis.asyncio as redis  # асинхронный клиент

# Создаём глобальный клиент Redis (можно через lazy init)
redis_client: redis.Redis = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD')
    # decode_responses=True  # если ты хочешь строки, а не байты
)

def get_redis() -> redis.Redis:
    return redis_client