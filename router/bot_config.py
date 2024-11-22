from fastapi import APIRouter, HTTPException, status
from typing import List
import psycopg2
from modules.config.database import conn_config
from modules.store_get_data.bot_config import fetch_bot_config_from_db,store_bot_config
from modules.model.bot_config import BotConfigResponse,BotConfig
import json

# Initialize the FastAPI router
bot_config_router = APIRouter()

@bot_config_router.get("/get_bot_config", response_model=BotConfigResponse)
async def get_bot_config():
    try:
        bot_config = fetch_bot_config_from_db()
        return bot_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f" {str(e)}")
    
@bot_config_router.post("/add_bot_config",status_code=status.HTTP_201_CREATED)
async def add_bot_config(bot:BotConfig):
    try:
        add_bot = store_bot_config(bot)
        return add_bot
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"")
