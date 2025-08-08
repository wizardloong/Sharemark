from fastapi import APIRouter, HTTPException
from uuid import uuid4
import json

from repos.share_repo import generateShareUrl
from schemas import ShareRequest
from websocket import active_connections

router = APIRouter()


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

    master_uuid = ShareRequest.sharemark_uuid

    return {
        "share_id": master_uuid,
        "share_url": generateShareUrl(ShareRequest.sharemark_uuid, ''),
    }