from fastapi import APIRouter, HTTPException
from modules.model.dashboard import DashboardResponse, SentimentData
from modules.config.database import conn_config
import psycopg2
from datetime import datetime
from typing import List

# Initialize the router
dashboard_router = APIRouter()

@dashboard_router.get("/dashboard", response_model=List[DashboardResponse])
async def get_dashboard():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Fetch all group names from the database
        cursor.execute("SELECT DISTINCT group_name FROM whatsapp_messages;")
        group_names = cursor.fetchall()  # Use fetchall() instead of fetchone() to get all groups

        if not group_names:
            raise HTTPException(status_code=404, detail="No group names found")

        # Prepare a list to hold the data for each group
        dashboard_data = []

        # Iterate through each group name
        for group_name in group_names:
            group_name_str = group_name[0]

            # Fetch sentiment data for the group
            cursor.execute("""
                SELECT message_time, 
                    SUM(CASE WHEN sentiment_data->>'sentiment' = 'Positive' THEN 1 ELSE 0 END) AS Positive,
                    SUM(CASE WHEN sentiment_data->>'sentiment' = 'Neutral' THEN 1 ELSE 0 END) AS Neutral,
                    SUM(CASE WHEN sentiment_data->>'sentiment' = 'Negative' THEN 1 ELSE 0 END) AS Negative,
                    SUM(CASE WHEN sentiment_data->>'sentiment' = 'Commercial' THEN 1 ELSE 0 END) AS Commercial
                FROM whatsapp_messages
                WHERE group_name = %s
                GROUP BY message_time
                ORDER BY message_time
            """, (group_name_str,))

            sentiment_data = [
                SentimentData(
                    day=datetime.strftime(message_time, '%A'),  # Convert the datetime object to the full day name
                    Positive=positive,
                    Neutral=neutral,
                    Negative=negative,
                    Commercial=commercial
                )
                for message_time, positive, neutral, negative, commercial in cursor.fetchall()
            ]

            # Fetch the last 10 topics data (from the same table)
            cursor.execute("""
                SELECT topic_data, COUNT(*) AS frequency
                FROM whatsapp_messages
                WHERE group_name = %s
                GROUP BY topic_data
                ORDER BY frequency DESC
                LIMIT 10
            """, (group_name_str,))

            topics_data = [{"topic": topic, "frequency": frequency} for topic, frequency in cursor.fetchall()]

            # Append the group data to the response list
            dashboard_data.append(DashboardResponse(
                name=group_name_str,  # Group name retrieved from the DB
                sentimentData=sentiment_data,
                topicsData=topics_data
            ))

        # Return the entire dashboard data as a list of DashboardResponse
        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()
