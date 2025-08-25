import os
import asyncio
from aio_pika import connect_robust, Message, IncomingMessage
import json

RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASSWORD = os.getenv("RABBIT_PASSWORD", "guest")

QUEUE_NAME = "shared_folders_queue"
DELAY_QUEUE_NAME = "shared_folders_delay_queue"
MAX_QUEUE_LENGTH = 1000  # пример ограничения очереди (high-watermark логика)


class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await connect_robust(
            host=RABBIT_HOST,
            port=RABBIT_PORT,
            login=RABBIT_USER,
            password=RABBIT_PASSWORD
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        # Основная очередь с ограничением длины (high-watermark логика)
        await self.channel.declare_queue(
            QUEUE_NAME,
            durable=True,
            arguments={"x-max-length": MAX_QUEUE_LENGTH}
        )

        # Очередь задержки для retry
        await self.channel.declare_queue(
            DELAY_QUEUE_NAME,
            durable=True,
            arguments={
                "x-message-ttl": 1000,  # первая задержка 1 секунда
                "x-dead-letter-exchange": "",  # после TTL вернется в основную очередь
                "x-dead-letter-routing-key": QUEUE_NAME
            }
        )

    async def publish(self, message, delay: int = 0):
        if not self.channel:
            await self.connect()

        if isinstance(message, dict):
            message = json.dumps(message)
        elif not isinstance(message, str) and not isinstance(message, bytes):
            raise TypeError(f"Message must be str, dict or bytes, got {type(message).__name__}")

        if isinstance(message, str):
            message = message.encode()

        target_queue = DELAY_QUEUE_NAME if delay else QUEUE_NAME
        # Если задан delay > 0, временно используем delay очередь и TTL
        if delay:
            await self.channel.declare_queue(
                DELAY_QUEUE_NAME,
                durable=True,
                arguments={
                    "x-message-ttl": delay,
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": QUEUE_NAME,
                }
            )

        await self.channel.default_exchange.publish(
            Message(body=message),
            routing_key=target_queue
        )

    async def consume(self, callback, retries: int = 3):
        if not self.channel:
            await self.connect()

        queue = await self.channel.declare_queue(QUEUE_NAME, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(requeue=False):
                    attempt = 0
                    backoffs = [1, 5, 20]  # секунды
                    while attempt < retries:
                        try:
                            await callback(message)
                            break
                        except Exception as e:
                            attempt += 1
                            if attempt >= retries:
                                print(f"❌ Message failed after {retries} attempts: {e}")
                                # можно отправить в DLQ или логировать
                                break
                            else:
                                delay = backoffs[attempt - 1]
                                print(f"⚠ Retry {attempt} after {delay}s due to error: {e}")
                                await asyncio.sleep(delay)
                                # повторная публикация в очередь с delay
                                await self.publish(message.body, delay=delay * 1000)


# Глобальный объект
rabbit = RabbitMQ()
