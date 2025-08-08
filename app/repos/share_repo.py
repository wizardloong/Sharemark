import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from storage.mysql import get_db  # Получение сессии БД
from models.share import Share

BASE_URL = "https://yourdomain.com/share/"

def generateShareUrl(sharemark_uuid: str, master_uuid: str) -> str:
    try:
        db = next(get_db())
        # Попробуем найти запись по uuid
        share = db.query(Share).filter_by(uuid=sharemark_uuid).one()
    except NoResultFound:
        # Если не нашли — создаём новую
        share_url = f"{BASE_URL}{sharemark_uuid}"

        share = Share(
            uuid=sharemark_uuid,
            master_uuid=master_uuid,
            share_url=share_url,
        )
        db.add(share)
        db.commit()
        db.refresh(share)

    return share.share_url
