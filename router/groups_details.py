from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import JSONResponse
from modules.store_get_data.groups import get_groups_from_db , get_group_details_by_id , get_group_activity , get_members_from_db,update_botconfig_in_db,delete_group # Import the function

router = APIRouter()

@router.get("/get_groups")
def get_groups(tenant:Request):
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
def get_members(tenant:Request):
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
def get_group_details(id: int,tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        group_details = get_group_details_by_id(id,tenant_id)

        if group_details:
            return {"message": "Group details fetched successfully", "data": group_details}
        else:
            raise HTTPException(status_code=404, detail=f"Group with ID {id} not found")
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching group details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch group details.")

@router.get("/get_group_activity/{group_name}")
def get_activity(group_name: str,tenant:Request):
    try:
         # Extract tenant_id from request headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        grp_activity = get_group_activity(group_name,tenant_id)

        if grp_activity:
            return {"message": "Group activity fetched successfully", "data": grp_activity}
        else:
            raise HTTPException(status_code=404, detail=f"Group activity not found for {group_name}")
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching group activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch group activity.")
    

@router.post("/group_update_botconfig/{group_id}")
def update_botconfig(group_id: int, request: Request):
    try:
        # Extract tenant_id from request headers
        tenant_id = request.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        # Get botconfig_id from request body (parsed as JSON)
        request_data = request.json()  # Parse the JSON body
        botconfig_id = request_data.get("botconfig_id")

        if not botconfig_id:
            raise HTTPException(status_code=400, detail="botconfig_id is missing in the request body.")
        
        # Update the botconfig_id in the database for the specified group and tenant
        update_botconfig_in_db(group_id, tenant_id, botconfig_id)

        return {"message": f"botconfig_id updated successfully for group ID {group_id}"}
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error updating botconfig_id: {e}")
        raise HTTPException(status_code=500, detail="Failed to update botconfig_id.")

@router.delete("/delete_group/{group_name}")
def delete_group_endpoint(group_name: str, req: Request):
    try:
        # Extract tenant_id from request headers
        tenant_id = req.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        del_grp = delete_group(group_name,tenant_id)

        if del_grp:
            return {"message": f"{del_grp} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Group with name {group_name} not found")
    except Exception as e:
        # Log the error for debugging
        print(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete group.")