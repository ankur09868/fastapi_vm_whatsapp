from fastapi import APIRouter,HTTPException
from fastapi.responses import JSONResponse
from modules.store_get_data.groups import get_groups_from_db , get_group_details_by_id , get_group_activity , get_members_from_db # Import the function

router = APIRouter()

@router.get("/get_groups")
async def get_groups():
    groups = get_groups_from_db()  # Call the function to fetch data from the database
    return JSONResponse(content={"groups": groups})

@router.get("/get_members")
async def get_members():
    members = get_members_from_db()  # Fetch data from the database
    return JSONResponse(content={"members": members})


# FastAPI endpoint for group details
@router.get("/get_group_details/{id}")
async def get_group_details(id: int):
    group_details = get_group_details_by_id(id)

    if group_details:
        return {"message": "Group details fetched successfully", "data": group_details}
    else:
        raise HTTPException(status_code=404, detail=f"Group with ID {id} not found")
    
@router.get("/get_group_activity/{group_name}")
async def get_activity(group_name:str):
    grp_activity = get_group_activity(group_name)

    if grp_activity :
        return {"message": "Group activity fetched successfully", "data": grp_activity}
    else:
         raise HTTPException(status_code=404, detail=f"Group with ID {id} not found")

    
