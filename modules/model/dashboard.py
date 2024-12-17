from pydantic import BaseModel
from typing import List ,Optional

# Model to structure the sentiment data
class SentimentData(BaseModel):
    day: str
    Positive: int
    Neutral: int
    Negative: int
    Commercial: int

# Model to structure the response

class EngagementData(BaseModel):
    metric: str
    score: float
class DashboardResponse(BaseModel):
    name: str
    sentimentData: Optional[List[SentimentData]] = None
    engagementData: Optional[List[EngagementData]] = None
    topicsData: Optional[List[dict]] = None