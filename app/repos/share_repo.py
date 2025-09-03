import json
import uuid as uuid_lib
from sqlalchemy.exc import NoResultFound
from models.share import Share
from schemas import SharedFolder

import msgpack
from typing import Dict, Optional
from pydantic import TypeAdapter
from storage.redis import get_redis
from schemas import SharedFolder

BASE_URL = "getsharemark.com/get_sharemark_share?share_id="

def generateShareUrl(db, share_id: str, master_uuid: str) -> str:
    try:
        share = db.query(Share).filter_by(share_id=share_id).one()
    except NoResultFound:
        share_url = f"{BASE_URL}{share_id}"
        share = Share(
            share_id=share_id,
            master_uuid=master_uuid,
            share_url=share_url,
        )
        db.add(share)
        db.commit()
        db.refresh(share)
    return share.share_url


def redis_key(share_id: str) -> str:
    return f"shared_folder:{share_id}"

TTL_SECONDS = 15 * 60  # 15 минут
async def save_shared_folder(share_id: str, folder_data: dict):
    """
    Сохраняет данные папки в Redis с TTL и сериализацией через MsgPack.
    folder_data: dict[str, SharedFolder]
    """
    redis = get_redis()
    assert redis is not None, "Redis client not initialized"
    
    adapter = TypeAdapter(dict[str, SharedFolder])
    # Сначала сериализуем Pydantic модели в словарь, затем в MsgPack
    dict_data = {k: v.model_dump() for k, v in folder_data.items()}
    packed_data = msgpack.packb(dict_data, use_bin_type=True)
    await redis.set(redis_key(share_id), packed_data, ex=TTL_SECONDS)

async def get_shared_folder(share_id: str) -> Optional[dict]:
    """
    Получает данные папки из Redis и десериализует.
    Возвращает dict[str, SharedFolder] или пустой словарь.
    """
    redis = get_redis()
    assert redis is not None, "Redis client not initialized"
    
    packed_data = await redis.get(redis_key(share_id))
    if not packed_data:
        return {}
    
    dict_data = msgpack.unpackb(packed_data, raw=False)

    return dict_data
    
    # Можно сразу вернуть как Pydantic модели:
    # return {k: SharedFolder.model_validate(v) for k, v in dict_data.items()}

async def delete_shared_folder(share_id: str):
    """
    Удаляет данные папки из Redis.
    """
    redis = get_redis()
    assert redis is not None, "Redis client not initialized"
    await redis.delete(redis_key(share_id))
