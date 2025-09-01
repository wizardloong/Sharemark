from sqlalchemy import Column, Integer, String, Text, CheckConstraint
from models.base import Base

class FutureVote(Base):
    __tablename__ = "future_votes"

    id = Column(Integer, primary_key=True, index=True)
    future_id = Column(Integer, index=True, nullable=False)
    uniq_user_hash = Column(String(256), index=True, nullable=False, unique=True)
    vote = Column(Integer, nullable=False)
    created_at = Column(String(36), nullable=False)  # ISO 8601 format
    updated_at = Column(String(36), nullable=False)  # ISO 8601 format

    __table_args__ = (
        CheckConstraint('vote BETWEEN 0 AND 3', name='check_vote_range'),
    )

    def __repr__(self):
        return f"<FutureVotesData(future={self.future_id}, vote={self.vote}, updated_at={self.updated_at})>"
