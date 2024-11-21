from pydantic import BaseModel,HttpUrl
from datetime import datetime
from typing import Optional,List

class Media(BaseModel):
    url: HttpUrl
    type: str
    name: str

class ScheduleMessageRequest(BaseModel):
    groups: List[str]
    messageType: str
    content: str
    media: Optional[Media] = None
    scheduledTime: datetime
