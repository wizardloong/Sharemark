import uuid
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from data_storage import active_connections
from repos.share_repo import get_shared_folder
from storage.redis import redis_client

router = APIRouter()

@router.websocket("/ws/sync")
async def websocket_endpoint(
    websocket: WebSocket,
    sharemark_uuid: str = Query(...)
):
    await websocket.accept()
    
    # Генерируем уникальный ID для соединения
    connection_id = str(uuid.uuid4())
    
    # Добавляем в локальный словарь для быстрого доступа
    if sharemark_uuid not in active_connections:
        active_connections[sharemark_uuid] = []
    active_connections[sharemark_uuid].append(websocket)
    
    # Регистрируем в Redis для межпроцессного оповещения
    await redis_client.sadd(f"ws:connections:{sharemark_uuid}", connection_id)
    
    # Добавляем маппинг ID -> UUID для быстрого поиска
    await redis_client.set(f"ws:mapping:{connection_id}", sharemark_uuid)
    
    try:
        ping_task = asyncio.create_task(periodic_ping(websocket))
        # Обработка сообщений от клиента...
        while True:
            message = await websocket.receive_json()
            # Проверяем, есть ли указан конкретный share_id в сообщении
            target_share_id = message.get("share_id")

            for folder_data in await get_shared_folder(sharemark_uuid):
                # Если указан конкретный share_id, обрабатываем только его
                if target_share_id and folder_data.share_id != target_share_id:
                    continue

                print(f"[WS] Подключен клиент {sharemark_uuid} "
                      + "к share_id={folder_data.share_id}")

                # Если пришло обновление закладок
                if message.get("type") == "bookmark_update":
                    folder = folder_data
                    if folder and folder.can_write:
                        folder.bookmarks = message.get("data", [])

                # Рассылаем всем подключениям владельца, кроме отправителя
                for conn in active_connections[sharemark_uuid]:
                    if conn != websocket:
                        await conn.send_json(message)
    except WebSocketDisconnect:
        # Удаляем из локального хранилища
        active_connections[sharemark_uuid].remove(websocket)
        
        # Удаляем из Redis
        await redis_client.srem(f"ws:connections:{sharemark_uuid}", connection_id)
        await redis_client.delete(f"ws:mapping:{connection_id}")


async def start_redis_subscriber():
    """Запускает прослушивание Redis-каналов для WebSocket уведомлений"""
    pubsub = redis_client.pubsub()
    
    # Подписываемся на все каналы ws:notifications:*
    await pubsub.psubscribe("ws:notifications:*")
    
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            try:
                # Извлекаем sharemark_uuid из названия канала
                channel = message["channel"].decode("utf-8")
                sharemark_uuid = channel.split(":")[-1]
                
                # Парсим данные сообщения
                notification = json.loads(message["data"])
                
                # Рассылаем всем активным соединениям
                if sharemark_uuid in active_connections:
                    for websocket in active_connections[sharemark_uuid]:
                        try:
                            await websocket.send_json(notification)
                        except Exception as e:
                            print(f"Error sending to websocket: {e}")
                            
            except Exception as e:
                print(f"Error processing Redis notification: {e}")


async def periodic_ping(websocket):
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.ping()
    except Exception:
        # Соединение потеряно
        pass
