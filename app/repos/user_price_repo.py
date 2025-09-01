from models.user_price import UserPrice
from datetime import datetime
from infrastructure.helpers.uniq_user_hash_helper import get_user_hash


def savePrice(db, ip: str, userAgent: str, price: int) -> int:
    uniq_user_hash = get_user_hash(ip, userAgent)

    model = getPrice(db, uniq_user_hash)
    date = datetime.now().isoformat()

    if model:
        model.price = price
        model.updated_at = date
    else:
        model = UserPrice(
            uniq_user_hash=uniq_user_hash,
            price=price,
            created_at=date,
            updated_at=date,
        )
        db.add(model)

    db.commit()
    db.refresh(model)
    return model.id


def getPrice(db, user_hash: str) -> UserPrice:
    return db.query(UserPrice).filter_by(uniq_user_hash=user_hash).one_or_none()
