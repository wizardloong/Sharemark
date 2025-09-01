from sqlalchemy import Column, Integer, String, Text
from models.base import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    email = Column(String(256), nullable=False)
    message = Column(Text, nullable=False)
    subscribe = Column(String(3), nullable=False)  # 'yes' or 'no'
    created_at = Column(String(36), nullable=False)  # ISO 8601 format
    updated_at = Column(String(36), nullable=False)  # ISO 8601 format
