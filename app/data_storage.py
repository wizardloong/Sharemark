# storage.py
from typing import Dict, List
from fastapi import WebSocket

# share_id → список соединений
active_connections: Dict[str, List[WebSocket]] = {}
