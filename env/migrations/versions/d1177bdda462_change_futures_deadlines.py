"""change futures deadlines

Revision ID: d1177bdda462
Revises: 9238d068d37f
Create Date: 2025-09-03 15:05:56.169599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from storage.mysql import SessionLocal  # Импортируйте SessionLocal вместо get_db
from repos.future_repo import updateBySlug
from models.future import FutureSlugs

# revision identifiers, used by Alembic.
revision: str = 'd1177bdda462'
down_revision: Union[str, None] = '9238d068d37f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем сессию вручную
    db = SessionLocal()
    try:
        updateBySlug(db, FutureSlugs.SYNC, {"deadline_quarter": 2})
        updateBySlug(db, FutureSlugs.HEALTHCHECK, {"deadline_quarter": 3})
        updateBySlug(db, FutureSlugs.EXPORT, {"deadline_quarter": 3})
        updateBySlug(db, FutureSlugs.SELFHOSTED, {"deadline_quarter": 4})
        db.commit()  # Не забываем коммитить изменения
    except Exception:
        db.rollback()  # Откатываем при ошибке
        raise
    finally:
        db.close()  # Всегда закрываем сессию


def downgrade() -> None:
    # Аналогично для отката, если нужно
    db = SessionLocal()
    try:
        # Здесь код для отката изменений
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()