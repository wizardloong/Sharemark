from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi_limiter.depends import RateLimiter
from fastapi.responses import JSONResponse
from data_storage import active_connections
from schemas import ShareRequest, SharedFolder
from repos.share_repo import generateShareUrl, get_shared_folder, save_shared_folder
from infrastructure.rabbitmq import rabbit

router = APIRouter()

async def get_sharemark_uuid(request: Request) -> str:
    data = await request.json()
    return data.get("sharemark_uuid")

# 🔹 POST /api/share: 5 запросов в минуту на sharemark_uuid
@router.post("/share")
async def share_folder(
    data: ShareRequest, 
    request: Request,
    _=Depends(RateLimiter(times=5, seconds=60, identifier=get_sharemark_uuid))
):
    if not data.bookmarks:
        raise HTTPException(400, "Bookmarks cannot be empty")

    folder = SharedFolder(
        folder_id=data.folder_id,
        name=data.name,
        bookmarks=data.bookmarks,
        can_write=data.can_write,
        owner_uuid=data.sharemark_uuid,
    )

    folder_key = folder.owner_uuid + "_" + folder.folder_id
    shared_folders = await get_shared_folder(folder_key)
    if folder_key not in shared_folders:
        shared_folders[folder_key] = []

    shared_folders[folder_key] = folder
    await save_shared_folder(folder_key, shared_folders)

    share_url = generateShareUrl(folder_key, data.sharemark_uuid)

    return {"share_id": folder_key, "share_url": share_url}


# 🔹 GET /api/share: 10 запросов в секунду на IP, burst=20
@router.get("/share")
async def get_share(
    share_id: str = Query(..., description="ID расшариваемой папки"),
    sharemark_uuid: str = Query(..., description="UUID владельца, хранящийся в локальном хранилище"),
    _=Depends(RateLimiter(times=10, seconds=1))  # лимит на IP
):
    payload = {"sharemark_uuid": sharemark_uuid, "share_id": share_id}

    # Отправляем в очередь
    await rabbit.publish(payload)
    return {"status": "queued"}
