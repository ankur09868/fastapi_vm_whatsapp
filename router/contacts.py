from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from modules.model.contact import UpdateRatingRequest
import psycopg2
from modules.config.database import conn_config
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contact_router.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

contactrouter = APIRouter()

@contactrouter.put("/update-rating")
async def update_contact(request: UpdateRatingRequest):
    conn = None
    cursor = None
    
    try:
        # Log the incoming request
        logger.info(f"Received update rating request - Group ID: {request.group_id}, Member ID: {request.member_id}, Rating: {request.rating}")
        
        # Extract the values from the request
        group_id = request.group_id
        member_id = request.member_id
        rating = request.rating
        
        # Log connection attempt
        logger.debug("Attempting to connect to database")
        
        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()
        
        logger.debug("Successfully connected to database")
        
        # Log the SQL query
        query = """
            UPDATE whatsapp_group_members
            SET rating = %s
            WHERE group_id = %s AND id = %s
            RETURNING id;
        """
        logger.debug(f"Executing query: {query} with params: {(rating, group_id, member_id)}")

        # Update the rating for the member
        cursor.execute(query, (rating, group_id, member_id))
        
        # Fetch the result of the update
        updated_row = cursor.fetchone()
        
        if updated_row is None:
            logger.warning(f"No member found for group_id: {group_id} and member_id: {member_id}")
            raise HTTPException(status_code=404, detail="Member not found or no change in rating")
        
        logger.info(f"Successfully updated rating for member_id: {member_id}")
        
        # Commit the transaction
        conn.commit()
        logger.debug("Transaction committed successfully")

        return JSONResponse(
            content={"message": "Rating updated successfully", "member_id": member_id, "new_rating": rating},
            status_code=200
        )

    except psycopg2.Error as db_error:
        if conn:
            conn.rollback()
        logger.error(f"Database error occurred: {str(db_error)}")
        logger.error(f"Database error details: {db_error.pgerror if hasattr(db_error, 'pgerror') else 'No details available'}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")

    except HTTPException as http_error:
        # Re-raise HTTP exceptions without modification
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Unexpected error occurred: {str(e)}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating rating: {str(e)}")

    finally:
        # Close the cursor and connection
        try:
            if cursor:
                cursor.close()
                logger.debug("Database cursor closed")
            if conn:
                conn.close()
                logger.debug("Database connection closed")
        except Exception as e:
            logger.error(f"Error while closing database connections: {str(e)}")