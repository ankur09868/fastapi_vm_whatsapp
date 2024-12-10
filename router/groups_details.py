from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import JSONResponse
from modules.store_get_data.groups import get_groups_from_db , get_group_details_by_id , get_group_activity , get_members_from_db # Import the function

router = APIRouter()

@router.get("/get_groups")
async def get_groups(tenant:Request):
    try:
          # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        groups = get_groups_from_db(tenant_id)  # Call the function to fetch data from the database
        return JSONResponse(content={"groups": groups})
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch groups.")

@router.get("/get_members")
async def get_members(tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        members = get_members_from_db(tenant_id)  # Fetch data from the database
        return JSONResponse(content={"members": members})
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching members: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch members.")

# FastAPI endpoint for group details
@router.get("/get_group_details/{id}")
async def get_group_details(id: int,tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        group_details = get_group_details_by_id(id)

        if group_details:
            return {"message": "Group details fetched successfully", "data": group_details}
        else:
            raise HTTPException(status_code=404, detail=f"Group with ID {id} not found")
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching group details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch group details.")

@router.get("/get_group_activity/{group_name}")
async def get_activity(group_name: str,tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        grp_activity = get_group_activity(group_name)

        if grp_activity:
            return {"message": "Group activity fetched successfully", "data": grp_activity}
        else:
            raise HTTPException(status_code=404, detail=f"Group activity not found for {group_name}")
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching group activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch group activity.")

# @router.delete("/delete_group/{group_name}")
# async def delete_group(group_name:str):
#     del_grp = delete_grp(group_name)

#     if del_grp :
#         return {"message": "Group delete successfully", "data": del_grp}
#     else:
#          raise HTTPException(status_code=404, detail=f"Group with ID {id} not found")