from fastapi import APIRouter,HTTPException
from modules.model.schedule_model import ScheduleMessageRequest
from modules.store_get_data.schedule_message import save_scheduled_message_to_db,get_all_scheduled_messages
router = APIRouter()


@router.post("/create_schedule_message")
async def schedule_message(data: ScheduleMessageRequest):
    try:
        response = save_scheduled_message_to_db(data)
        return response
    except Exception as e:
        print(f"Error occurred while scheduling message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}",
        )

@router.get("/get_schedule_messages")
async def get_schedule_messages():
    try:
        response = get_all_scheduled_messages()
        return {"scheduled_messages": response}
    except Exception as e:
        print(f"Error occurred while fetching scheduled messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}",
        )