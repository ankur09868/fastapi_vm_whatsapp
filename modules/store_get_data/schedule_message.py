from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from datetime import datetime
import psycopg2
from modules.config.database import conn_config
from modules.model.schedule_model import ScheduleMessageRequest
import json 
import mimetypes
import validators


def save_scheduled_message_to_db(data: ScheduleMessageRequest):
    try:
        # Validate messageType and media
        media = data.media
        
        # Enforce media presence for specific message types
        if data.messageType in ["image", "document", "video"]:
            if not media:
                raise HTTPException(
                    status_code=400,
                    detail=f"Media data is required for message type '{data.messageType}'."
                )
            
            # Extract media fields
            media_url = media.url
            media_type = media.type
            media_name = media.name

            # Validate media URL
            if not validators.url(str(media_url)):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid media URL for message type '{data.messageType}'."
                )

            # Extract file extension from media type
            file_extension = mimetypes.guess_extension(media_type)
            if not file_extension:
                # Fallback for common media types
                if "image" in media_type:
                    file_extension = ".jpg"
                elif "video" in media_type:
                    file_extension = ".mp4"
                elif "document" in media_type:
                    file_extension = ".pdf"
                else:
                    file_extension = ".bin"  # Default for unknown types

            # Add file extension to media object
            media_dict = media.dict()
            media_dict["file_extension"] = file_extension
            media_dict["url"] = str(media_dict["url"])  # Convert URL to string

            # Serialize media dictionary to JSON
            media_json = json.dumps(media_dict)

        elif data.messageType == "text":
            # Validate content for text messages
            if not data.content.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Message content cannot be empty for text messages."
                )
            media_json = None  # No media required for text

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported message type: {data.messageType}"
            )

        # Convert groups to a comma-separated string if it's a list
        if isinstance(data.groups, list):
            groups = ', '.join(data.groups)
        else:
            raise HTTPException(status_code=400, detail="Groups must be provided as a list.")

        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Insert the scheduled message into the database
        query = """
        INSERT INTO whatsapp_scheduled_messages (groups, message_type, message_content, schedule_time, media, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        cursor.execute(
            query,
            (groups, data.messageType, data.content, data.scheduledTime, media_json, "pending"),
        )
        message_id = cursor.fetchone()[0]
        conn.commit()

        return {"message": "Scheduled message saved successfully", "id": message_id}

    except Exception as e:
        print(f"Error saving scheduled message: {e}")
        raise HTTPException(status_code=500, detail="Failed to save the scheduled message.")

    finally:
        if "conn" in locals() and conn:
            conn.close()  # Ensure the connection is closed

    
def get_all_scheduled_messages():
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Fetch all scheduled messages
        query = "SELECT id, groups, message_type, message_content, schedule_time, status, media FROM whatsapp_scheduled_messages;"
        cursor.execute(query)
        messages = cursor.fetchall()

        # Map the results to a list of dictionaries
        scheduled_messages = [
            {
                "id": row[0],
                "groups": [row[1]],
                "messageType": row[2],
                "messageContent": row[3],
                "scheduleTime": row[4],
                "media":row[6],
                "status": row[5]
            }
            for row in messages
        ]

        conn.close()
        return scheduled_messages
    except Exception as e:
        print(f"Error fetching scheduled messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scheduled messages")
    

def update_schedule_message(message_id,updated_message):
    try:
        # Enforce media presence for specific message types
        if updated_message.messageType in ["image", "document", "video"]:
            if not updated_message.media:
                raise HTTPException(
                    status_code=400,
                    detail=f"Media data is required for message type '{updated_message.messageType}'."
                )
        
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Prepare media details
        media_url = updated_message.media.url if updated_message.media else None
        media_type = updated_message.media.type if updated_message.media else None
        media_name = updated_message.media.name if updated_message.media else None

        # Update query
        update_query = """
        UPDATE whatsapp_scheduled_messages
        SET 
            groups = %s,
            message_type = %s,
            content = %s,
            media_url = %s,
            media_type = %s,
            media_name = %s,
            scheduled_time = %s
        WHERE id = %s
        """
        cursor.execute(
            update_query,
            (
                json.dumps(updated_message.groups),
                updated_message.messageType,
                updated_message.content,
                media_url,
                media_type,
                media_name,
                updated_message.scheduledTime,
                message_id,
            ),
        )

        conn.commit()

        # Check if update succeeded
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Message not found or no changes made")

        return {"message": f"Scheduled message {message_id} updated successfully"}

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_schedule_message(message_id):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Delete query
        delete_query = "DELETE FROM whatsapp_scheduled_messages WHERE id = %s"
        cursor.execute(delete_query, (message_id,))
        conn.commit()

        # Check if delete succeeded
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Message not found")

        return {"message": f"Scheduled message {message_id} deleted successfully"}

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
