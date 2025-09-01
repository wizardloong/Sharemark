from typing import Optional, List
from pydantic import BaseModel, EmailStr, constr, Field

class ShareRequest(BaseModel):
    folder_id: str
    name: str
    bookmarks: List[dict]
    can_write: bool
    sharemark_uuid: str

class UpdateRequest(BaseModel):
    name: Optional[str]
    bookmarks: Optional[List[dict]]

class Bookmark(BaseModel):
    title: str
    url: str

class SharedFolder(BaseModel):
    folder_id: str
    name: str
    bookmarks: List[Bookmark]
    can_write: bool
    owner_uuid: str

class FeedbackRequest(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=100)
    email: EmailStr
    message: constr(strip_whitespace=True, min_length=1, max_length=2000)
    subscribe: bool = False

class VoteRequest(BaseModel):
    feature_id: int = Field(..., description="Future Feature ID")
    vote_count: int = Field(..., ge=0, le=3, description="Votes count (0–3)")

class PriceRequest(BaseModel):
    price: int = Field(..., ge=0, le=101, description="Price in dollars")
