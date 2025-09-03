from storage.mysql import get_db
from models.feedback import Feedback
from datetime import datetime
from infrastructure.helpers.uniq_user_hash_helper import get_user_hash


def saveFeedback(db, ip: str, userAgent: str, name: str, email: str, message: str, subscribe: bool) -> int:
    date = datetime.now().isoformat()
    uniq_user_hash = get_user_hash(ip, userAgent)

    feedback = Feedback(
        name=name,
        email=email,
        message=message,
        subscribe='yes' if subscribe else 'no',
        created_at=date,
        updated_at=date,
        uniq_user_hash=uniq_user_hash,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback.id
