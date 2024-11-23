from fastapi import APIRouter,HTTPException
from fastapi.responses import JSONResponse
from modules.model.contact import UpdateRatingRequest
import psycopg2
from modules.config.database import conn_config

contactrouter = APIRouter()

@contactrouter.put("/update-rating")
async def update_contact(request: UpdateRatingRequest):
    #Extract the values from the request
    group_id = request.group_id
    member_id = request.member_id
    rating = request.rating

    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Update the rating for the member in the whatsapp_group_members table
        cursor.execute("""
            UPDATE whatsapp_group_members
            SET rating = %s
            WHERE group_id = %s AND member_id = %s
            RETURNING id;
        """, (rating, group_id,member_id))

        # Fetch the result of the update
        updated_row = cursor.fetchone()

        if updated_row is None:
            raise HTTPException(status_code=404, detail="Member not found or no change in rating")

        # Commit the transaction
        conn.commit()

        # Return a success response with updated member data
        return JSONResponse(content={"message": "Rating updated successfully", "member_id": member_id, "new_rating": rating}, status_code=200)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating rating: {str(e)}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
# @contactrouter.put("/get-contact/{}")