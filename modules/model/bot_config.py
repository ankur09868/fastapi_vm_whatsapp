from pydantic import BaseModel
# Define the Pydantic model for the request body
class BotConfig(BaseModel):
    word: str
    reply_message: str