from pydantic import BaseModel
from typing import List 

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
    sentimentData: List[SentimentData]
    engagementData: List[EngagementData]
    topicsData: List[dict]