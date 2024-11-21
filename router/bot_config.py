import psycopg2
from fastapi import APIRouter, HTTPException, Body
from modules.config.database import conn_config
from modules.model.bot_config import BotConfig
from modules.store_get_data.bot_config import store_bot_config

# Initialize the FastAPI router
router = APIRouter()

# FastAPI POST endpoint to accept word and reply_message from frontend
@router.post("/store_bot_data")
async def create_bot_config(bot_config: BotConfig):
    response = store_bot_config(bot_config.word, bot_config.reply_message)
    return response
