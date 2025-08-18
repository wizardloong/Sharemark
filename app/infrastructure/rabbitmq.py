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
        await self.channel.declare_queue(QUEUE_NAME, durable=True)

        # Очередь для задержки
        await self.channel.declare_queue(
            DELAY_QUEUE_NAME,
            durable=True,
            arguments={
                "x-message-ttl": 1000,  # Задержка 1 секунд
                "x-dead-letter-exchange": "",  # После TTL вернется в основную очередь
                "x-dead-letter-routing-key": QUEUE_NAME
            }
        )

    async def publish(self, message):
        if not self.channel:
            await self.connect()

        # Автоматическая конвертация словарей в JSON-строку
        if isinstance(message, dict):
            message = json.dumps(message)
        elif not isinstance(message, str):
            raise TypeError(f"Message must be str or dict, got {type(message).__name__}")

        await self.channel.default_exchange.publish(
            Message(body=message.encode()),
            routing_key=QUEUE_NAME
        )

    async def consume(self, callback):
        if not self.channel:
            await self.connect()
        queue = await self.channel.declare_queue(QUEUE_NAME, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await callback(message)
                    
    # Добавьте этот метод в класс RabbitMQ
    async def publish_delayed(self, message):
        """Публикует сообщение в очередь с задержкой"""
        if not self.channel:
            await self.connect()

        # Автоматическая конвертация словарей в JSON-строку
        if isinstance(message, dict):
            message = json.dumps(message)
        elif not isinstance(message, str) and not isinstance(message, bytes):
            raise TypeError(f"Message must be str, dict or bytes, got {type(message).__name__}")

        # Если это строка, конвертируем в байты
        if isinstance(message, str):
            message = message.encode()

        await self.channel.default_exchange.publish(
            Message(body=message),
            routing_key=DELAY_QUEUE_NAME
        )


# Глобальный объект для удобства
rabbit = RabbitMQ()
