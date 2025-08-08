from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter()
active_connections: Dict[str, List[WebSocket]] = {}
shared_folders = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, share_id: str):
    await websocket.accept()

    # Проверка валидности токена
    # if token not in shared_folders:
    #     await websocket.close(code=1008)
    #     return

    # Регистрация соединения
    if share_id not in active_connections:
        active_connections[share_id] = []
    active_connections[share_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # Проверка прав на запись
            # folder = next(f for f in shared_folders.values() if f.token == token)
            # if not folder.can_write:
            #     await websocket.send_json({"error": "Read-only access"})
            #     continue

            # Рассылка обновлений
            for conn in active_connections[share_id]:
                if conn != websocket:
                    await conn.send_json(data)

    except WebSocketDisconnect:
        active_connections[share_id].remove(websocket)
