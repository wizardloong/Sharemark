# storage.py
from typing import Dict, List
from fastapi import WebSocket

active_connections: Dict[str, List[WebSocket]] = {}
shared_folders: dict = {}  # Переносим сюда для сохранности при рефакторинге
