from sqlalchemy import Column, Integer, String, Text, CheckConstraint
from models.base import Base

class UserPrice(Base):
    __tablename__ = "user_prices"

    id = Column(Integer, primary_key=True, index=True)
    uniq_user_hash = Column(String(256), index=True, nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(String(36), nullable=False)  # ISO 8601 format
    updated_at = Column(String(36), nullable=False)  # ISO 8601 format

    def __repr__(self):
        return f"<UserPricesData(uniq_user_id={self.uniq_user_hash}, price={self.price}, updated_at={self.updated_at})>"
