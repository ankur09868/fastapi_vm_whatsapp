from fastapi import APIRouter, HTTPException, status
from typing import List
import psycopg2
from modules.config.database import conn_config
from modules.store_get_data.bot_config import fetch_bot_config_from_db,store_bot_config,delete_bot_config,updata_bot_config
from modules.model.bot_config import BotConfigResponse,BotConfig
import json

# Initialize the FastAPI router
bot_config_router = APIRouter()


@bot_config_router.get("/get_bot_config", response_model=BotConfigResponse)
async def get_bot_config():
    try:
        # Attempt to fetch bot configuration from the database
        bot_config = fetch_bot_config_from_db()
        if not bot_config:
            # If no bot config is found, raise a 404 not found error
            raise HTTPException(status_code=404, detail="Bot configuration not found")
        return bot_config
    except Exception as e:
        # Raise a detailed 500 Internal Server Error with the exception message
        raise HTTPException(status_code=500, detail=f"Error fetching bot configuration: {str(e)}")

@bot_config_router.post("/add_bot_config", status_code=status.HTTP_201_CREATED)
async def add_bot_config(bot: BotConfig):
    try:
        # Attempt to add the bot configuration to the database
        add_bot = store_bot_config(bot)
        if not add_bot:
            # If the bot config couldn't be added, raise a 400 error
            raise HTTPException(status_code=400, detail="Failed to add bot configuration. Please check the input data.")
        return {"message": "Bot configuration added successfully"}
    except Exception as e:
        # Raise a detailed 500 Internal Server Error with the exception message
        raise HTTPException(status_code=500, detail=f"Error adding bot configuration: {str(e)}")

@bot_config_router.delete("/delete_bot_config/{bot_id}", status_code=status.HTTP_200_OK)
async def delete_botConfig(bot_id: int):
    try:
        # Assuming delete_bot_config returns None or some indication when the bot is not found
        delete_bot = delete_bot_config(bot_id)
        if not delete_bot:
            # If the bot is not found, raise a 404 error with a custom message
            raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found")
        return {"message": f"Bot with ID {bot_id} has been deleted successfully"}
    except Exception as e:
        print(f"Error while deleting Bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@bot_config_router.put("/update_bot_config/{bot_id}", status_code=status.HTTP_200_OK)
async def update_botConfig(bot_id: int, bot: BotConfig):
    try:
        # Assuming update_bot_config returns None or some indication when the bot is not found
        update_bot = updata_bot_config(bot_id, bot)
        if not update_bot:
            # If the bot is not found, raise a 404 error with a custom message
            raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found")
        return {"message": f"Bot with ID {bot_id} has been updated successfully"}
    except Exception as e:
        print(f"Error while updating Bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")