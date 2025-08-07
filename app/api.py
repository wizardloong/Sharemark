from fastapi import APIRouter, HTTPException
from uuid import uuid4
import json

from app.websocket import active_connections

router = APIRouter()
shared_folders = {}


class SharedFolder:
    def __init__(self, folder_id, name, bookmarks, can_write):
        self.share_id = str(uuid4())
        self.token = str(uuid4())
        self.folder_id = folder_id
        self.name = name
        self.bookmarks = bookmarks
        self.can_write = can_write
        self.owner_token = self.token


@router.post("/share")
async def share_folder(data: ShareRequest):  # Используем Pydantic модель
    if not data.bookmarks:
        raise HTTPException(400, "Bookmarks cannot be empty")

    folder = SharedFolder(
        folder_id=data.folder_id,
        name=data.name,
        bookmarks=data.bookmarks,
        can_write=data.can_write
    )

    shared_folders[folder.share_id] = folder
    return {
        "share_id": folder.share_id,
        "token": folder.token,
        "readOnly": not folder.can_write
    }


@router.get("/folder/{share_id}")
async def get_shared_folder(share_id: str):
    folder = shared_folders.get(share_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    return {
        "name": folder.name,
        "bookmarks": folder.bookmarks,
        "token": folder.token,
        "readOnly": not folder.can_write
    }


@router.post("/update/{token}")
async def update_folder(token: str, update_data: dict):
    # Find folder by token
    folder = next((f for f in shared_folders.values() if f.token == token), None)
    if not folder:
        raise HTTPException(status_code=404, detail="Invalid token")

    if not folder.can_write:
        raise HTTPException(status_code=403, detail="Read-only folder")

    # Apply updates
    folder.name = update_data.get("name", folder.name)
    folder.bookmarks = update_data.get("bookmarks", folder.bookmarks)

    # Notify all clients
    for connection in active_connections.get(token, []):
        await connection.send_json({
            "type": "bookmark_update",
            "data": {
                "folder_id": folder.folder_id,
                "name": folder.name,
                "bookmarks": folder.bookmarks
            }
        })

    return {"status": "success"}