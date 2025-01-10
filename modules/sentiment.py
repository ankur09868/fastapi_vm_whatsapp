from fastapi import FastAPI, HTTPException
import psycopg2
import logging
import json
from openai import OpenAI
from modules.config.database import conn_config

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Sentiment analysis function
def analyze_topic_and_sentiment(messages):
    prompt = f"""
    Analyze the following messages collectively for sentiment and topics. Ensure to provide a structured JSON response as follows:
    {{
        "sentiment_data": {{"Positive": int, "Neutral": int, "Negative": int, "Commercial": int}},
        "topic_data": [{{"topic": "string", "frequency": int}}, ...]
    }}
    Provide aggregated sentiment data and at least 6 important topics with their frequencies across all messages. The topics should be the most relevant ones based on the messages.
    Messages: {json.dumps(messages)}
    """
    print("Messages Batch Prompt:", prompt)
    return call_gpt_api(prompt)

# Unified function to call the GPT API
def call_gpt_api(prompt):
    """
    A unified function to call the GPT API with the provided prompt.
    Returns the parsed response.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Use a suitable GPT model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )

        raw_response_content = response.choices[0].message.content.strip()
        print("GPT Response:", raw_response_content)
        return json.loads(raw_response_content)

    except Exception as e:
        logging.error(f"Error during GPT API call: {e}")
        return None
    
from collections import defaultdict

from datetime import datetime,timedelta
def get_groups_message():
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Get today's date and calculate the previous day
        today = datetime.now()
        previous_day = today - timedelta(days=1)
        previous_day_str = previous_day.strftime("%Y-%m-%d 00:00:00")  # Start of the previous day

        # Fetch messages from the previous day
        cursor.execute("""
            SELECT group_name, message_time, message, phone_number, sender, tenant_id
            FROM whatsapp_messages
            WHERE message_time >= %s AND message_time < %s
        """, (previous_day_str, today.strftime("%Y-%m-%d 00:00:00")))
        rows = cursor.fetchall()

        # Log the rows returned from the database
        print("Fetched Rows:", rows)  # Log to see if we're getting data

        # If no rows are returned, return an empty dictionary
        if not rows:
            return {}

        # Organize messages by group (group_name, tenant_id as the key)
        grouped_messages = {}
        for row in rows:
            group_name = row[0]
            message = row[2]
            tenant_id = row[5]  # Make sure tenant_id is at index 5 (as it's in the SELECT query)

            # Use (group_name, tenant_id) as the key for grouped_messages
            if (group_name, tenant_id) not in grouped_messages:
                grouped_messages[(group_name, tenant_id)] = []  # Initialize list for each (group_name, tenant_id) pair
            
            grouped_messages[(group_name, tenant_id)].append(message)

        # Log the grouped messages to confirm the structure
        print("Grouped Messages:", grouped_messages)  # Check the structure of the data

        return grouped_messages  # Ensure we're returning a dictionary of (group_name, tenant_id) -> messages

    except Exception as e:
        logging.error(f"Error fetching messages: {e}")
        return {}  # Return an empty dictionary if there's an error

    finally:
        cursor.close()
        conn.close()
    
# Function to insert sentiment and topic data into the database
def save_sentiment_data(group_name, sentiment_data, topic_data, time,tenant_id):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Prepare SQL query to insert the data
        cursor.execute("""
            INSERT INTO whatsapp_sentiment (group_name,created_at, sentiment_data, topic_data,tenant_id)
            VALUES (%s, %s, %s, %s,%s)
        """, (group_name, time, json.dumps(sentiment_data), json.dumps(topic_data),tenant_id))
        
        conn.commit()

    except Exception as e:
        logging.error(f"Error saving sentiment data: {e}")
    finally:
        cursor.close()
        conn.close()
    