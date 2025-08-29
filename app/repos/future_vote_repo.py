import hashlib
from storage.mysql import get_db
from models.future_vote import FutureVote
from datetime import datetime


def saveFutureVote(db, future_id: int, ip: str, userAgent: str, vote: int) -> int:
    uniq_user_hash = get_user_hash(ip, userAgent)

    model = getFutureVote(db, future_id, uniq_user_hash)
    date = datetime.now().isoformat()

    if model:
        model.vote = vote
        model.updated_at = date
    else:
        model = FutureVote(
            future_id=future_id,
            uniq_user_hash=uniq_user_hash,
            vote=vote,
            created_at=date,
            updated_at=date,
        )
        db.add(model)

    db.commit()
    db.refresh(model)
    return model.id


def getFutureVote(db, future_id: int, user_hash: str) -> FutureVote:
    return db.query(FutureVote).filter_by(future_id=future_id, uniq_user_hash=user_hash).one_or_none()


def get_user_hash(ip: str, userAgent: str) -> str:
    """Создаём уникальный хэш для пользователя на основе IP и User-Agent"""
    raw = f"{ip}:{userAgent}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
