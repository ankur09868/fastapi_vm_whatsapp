from fastapi import APIRouter, HTTPException, status,Request
from typing import List
import psycopg2
from modules.config.database import conn_config
from modules.store_get_data.bot_config import fetch_bot_config_from_db,store_bot_config,delete_bot_config,update_bot_config
from modules.model.bot_config import BotConfigResponse,BotConfig
import json

# Initialize the FastAPI router
bot_config_router = APIRouter()


@bot_config_router.get("/get_bot_config", response_model=BotConfigResponse)
async def get_bot_config(tenant:Request):
    try:
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        # Attempt to fetch bot configuration from the database
        bot_config = fetch_bot_config_from_db(tenant_id)
        print(bot_config)
        if not bot_config:
            # If no bot config is found, raise a 404 not found error
            raise HTTPException(status_code=200, detail="Bot configuration not found")
        return bot_config
    except Exception as e:
        # Raise a detailed 500 Internal Server Error with the exception message
        raise HTTPException(status_code=500, detail=f"Error fetching bot configuration: {str(e)}")


@bot_config_router.post("/add_bot_config", status_code=status.HTTP_201_CREATED)
async def add_bot_config(bot: BotConfig, tenant: Request):
    try:
        # Print incoming bot configuration details
        print(f"Received Bot Configuration: {bot.dict()}")
        
        # Print tenant ID extraction
        tenant_id = tenant.headers.get("X-tenant-id")
        print(f"Extracted Tenant ID: {tenant_id}")
        
        # Validate tenant ID
        if not tenant_id:
            print("ERROR: No tenant ID provided in headers")
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        # Print attempt to store bot configuration
        print(f"Attempting to store bot configuration for tenant {tenant_id}")
        
        # Attempt to add the bot configuration to the database
        try:
            add_bot = store_bot_config(bot, tenant_id)
            print(f"Store bot config result: {add_bot}")
        except Exception as store_error:
            print(f"Error in store_bot_config: {store_error}")
            raise
        
        # Check if bot configuration was successfully added
        if not add_bot:
            print("Failed to add bot configuration")
            raise HTTPException(status_code=400, detail="Failed to add bot configuration. Please check the input data.")
        
        print("Bot configuration added successfully")
        return {"message": "Bot configuration added successfully"}
    
    except HTTPException as http_error:
        # Log HTTP exceptions with their specific details
        print(f"HTTP Exception: {http_error.status_code} - {http_error.detail}")
        raise
    
    except Exception as e:
        # Print full exception details for unexpected errors
        print(f"Unexpected Error: {type(e).__name__}")
        print(f"Error Details: {str(e)}")
        print(f"Error Args: {e.args}")
        import traceback
        print("Full Traceback:")
        traceback.print_exc()
        
        # Raise a detailed 500 Internal Server Error with the exception message
        raise HTTPException(status_code=500, detail=f"Error adding bot configuration: {str(e)}")

@bot_config_router.delete("/delete_bot_config/{bot_id}", status_code=status.HTTP_200_OK)
async def delete_botConfig(bot_id: int,tenant:Request):
    try:
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        # Assuming delete_bot_config returns None or some indication when the bot is not found
        delete_bot = delete_bot_config(bot_id,tenant_id)
        if not delete_bot:
            # If the bot is not found, raise a 404 error with a custom message
            raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found")
        return {"message": f"Bot with ID {bot_id} has been deleted successfully"}
    except Exception as e:
        print(f"Error while deleting Bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@bot_config_router.put("/update_bot_config/{bot_id}", status_code=status.HTTP_200_OK)
async def update_botConfig(bot_id: int, bot: BotConfig,tenant:Request):
    try:
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        # Assuming update_bot_config returns None or some indication when the bot is not found
        update_bot = update_bot_config(bot_id, bot,tenant_id)
        if not update_bot:
            # If the bot is not found, raise a 404 error with a custom message
            raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found")
        return {"message": f"Bot with ID {bot_id} has been updated successfully"}
    except Exception as e:
        print(f"Error while updating Bot {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")