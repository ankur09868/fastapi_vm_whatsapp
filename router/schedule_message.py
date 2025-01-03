from fastapi import APIRouter,HTTPException,status,Request
from modules.model.schedule_model import ScheduleMessageRequest
from modules.store_get_data.schedule_message import save_scheduled_message_to_db,get_all_scheduled_messages,update_schedule_message,delete_schedule_message
router = APIRouter()

    
@router.post("/create_schedule_message")
async def schedule_message(data: ScheduleMessageRequest,tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        # Attempt to save the scheduled message
        response = save_scheduled_message_to_db(data,tenant_id)
        if not response:
            # If saving failed, raise a 400 Bad Request
            raise HTTPException(status_code=400, detail="Failed to schedule the message.")
        return {"message": "Scheduled message created successfully", "data": response}
    except Exception as e:
        print(f"Unexpected error occurred while scheduling message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@router.get("/get_schedule_messages")
async def get_schedule_messages(tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        # Attempt to retrieve all scheduled messages
        response = get_all_scheduled_messages(tenant_id)
        
        # If no messages are found, return an empty list
        if not response:
            return {"scheduled_messages": []}
        
        # Return the scheduled messages if found
        return {"scheduled_messages": response}
    
    except Exception as e:
        # Catch any other general exceptions
        print(f"Unexpected error occurred while fetching scheduled messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
from typing import Any

@router.put("/update_scheduled_message/{message_id}", status_code=status.HTTP_200_OK)
async def update_scheduledmessage(message_id: int, updated_message: ScheduleMessageRequest,tenant:Request)-> Any:
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")

        # Attempt to update the scheduled message
        update_message = update_schedule_message(message_id, updated_message,tenant_id)
        
        if not update_message:
            # If the message update failed, raise a 404 error
            raise HTTPException(status_code=404, detail=f"Message with ID {message_id} not found")
        
        return {"message": "Scheduled message updated successfully"}
    
    except Exception as e:
        # For any other general exceptions
        print(f"Unexpected error while updating message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@router.delete("/delete_scheduled_message/{message_id}/", status_code=status.HTTP_200_OK)
async def delete_scheduled_message(message_id: int,tenant:Request):
    try:
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=404, detail=f"Message with ID {message_id} not found")

        delete_message = delete_schedule_message(message_id,
                                                 tenant_id)
        if not delete_message:
            raise HTTPException(status_code=404,detail=f"Message with ID{message_id} not found")
        return{"message":f"Scheduled message with ID {message_id} delete successfully"}
    
    except Exception as e :
        # For any other general exceptions
        print(f"Unexpected error while deleting message {message_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")