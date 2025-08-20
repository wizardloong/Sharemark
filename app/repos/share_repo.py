import json
import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from storage.mysql import get_db
from models.share import Share
from schemas import SharedFolder
from storage.redis import get_redis
from typing import Dict, List, Optional
from fastapi import WebSocket
from pydantic import TypeAdapter

BASE_URL = "getsharemark.com:8000/get_sharemark_share?share_id="

def generateShareUrl(share_id: str, master_uuid: str) -> str:
    db = next(get_db())
    try:
        share = db.query(Share).filter_by(uuid=share_id).one()
    except NoResultFound:
        share_url = f"{BASE_URL}{share_id}"
        share = Share(
            uuid=share_id,
            master_uuid=master_uuid,
            share_url=share_url,
        )
        db.add(share)
        db.commit()
        db.refresh(share)
    return share.share_url


# Ключи в Redis будем формировать как "shared_folder:{share_id}"
def redis_key(share_id: str) -> str:
    return f"shared_folder:{share_id}"

async def save_shared_folder(share_id: str, folder_data: dict):
    redis = get_redis()
    assert redis is not None, "Redis client not initialized"
    adapter = TypeAdapter(dict[str, SharedFolder])
    data_json = adapter.dump_json(folder_data).decode()
    await redis.set(redis_key(share_id), data_json)

async def get_shared_folder(share_id: str) -> Optional[dict]:
    redis = get_redis()
    assert redis is not None, "Redis client not initialized"
    data_json = await redis.get(redis_key(share_id))
    if not data_json:
        return {}
    return json.loads(data_json)

async def delete_shared_folder(share_id: str):
    redis = get_redis()
    assert redis is not None, "Redis client not initialized"
    await redis.delete(redis_key(share_id))