from fastapi import APIRouter, HTTPException
from uuid import uuid4
from repos.share_repo import generateShareUrl
from schemas import ShareRequest
from data_storage import shared_folders

router = APIRouter()

class SharedFolder:
    def __init__(self, folder_id, name, bookmarks, can_write, owner_uuid):
        self.share_id = str(uuid4())
        self.folder_id = folder_id
        self.name = name
        self.bookmarks = bookmarks
        self.can_write = can_write
        self.owner_uuid = owner_uuid

@router.post("/share")
async def share_folder(data: ShareRequest):
    if not data.bookmarks:
        raise HTTPException(400, "Bookmarks cannot be empty")

    folder = SharedFolder(
        folder_id=data.folder_id,
        name=data.name,
        bookmarks=data.bookmarks,
        can_write=data.can_write,
        owner_uuid=data.sharemark_uuid
    )

    # Сохраняем в памяти
    shared_folders[folder.share_id] = folder

    # Создаём или получаем ссылку
    share_url = generateShareUrl(folder.share_id, data.sharemark_uuid)

    return {
        "share_id": folder.share_id,
        "share_url": share_url,
    }
