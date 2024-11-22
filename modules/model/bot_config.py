from pydantic import BaseModel
from typing import List, Optional

class BotLog(BaseModel):
    message: str  # Message content flagged as spam
    action: str  # Action taken (e.g., "Warned")
    phone_or_name : Optional[str] = None

class BotConfig(BaseModel):
    
    name: str
    isBotEnabled: Optional[bool] = True
    spamKeywords: Optional[List[str]] = ['spam']
    messageLimit: Optional[int] = 5
    replyMessage: Optional[str] = None
    spamAction: Optional[str] = None
    logs: Optional[List[BotLog]] = []

class BotConfigResponse(BaseModel):
    bots: List[BotConfig]