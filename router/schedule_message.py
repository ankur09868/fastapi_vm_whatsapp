from fastapi import APIRouter
from modules.model.schedule_model import ScheduleMessageRequest
from modules.store_get_data.schedule_message import save_scheduled_message_to_db,get_all_scheduled_messages
router = APIRouter()


@router.post("/create_schedule_message")
async def schedule_message(data: ScheduleMessageRequest):
    response = save_scheduled_message_to_db(data)
    return response

@router.get("/get_schedule_messages")
async def get_schedule_messages():
    response = get_all_scheduled_messages()
    return {"scheduled_messages": response}

