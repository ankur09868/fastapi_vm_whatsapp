from pydantic import BaseModel
from typing import List, Optional,Dict
from datetime import datetime

class BotLog(BaseModel):
    id:int
    message: str  # Message content flagged as spam
    action: str  # Action taken (e.g., "Warned")
    phone_or_name : Optional[str] = None
    group_name: Optional[str] = None
    time: Optional[datetime] = None

class BotConfig(BaseModel):
    id: Optional[int]
    name: Optional[str] = None 
    isBotEnabled: Optional[bool] = True
    spamKeywordsActions: Optional[Dict[str, str]] = {"spam": "warn"}
    messageLimit: Optional[int] = 5
    replyMessage: Optional[str] = None
    aidetection:Optional[bool] =False
    aireply: Optional[bool] =False
    aiSpamActionPrompt:Optional[str] = None
    logs: Optional[List[BotLog]] = []

    
class BotConfigResponse(BaseModel):
    bots: List[BotConfig]