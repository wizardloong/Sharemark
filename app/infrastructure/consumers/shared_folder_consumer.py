# consumers/shared_folder_consumer.py
import asyncio
import json
from aio_pika import connect_robust, IncomingMessage
import aio_pika

from dotenv import load_dotenv
import os
from pathlib import Path

# Загружаем .env
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / 'env' / '.env')

from data_storage import active_connections
from repos.share_repo import get_shared_folder, delete_shared_folder
from infrastructure.rabbitmq import rabbit
from storage.redis import redis_client

MAX_RETRY_ATTEMPTS = 5

async def process_message(message: IncomingMessage):
    # try:
        payload = json.loads(message.body)
        sharemark_uuid = payload.get("sharemark_uuid")
        share_id = payload.get("share_id")

        # Получаем счетчик из заголовков
        headers = message.headers or {}
        retry_count = headers.get("x-retry-count", 0)

        await send_bookmarks(sharemark_uuid, share_id)
        
        notification = {
            "type": "bookmark_update",
            "data": payload
        }
        
        await redis_client.publish(
            f"ws:notifications:{sharemark_uuid}", 
            json.dumps(notification)
        )
        
    # except Exception as e:
    #     print(f"Ошибка: {e}, переотправляем через delay_queue")
        
    #     # Увеличиваем счетчик попыток
    #     retry_count = int(retry_count) + 1
        
    #     if retry_count <= MAX_RETRY_ATTEMPTS:
    #         try:
    #             # Используем заголовки для хранения счетчика
    #             headers = {"x-retry-count": retry_count}
    #             await rabbit.publish(
    #                 message.body, 
    #                 headers=headers,
    #                 delay=1000
    #             )
    #             print(f"Сообщение успешно добавлено в очередь задержки (попытка {retry_count}/{MAX_RETRY_ATTEMPTS})")
    #         except Exception as publish_error:
    #             print(f"Ошибка при публикации в delay_queue: {publish_error}")
    #             raise
    #     else:
    #         print(f"Достигнут лимит попыток ({MAX_RETRY_ATTEMPTS}). Сообщение удаляется.")
    #         await message.ack()


async def send_bookmarks(sharemark_uuid, share_id):
    # Проверка наличия соединений в Redis
    connection_ids = await redis_client.smembers(f"ws:connections:{sharemark_uuid}")
    if not connection_ids:
        message = f"[Consumer] Активные соединения для {sharemark_uuid} не найдены в Redis"
        print(message)
        raise Exception(message)
        # Возможно, не стоит прерывать выполнение, а просто опубликовать сообщение в Redis
        # для потенциальных будущих подключений


    # Находим данные папки
    folders = await get_shared_folder(share_id)
    if share_id not in folders:
        message = f"[Consumer] Share_id {share_id} не найден в папках пользователя"
        print(message)
        raise Exception(message)

    folder = folders[share_id]

    # Вместо отправки данных по соединениям:
    notification = {
        "type": "initial_data",
        "share_id": share_id,
        "folder_id": folder["folder_id"],
        "name": folder["name"],
        "bookmarks": folder["bookmarks"],
        "can_write": folder["can_write"]
    }

    # Публикация через Redis
    await redis_client.publish(
        f"ws:notifications:{sharemark_uuid}", 
        json.dumps(notification)
    )

    await delete_shared_folder(share_id)

    print(f"[Consumer] Данные отправлены пользователю {sharemark_uuid} по share_id {share_id}")


async def main():

    await rabbit.consume(process_message)

    # connection = await connect_robust(RABBIT_URL)
    # channel = await connection.channel()
    # queue = await channel.declare_queue(QUEUE_NAME, durable=True)

    # print("[Consumer] Ждём сообщений в очереди...")
    # await queue.consume(process_message)

    # держим consumer живым
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
