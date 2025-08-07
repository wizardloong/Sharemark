from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

from app.api import shared_folders

router = APIRouter()
active_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    # Проверка валидности токена
    if token not in shared_folders:
        await websocket.close(code=1008)
        return

    # Регистрация соединения
    if token not in active_connections:
        active_connections[token] = []
    active_connections[token].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # Проверка прав на запись
            folder = next(f for f in shared_folders.values() if f.token == token)
            if not folder.can_write:
                await websocket.send_json({"error": "Read-only access"})
                continue

            # Рассылка обновлений
            for conn in active_connections[token]:
                if conn != websocket:
                    await conn.send_json(data)

    except WebSocketDisconnect:
        active_connections[token].remove(websocket)
