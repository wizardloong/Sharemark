from sqlalchemy import Column, Integer, String, Text, CheckConstraint, Boolean
from models.base import Base

class Future(Base):
    __tablename__ = "futures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    slug = Column(String(256), index=True, nullable=False)
    description = Column(Text, nullable=False)
    icon_url = Column(String(256))
    icon_path = Column(String(256))
    deadline_year = Column(Integer, nullable=False)
    deadline_quarter = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint('quarter BETWEEN 1 AND 4', name='check_quarter_range'),
    )

    def __repr__(self):
        return f"<FuturesData(year={self.year}, quarter={self.quarter}, name={self.name})>"
