from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from data_storage import active_connections
from schemas import ShareRequest
from uuid import uuid4
from repos.share_repo import generateShareUrl, get_shared_folder, save_shared_folder
from schemas import SharedFolder
from infrastructure.rabbitmq import rabbit

router = APIRouter()

@router.post("/share")
async def share_folder(data: ShareRequest):
    if not data.bookmarks:
        raise HTTPException(400, "Bookmarks cannot be empty")

    folder = SharedFolder(
        folder_id=data.folder_id,
        name=data.name,
        bookmarks=data.bookmarks,
        can_write=data.can_write,
        owner_uuid=data.sharemark_uuid # uuid того кто делится
    )

    folder_key = folder.owner_uuid + "_" + folder.folder_id

    shared_folders = await get_shared_folder(folder_key)
    if folder_key not in shared_folders:
            shared_folders[folder_key] = []

    shared_folders[folder_key] = folder

    # if not any(f["folder_id"] == folder.folder_id for f in shared_folders[folder_key]):
    #     shared_folders[folder_key].append(folder)

    await save_shared_folder(folder_key, shared_folders)
    share_url = generateShareUrl(folder_key, data.sharemark_uuid)

    return {
        "share_id": folder_key,
        "share_url": share_url,
    }


# просто поместить задачу в очередь, спасибо
@router.get("/share")
async def get_share(
    share_id: str = Query(..., description="ID расшариваемой папки"),
    sharemark_uuid: str = Query(..., description="UUID владельца, хранящийся в локальном хранилище")
):
    payload = {
        "sharemark_uuid": sharemark_uuid,
        "share_id": share_id
    }

    # Отправляем в очередь
    await rabbit.publish(payload)