from storage.mysql import get_db
from models.future import Future


def saveFuture(
        db,
        name: str, 
        slug: str, 
        description: str, 
        icon_url: str, 
        icon_path:str, 
        deadline_yead: int, 
        deadline_quarter: int,
        is_active: bool = True
) -> int:
    model = Future(
        name=name,
        slug=slug,
        description=description,
        icon_url=icon_url,
        icon_path=icon_path,
        deadline_year=deadline_yead,
        deadline_quarter=deadline_quarter,
        is_active=is_active,
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    return model.id

def getFutures(db) -> list[Future]:
    return db.query(Future).filter(Future.is_active == True).all()

def updateBySlug(
        db,
        slug: str,
        data: dict,
) -> int:
    model = db.query(Future).filter(Future.slug == slug).one_or_none()
    if not model:
        return None
    
    for key, value in data.items():
        setattr(model, key, value)


    db.commit()
    db.refresh(model)

    return model.id
