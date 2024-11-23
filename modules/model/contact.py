from pydantic import BaseModel

# Pydantic model for the request body

class UpdateRatingRequest(BaseModel):
    group_id:int
    member_id: int
    rating: float