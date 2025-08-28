import uuid
import json
import asyncio
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from data_storage import active_connections
from repos.share_repo import get_shared_folder
from storage.redis import redis_client

IDLE_TIMEOUT = 90  # секунды

router = APIRouter()

@router.websocket("/ws/sync")
async def websocket_endpoint(websocket: WebSocket, sharemark_uuid: str = Query(...)):
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    # добавляем в локальные подключения
    if sharemark_uuid not in active_connections:
        active_connections[sharemark_uuid] = []
    active_connections[sharemark_uuid].append({"ws": websocket, "last_pong": time.time()})
    
    # регистрируем в Redis
    await redis_client.sadd(f"ws:connections:{sharemark_uuid}", connection_id)
    await redis_client.set(f"ws:mapping:{connection_id}", sharemark_uuid)
    
    try:
        ping_task = asyncio.create_task(periodic_ping(websocket, sharemark_uuid, connection_id))
        
        while True:
            message = await websocket.receive_json()
            
            # если пришёл pong от клиента
            if message.get("type") == "pong":
                for conn in active_connections[sharemark_uuid]:
                    if conn["ws"] == websocket:
                        conn["last_pong"] = time.time()
                        break
                continue
            
            # обработка bookmark_update или других сообщений
            target_share_id = message.get("share_id")
            for folder_data in await get_shared_folder(sharemark_uuid):
                if target_share_id and folder_data.share_id != target_share_id:
                    continue
                if message.get("type") == "bookmark_update" and folder_data.can_write:
                    folder_data.bookmarks = message.get("data", [])
                # рассылка другим подключенным клиентам
                for conn in active_connections[sharemark_uuid]:
                    if conn["ws"] != websocket:
                        await conn["ws"].send_json(message)
    
    except WebSocketDisconnect:
        await cleanup_connection(websocket, sharemark_uuid, connection_id)


async def periodic_ping(websocket, sharemark_uuid, connection_id):
    try:
        while True:
            await asyncio.sleep(30)
            # проверяем last_pong
            now = time.time()
            for conn in list(active_connections.get(sharemark_uuid, [])):
                if now - conn["last_pong"] > IDLE_TIMEOUT:
                    print(f"Закрываю idle соединение {connection_id}")
                    await cleanup_connection(conn["ws"], sharemark_uuid, connection_id)
                    return

            # отправляем ping
            await websocket.send_json({"type": "ping"})
    except Exception:
        # соединение потеряно
        await cleanup_connection(websocket, sharemark_uuid, connection_id)


async def cleanup_connection(websocket, sharemark_uuid, connection_id):
    # удаляем из локальных подключений
    conns = active_connections.get(sharemark_uuid, [])
    active_connections[sharemark_uuid] = [c for c in conns if c["ws"] != websocket]
    
    # удаляем из Redis
    await redis_client.srem(f"ws:connections:{sharemark_uuid}", connection_id)
    await redis_client.delete(f"ws:mapping:{connection_id}")
    
    try:
        await websocket.close()
    except:
        pass


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
                            await websocket["ws"].send_json(notification)
                        except Exception as e:
                            print(f"Error sending to websocket: {e}")
                            
            except Exception as e:
                print(f"Error processing Redis notification: {e}")

