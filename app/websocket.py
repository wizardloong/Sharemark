from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()
connections: Dict[str, list[WebSocket]] = {}

@router.websocket("/ws/sync/{share_id}")
async def sync_socket(websocket: WebSocket, share_id: str):
    await websocket.accept()
    if share_id not in connections:
        connections[share_id] = []
    connections[share_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Рассылаем другим
            for ws in connections[share_id]:
                if ws != websocket:
                    await ws.send_text(data)
    except WebSocketDisconnect:
        connections[share_id].remove(websocket)
