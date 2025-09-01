from storage.mysql import get_db
from models.future import Future


def saveFuture(name: str, slug: str, description: str, icon_url: str, icon_path:str, deadline_yead: int, deadline_quarter: int) -> int:
    db = next(get_db())

    model = Future(
        name=name,
        slug=slug,
        description=description,
        icon_url=icon_url,
        icon_path=icon_path,
        deadline_year=deadline_yead,
        deadline_quarter=deadline_quarter,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    return model.id

def getFutures() -> list[Future]:
    db = next(get_db())
    return db.query(Future).filter(Future.is_active == True).all()
