# schemas.py
from typing import Optional

from pydantic import BaseModel

class ShareRequest(BaseModel):
    folder_id: str
    name: str
    bookmarks: list
    can_write: bool

class UpdateRequest(BaseModel):
    name: Optional[str]
    bookmarks: Optional[list]
