from sqlalchemy import Column, Integer, String
from models.base import Base

class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    master_uuid = Column(String, nullable=False)
    share_url = Column(String, nullable=False)
