import psycopg2
from modules.config.database import conn_config
from fastapi import HTTPException
# Function to insert new bot configuration (word and reply) into the database
def connection():
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()
    except:
        pass

def store_bot_config(word: str, reply_message: str):
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Query to insert the word and reply_message into the whatsapp_botconfig table
        cursor.execute(
            "INSERT INTO whatsapp_botconfig (word, reply_message) VALUES (%s, %s)",
            (word, reply_message)
        )

        # Commit the transaction
        conn.commit()

        # Close the database connection
        conn.close()
        return {"message": "Bot configuration saved successfully."}
    except Exception as e:
        print(f"Error saving bot configuration to database: {e}")
        raise HTTPException(status_code=500, detail="Error saving bot configuration.")
    
def fetch_bot_config_from_db():
    try:
        pass
    except:
        pass