from fastapi import APIRouter, HTTPException,Request
from fastapi.responses import JSONResponse
from modules.model.contact import UpdateRatingRequest
import psycopg2
from modules.config.database import conn_config
import traceback



contactrouter = APIRouter()

@contactrouter.put("/update-rating")
async def update_contact(request: UpdateRatingRequest, tenant: Request):
    conn = None
    cursor = None
    
    try:
        # Extract tenant_id from headers
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        # Extract the values from the request
        group_id = request.group_id
        member_id = request.member_id
        rating = request.rating
        
        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()
        
        # SQL query to update the rating
        query = """
            UPDATE whatsapp_group_members
            SET rating = %s
            WHERE group_id = %s AND member_id = %s AND tenant_id=%s
            RETURNING member_id;
        """

        # Update the rating for the member
        cursor.execute(query, (rating, group_id, member_id,tenant_id))
        
        # Fetch the result of the update
        updated_row = cursor.fetchone()
        
        if updated_row is None:
            raise HTTPException(status_code=404, detail="Member not found or no change in rating")
        
        # Commit the transaction
        conn.commit()

        return JSONResponse(
            content={"message": "Rating updated successfully", "member_id": member_id, "new_rating": rating},
            status_code=200
        )

    except psycopg2.Error as db_error:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating rating: {str(e)}")

    finally:
        # Close the cursor and connection
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            pass  # In case there's an error while closing the database connection