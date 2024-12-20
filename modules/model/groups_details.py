from pydantic import BaseModel
from typing import Optional, List


class Member(BaseModel):
    id: int
    name: str
    phone_number: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[float] = None
    avatar: Optional[str] = None

class Group(BaseModel):
    id: int
    name: str
    description: str
    members: List[Member]
    botconfg_id = int

