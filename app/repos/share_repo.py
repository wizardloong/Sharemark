import uuid as uuid_lib
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from storage.mysql import get_db
from models.share import Share

BASE_URL = "http://localhost:8000/share/"

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
