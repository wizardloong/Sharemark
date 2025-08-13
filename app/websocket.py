from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from data_storage import active_connections
from repos.share_repo import get_shared_folder

router = APIRouter()

@router.websocket("/ws/sync")
async def websocket_endpoint(
    websocket: WebSocket,
    sharemark_uuid: str = Query(...)
):
    await websocket.accept()

    # Регистрируем соединение по UUID пользователя
    if sharemark_uuid not in active_connections:
        active_connections[sharemark_uuid] = []

    active_connections[sharemark_uuid].append(websocket)

    try:
        while True:
            message = await websocket.receive_json()


            for folder_data in await get_shared_folder(sharemark_uuid):

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
        active_connections[sharemark_uuid].remove(websocket)
        print(f"[WS] Клиент {sharemark_uuid} отключен")
