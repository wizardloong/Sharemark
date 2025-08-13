from typing import Optional, List
from pydantic import BaseModel

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