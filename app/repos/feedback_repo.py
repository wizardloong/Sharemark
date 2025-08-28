from storage.mysql import get_db
from models.feedback import Feedback
from datetime import datetime


def saveFeedback(name: str, email: str, message: str, subscribe: bool) -> str:
    db = next(get_db())

    date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z')

    feedback = Feedback(
        name=name,
        email=email,
        message=message,
        subscribe='yes' if subscribe else 'no',
        created_at=date,
        updated_at=date,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback.id
