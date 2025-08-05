from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter()
active_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()

    if token not in active_connections:
        active_connections[token] = []
    active_connections[token].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Relay message to all clients with same token
            for connection in active_connections[token]:
                if connection != websocket:
                    await connection.send_text(data)
    except WebSocketDisconnect:
        active_connections[token].remove(websocket)
        if not active_connections[token]:
            del active_connections[token]