from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from data_storage import active_connections, shared_folders

router = APIRouter()

@router.websocket("/ws/sync")
async def websocket_endpoint(websocket: WebSocket, share_id: str):
    await websocket.accept()

    # Регистрируем соединение
    if share_id not in active_connections:
        active_connections[share_id] = []
    active_connections[share_id].append(websocket)

    print(f"[WS] Подключен клиент к share_id={share_id}")

    try:
        while True:
            message = await websocket.receive_json()

            # Если пришло обновление закладок
            if message.get("type") == "bookmark_update":
                folder = shared_folders.get(share_id)
                if folder and folder.can_write:
                    folder.bookmarks = message.get("data", [])

            # Рассылаем всем кроме отправителя
            for conn in active_connections[share_id]:
                if conn != websocket:
                    await conn.send_json(message)

    except WebSocketDisconnect as e:
        active_connections[share_id].remove(websocket)
        print(f"[WS] Клиент отключен от share_id={share_id}")
