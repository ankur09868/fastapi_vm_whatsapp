import psycopg2
from modules.config.database import conn_config
from fastapi import HTTPException
from modules.model.bot_config import BotConfig,BotLog,BotConfigResponse
import json

def store_bot_config(bot:BotConfig,tenant_id):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        is_bot_enabled = bot.isBotEnabled if bot.isBotEnabled is not None else True  # Default to True if not provided
        spam_keywords = json.dumps(bot.spamKeywords) if bot.spamKeywords else ['spam'] # Convert list to JSON or None
        message_limit = bot.messageLimit if bot.messageLimit is not None else 5  # Handle None for integer
        reply_message = bot.replyMessage if bot.replyMessage else None  # Handle None for string
        spam_action = bot.spamAction if bot.spamAction else None  # Handle None for string
        ai_detection = bot.aidetection if bot.aidetection is not None else False
        ai_reply = bot.aireply if bot.aireply is not None else False
        prompt = bot.prompt if bot.prompt else ""
        tenant_id = tenant_id

        logs = bot.logs if bot.logs else []

        # Log the values being inserted
        print(f"Inserting bot data: {bot.name}, {is_bot_enabled}, {spam_keywords}, {message_limit}, {reply_message}, {spam_action},{ai_detection},{ai_reply},{prompt},{tenant_id}")

        # Insert bot data into the database
        insert_query = """
        INSERT INTO whatsapp_botconfig (name, isbotenabled, spamkeywords, messagelimit, replymessage, spamaction,ai_detection,ai_reply,prompt,tenant_id)
        VALUES (%s, %s, %s, %s, %s, %s,%s,%s,%s,%s)
        """
        cursor.execute(
            insert_query,
            (
                bot.name,
                is_bot_enabled,  
                spam_keywords,   # Either JSON or None
                message_limit,   # Either integer or None
                reply_message,   # Either string or None
                spam_action,      # Either string or None
                ai_detection,
                ai_reply,
                prompt,
                tenant_id
                
            ),
        )
        conn.commit()  # Commit the transaction

        # Return success response
        return {"message": f"Bot {bot.name} added successfully"}

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
def fetch_bot_config_from_db(tenant_id):
    try:
        # Connect to the PostgreSQL database
        with psycopg2.connect(**conn_config) as conn:
            with conn.cursor() as cursor:
                # Fetch all bot configurations
                cursor.execute("""
                    SELECT *
                    FROM whatsapp_botconfig
                    WHERE tenant_id = %s;
                """,(tenant_id,))
                bot_configs = cursor.fetchall()
                print(f"Fetched bot configurations: {bot_configs}")

                if not bot_configs:
                    raise HTTPException(status_code=404, detail="No bot configurations found")

                # Fetch logs for all bots in a single query
                cursor.execute("""
                    SELECT 
                        bot_id, 
                        id, 
                        message, 
                        action, 
                        phone_or_name, 
                        group_name, 
                        timestamp::timestamp(0) AS timestamp
                    FROM 
                        whatsapp_bot_logs
                    WHERE 
                        tenant_id = %s;
                """,(tenant_id,))
                logs = cursor.fetchall()
                print(f"Fetched all logs: {logs}")

        # Group logs by bot_id for faster processing
        logs_by_bot = {}
        for log in logs:
            bot_id, log_id, message, action, phone_or_name, group_name, timestamp = log
            if bot_id not in logs_by_bot:
                logs_by_bot[bot_id] = []
            logs_by_bot[bot_id].append(
                BotLog(
                    id=log_id,
                    message=message,
                    action=action,
                    phone_or_name=phone_or_name or None,  # Use None if phone_or_name is empty or NULL
                    group_name=group_name or None,  # Ensure group_name is None if missing
                    time=timestamp or None  # Ensure timestamp is None if missing
                )
            )

        # Prepare BotConfig objects
        bots = []
        for bot in bot_configs:
            # Adjust unpacking to match the actual columns returned
            bot_id, name, is_bot_enabled, spam_keywords, message_limit, reply_message, spam_action, ai_detection, ai_reply, prompt = bot
            print(f"Processing bot with id={bot_id}, name={name}")

            # Parse spam_keywords
            if spam_keywords is None:
                spam_keywords = []
            elif isinstance(spam_keywords, str):
                try:
                    spam_keywords = json.loads(spam_keywords) if spam_keywords else []
                except json.JSONDecodeError:
                    print(f"Error parsing spamKeywords for bot {bot_id}, defaulting to empty list.")
                    spam_keywords = []

            print(f"spam_keywords for bot {bot_id}: {spam_keywords}")

            # Get logs for this bot
            bot_logs = logs_by_bot.get(bot_id, [])
            print(f"Logs for bot {bot_id}: {bot_logs}")

            # Add bot configuration to the list
            bots.append(
                BotConfig(
                    id=bot_id,
                    name=name,
                    isBotEnabled=is_bot_enabled,
                    logs=bot_logs,
                    spamKeywords=spam_keywords,
                    messageLimit=message_limit,
                    replyMessage=reply_message,
                    spamAction=spam_action,
                    aidetection=ai_detection,
                    aireply=ai_reply,
                    prompt=prompt
                )
            )

        # Return the response with the bot configurations and their logs
        return BotConfigResponse(bots=bots)

    except psycopg2.DatabaseError as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



    finally:
        # Ensure proper cleanup
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_bot_config(bot_id,tenant_id):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Check if the bot exists
        cursor.execute("SELECT id FROM whatsapp_botconfig WHERE id = %s AND tenant_id = %s;", (bot_id,tenant_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found")

        # Delete the bot configuration
        cursor.execute("DELETE FROM whatsapp_botconfig WHERE id = %s AND tenant_id = %s;", (bot_id,tenant_id))
        conn.commit()

        return {"message": f"Bot with ID {bot_id} and its logs deleted successfully"}

    except Exception as e:
        print(f"Error occurred while deleting bot config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_bots(tenant_id):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

       # Fetch all bot configurations
        cursor.execute("""
            SELECT *
            FROM whatsapp_botconfig
            WHERE tenant_id = %s;
        """,(tenant_id,))
        bot_configs = cursor.fetchall()
        print(f"Fetched bot configurations: {bot_configs}")

        if not bot_configs:
            raise HTTPException(status_code=404, detail="No bot configurations found")

        # Prepare a list to hold the bot data
        bots = []

        # Fetch logs for each bot
        for bot in bot_configs:
            bot_id, name, is_bot_enabled, spam_keywords, message_limit, reply_message, spam_action,ai_detection,ai_reply,prompt = bot
            print(f"Processing bot with id={bot_id}, name={name}")
        
           # Add the bot configuration and logs to the list
            bots.append(
                BotConfig(
                    id=bot_id,
                    name=name,
                    isBotEnabled=is_bot_enabled,
                    spamKeywords=spam_keywords,
                    messageLimit=message_limit,
                    replyMessage=reply_message,
                    spamAction=spam_action,
                    aidetection=ai_detection,
                    aireply=ai_reply,
                    prompt=prompt
                )
            )

        # Return the list of bots
        return {"bots": bots}

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        # Ensure proper cleanup
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def update_bot_config(bot_id,bot,tenant_id):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Check if the bot exists
        cursor.execute("SELECT id FROM whatsapp_botconfig WHERE id = %s AND tenant_id;", (bot_id,tenant_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Bot with ID {bot_id} not found")

        # Prepare the update query
        update_query = """
        UPDATE whatsapp_botconfig
        SET name = COALESCE(%s, name),
            isbotenabled = COALESCE(%s, isbotenabled),
            spamkeywords = COALESCE(%s, spamkeywords),
            messagelimit = COALESCE(%s, messagelimit),
            replymessage = COALESCE(%s, replymessage),
            spamaction = COALESCE(%s, spamaction)
        WHERE id = %s AND tenant_id = %s
        """
        cursor.execute(
            update_query,
            (
                bot.name,
                bot.isBotEnabled,
                json.dumps(bot.spamKeywords) if bot.spamKeywords else None,
                bot.messageLimit,
                bot.replyMessage,
                bot.spamAction,
                bot_id,
                tenant_id,
            ),
        )
        conn.commit()

        return {"message": f"Bot with ID {bot_id} updated successfully"}

    except Exception as e:
        print(f"Error occurred while updating bot config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
   