from pydantic import BaseModel

# Model to structure the sentiment data
class SentimentData(BaseModel):
    day: str
    Positive: int
    Neutral: int
    Negative: int
    Commercial: int

# Model to structure the response
class DashboardResponse(BaseModel):
    name: str
    sentimentData: list[SentimentData]
    topicsData: list[dict]