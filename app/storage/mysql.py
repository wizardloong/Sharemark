from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_URL = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"
)

engine = create_engine(
    DB_URL, 
    pool_size=5,          # кол-во постоянных соединений в пуле
    max_overflow=5,       # кол-во дополнительных соединений при пиковых нагрузках
    pool_recycle=1800,    # каждые 1800 секунд (30 мин) соединение обновляется
    echo=False, 
    pool_pre_ping=True    # проверка соединения перед использованием
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()