from sqlalchemy import Column, Integer, String
from models.base import Base

class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String(256), unique=True, index=True, nullable=False)
    master_uuid = Column(String(36), nullable=False)
    share_url = Column(String(256), nullable=False)
