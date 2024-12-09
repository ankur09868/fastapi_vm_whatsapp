from fastapi import APIRouter, HTTPException,Request
from pydantic import ValidationError
from datetime import datetime
import psycopg2
from modules.config.database import conn_config
from modules.model.schedule_model import ScheduleMessageRequest
import json 
import mimetypes
import validators
import pytz


def save_scheduled_message_to_db(data: ScheduleMessageRequest,tenant_id):
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
        
        # Convert the scheduledTime to Asia/Kolkata time zone
        if data.scheduledTime:
            if isinstance(data.scheduledTime, str):
                # Parse string to datetime
                scheduled_time_utc = datetime.strptime(data.scheduledTime, "%Y-%m-%d %H:%M:%S")
            elif isinstance(data.scheduledTime, datetime):
                # Already a datetime object
                scheduled_time_utc = data.scheduledTime
            else:
                raise HTTPException(status_code=400, detail="Invalid format for scheduledTime. Must be a string or datetime.")

            # Convert to Asia/Kolkata timezone
            kolkata_tz = pytz.timezone('Asia/Kolkata')
            scheduled_time_kolkata = scheduled_time_utc.replace(tzinfo=pytz.utc).astimezone(kolkata_tz)
            # Convert to string if needed
            scheduled_time_str = scheduled_time_kolkata.strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise HTTPException(status_code=400, detail="Scheduled time is required.")
            
        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        create = """
            CREATE TABLE IF NOT EXISTS whatsapp_scheduled_messages (
                id SERIAL PRIMARY KEY,
                groups TEXT NOT NULL,
                message_type TEXT NOT NULL,
                message_content TEXT NOT NULL,
                schedule_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                status TEXT DEFAULT 'false',
                media JSON,
                tenant_id VARCHAR(50) NOT NULL,
                CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenant_tenant (tenant_id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            );
                
        """

        # Insert the scheduled message into the database
        query = """
        INSERT INTO whatsapp_scheduled_messages (groups, message_type, message_content, schedule_time, media, tenant_id,status)
        VALUES (%s, %s, %s, %s, %s, %s,%s)
        RETURNING id;
        """
        cursor.execute(
            query,
            (groups, data.messageType, data.content, scheduled_time_str, media_json,tenant_id, "pending"),
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

    
def get_all_scheduled_messages(tenant_id):
    try:
        # Connect to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Fetch all scheduled messages
        query = """
        SELECT id, groups, message_type, message_content, schedule_time, status, media 
        FROM whatsapp_scheduled_messages
        where tenant_id = %s;
        
        """
        cursor.execute(query,(tenant_id,))
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
    

def update_schedule_message(message_id,updated_message,tenant_id):
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
        media_url = str(updated_message.media.url) if updated_message.media and updated_message.media.url else None
        media_type = updated_message.media.type if updated_message.media else None
        media_name = updated_message.media.name if updated_message.media else None

        # Update query
        update_query = """
        UPDATE whatsapp_scheduled_messages
        SET 
            groups = %s,
            message_type = %s,
            message_content = %s,
            media = %s,
            scheduled_time = %s
        WHERE id = %s and tenant_id =%s
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
                tenant_id
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
