from fastapi import APIRouter, HTTPException
from modules.model.dashboard import DashboardResponse, SentimentData, EngagementData
from modules.config.database import conn_config
import psycopg2
from datetime import datetime, timedelta
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
                    COALESCE(SUM((sentiment_data->>'Positive')::int), 0) AS Positive,
                    COALESCE(SUM((sentiment_data->>'Neutral')::int), 0) AS Neutral,
                    COALESCE(SUM((sentiment_data->>'Negative')::int), 0) AS Negative,
                    COALESCE(SUM((sentiment_data->>'Commercial')::int), 0) AS Commercial
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

            # Engagement Data Calculation
            seven_days_ago = datetime.now() - timedelta(days=7)
            cursor.execute("""
                SELECT DISTINCT phone_number
                FROM whatsapp_messages
                WHERE group_name = %s AND message_time >= %s
            """, (group_name_str, seven_days_ago))

            active_members = cursor.fetchall()
            active_members_count = len(active_members)

            # Total Members: Assuming there is a "members" table or data to get the total number of group members
            cursor.execute("""
                SELECT COUNT(DISTINCT phone_number)
                FROM whatsapp_group_members
                WHERE group_id = (SELECT group_id FROM whatsapp_groups WHERE group_name = %s)
            """, (group_name_str,))
            total_members = cursor.fetchone()[0]

            # Active Member Score Calculation
            if total_members > 0:
                active_member_score = (active_members_count / total_members) * 100
            else:
                active_member_score = 0

            # Engagement Rate: Assuming it's the ratio of active messages to total messages in the last 7 days
            cursor.execute("""
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE group_name = %s AND message_time >= %s
            """, (group_name_str, seven_days_ago))
            total_messages_last_7_days = cursor.fetchone()[0]

            if total_messages_last_7_days > 0:
                engagement_rate = (active_members_count / total_messages_last_7_days) * 100
            else:
                engagement_rate = 0


            cursor.execute("""
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE group_name = %s  AND message_time >= %s
            """, (group_name_str, seven_days_ago))
            response_messages = cursor.fetchone()[0]

            if total_messages_last_7_days > 0:
                response_rate = (response_messages / total_messages_last_7_days) * 100
            else:
                response_rate = 0

            # Create engagement data
            engagement_data = [
                {"metric": "Active Members", "score": active_member_score},
                {"metric": "Engagement Rate", "score": engagement_rate},
                {"metric": "Response Rate", "score": response_rate}
            ]

            # Append the group data to the response list
            dashboard_data.append(DashboardResponse(
                name=group_name_str,
                sentimentData=sentiment_data,
                engagementData=engagement_data, 
                topicsData=topics_data
            ))

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()
