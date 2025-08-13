from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from data_storage import active_connections
from schemas import ShareRequest
from uuid import uuid4
from repos.share_repo import generateShareUrl, get_shared_folder, save_shared_folder
from schemas import SharedFolder

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

    shared_folders = await get_shared_folder(folder.owner_uuid)

    if folder.owner_uuid not in shared_folders:
            shared_folders[folder.owner_uuid] = []

    shared_folders[folder.owner_uuid].append(folder)
    await save_shared_folder(folder.owner_uuid, shared_folders)
    share_url = generateShareUrl(folder.folder_id, data.sharemark_uuid)

    return {
        "share_id": folder.folder_id,
        "share_url": share_url,
    }


@router.get("/share")
async def get_share(
    share_id: str = Query(..., description="ID расшариваемой папки"),
    sharemark_uuid: str = Query(..., description="UUID владельца, хранящийся в локальном хранилище")
):
    # Находим активные соединения пользователя
    connections = active_connections.get(sharemark_uuid)
    if not connections:
        raise HTTPException(404, "Активное соединение пользователя не найдено")

    # Находим данные папки
    folder = await get_shared_folder(share_id)

    # тут на самом деде список папок и надо найти какой поделиться
    if not folder:
        raise HTTPException(404, "Данные для указанного share_id не найдены")

    # Отправляем данные по всем соединениям пользователя
    for ws in connections:
        await ws.send_json({
            "type": "shared_folder_data",
            "share_id": share_id,
            "folder_id": folder.folder_id,
            "name": folder.name,
            "bookmarks": folder.bookmarks,
            "can_write": folder.can_write
        })

    return {"status": "ok", "message": "Данные отправлены по активному WebSocket-соединению"}
