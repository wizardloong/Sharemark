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
MAX_QUEUE_LENGTH = 1000
DEFAULT_DELAY = 3000
MAX_RETRIES = 5  # Максимальное количество попыток

class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.main_queue = None
        self.delay_queue = None

    async def connect(self):
        self.connection = await connect_robust(
            host=RABBIT_HOST,
            port=RABBIT_PORT,
            login=RABBIT_USER,
            password=RABBIT_PASSWORD
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

        # Объявляем очередь задержки
        self.delay_queue = await self.channel.declare_queue(
            DELAY_QUEUE_NAME,
            durable=True,
            arguments={
                "x-message-ttl": DEFAULT_DELAY,
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": QUEUE_NAME,
                "x-max-length": MAX_QUEUE_LENGTH
            }
        )

        # Объявляем основную очередь
        self.main_queue = await self.channel.declare_queue(
            QUEUE_NAME,
            durable=True,
            arguments={
                "x-max-length": MAX_QUEUE_LENGTH
            }
        )

    async def publish(self, message, headers=None, delay: int = 0):
        if headers is None:
            headers = {}

        if not self.channel:
            await self.connect()

        if isinstance(message, dict):
            message = json.dumps(message)
        elif not isinstance(message, (str, bytes)):
            raise TypeError(f"Message must be str, dict or bytes, got {type(message).__name__}")

        if isinstance(message, str):
            message = message.encode()

        # Копируем заголовки
        message_headers = headers.copy()
        
        # Устанавливаем expiration для задержки
        expiration = delay if delay else None

        message_obj = Message(
            body=message,
            headers=message_headers,
            expiration=expiration
        )

        target_queue = DELAY_QUEUE_NAME if delay else QUEUE_NAME
        await self.channel.default_exchange.publish(
            message_obj,
            routing_key=target_queue
        )

    async def consume(self, callback):
        if not self.channel:
            await self.connect()

        async with self.main_queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    # Обрабатываем сообщение
                    await callback(message)
                    # Подтверждаем успешную обработку
                    await message.ack()
                    
                except Exception as e:
                    # Получаем текущее количество попыток
                    retry_count = message.headers.get('x-retry-count', 0)
                    
                    if retry_count >= MAX_RETRIES:
                        print(f"❌ Message failed after {MAX_RETRIES} attempts: {e}")
                        # Удаляем сообщение после исчерпания попыток
                        await message.ack()
                    else:
                        print(f"⚠ Retry {retry_count + 1} due to error: {e}")
                        
                        # Создаем новые заголовки с увеличенным счетчиком
                        new_headers = message.headers.copy()
                        new_headers['x-retry-count'] = retry_count + 1
                        
                        # Публикуем сообщение с задержкой
                        await self.publish(
                            message.body,
                            headers=new_headers,
                            delay=DEFAULT_DELAY
                        )
                        
                        # Подтверждаем исходное сообщение
                        await message.ack()

    async def close(self):
        if self.connection:
            await self.connection.close()

# Глобальный объект
rabbit = RabbitMQ()