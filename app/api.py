from fastapi import APIRouter
from uuid import uuid4

router = APIRouter()

SHARED_FOLDERS = {}

@router.post("/share")
def create_share(folder_id: str, write: bool = False):
    share_id = str(uuid4())
    token = str(uuid4())

    SHARED_FOLDERS[share_id] = {
        "folder_id": folder_id,
        "write": write,
        "token": token,
        "clients": []
    }

    return {
        "share_id": share_id,
        "token": token,
        "write": write
    }


@router.get("/hello")
async def share_folder():
    return {"message": "Folder shared"}