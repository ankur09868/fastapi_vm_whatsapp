from fastapi import APIRouter, HTTPException,Request
from modules.model.dashboard import DashboardResponse, SentimentData, EngagementData
from modules.config.database import conn_config
import psycopg2
from datetime import datetime, timedelta
from typing import List

# Define your router
dashboard_router = APIRouter()

@dashboard_router.get("/dashboard", response_model=List[DashboardResponse])
async def get_dashboard(tenant: Request):
    conn = None  # Initialize the connection variable
    try:
        tenant_id = tenant.headers.get("X-tenant-id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id header is missing.")
        
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Fetch all group names
        cursor.execute("SELECT DISTINCT group_name FROM whatsapp_groups WHERE tenant_id = %s;", (tenant_id,))
        group_names = cursor.fetchall()
        if not group_names:
            raise HTTPException(status_code=404, detail="No group names found")

        dashboard_data = []

        for group_name in group_names:
            group_name_str = group_name[0]

            cursor.execute("""
                SELECT 
                    group_name,
                    COALESCE(SUM((sentiment_data->>'Positive')::int), 0) AS Positive,
                    COALESCE(SUM((sentiment_data->>'Neutral')::int), 0) AS Neutral,
                    COALESCE(SUM((sentiment_data->>'Negative')::int), 0) AS Negative,
                    COALESCE(SUM((sentiment_data->>'Commercial')::int), 0) AS Commercial,
                    topic_data::text AS topic, COUNT(*) AS frequency
                FROM 
                    whatsapp_sentiment
                WHERE 
                    group_name = %s AND tenant_id = %s
                GROUP BY 
                    group_name, topic_data::text
                ORDER BY 
                    frequency DESC
                LIMIT 10
            """, (group_name_str, tenant_id))

            data = cursor.fetchall()

            # You can now iterate over `data` and separate sentiment and topics:
            sentiment_data = []
            topics_data = []

            for row in data:
                group_name_str = row[0]
                positive = row[1]
                neutral = row[2]
                negative = row[3]
                commercial = row[4]
                topic = row[5]
                frequency = row[6]

                sentiment_data.append(SentimentData(
                    day=datetime.strftime(datetime.now(), '%A'),  # you can adjust this logic based on how you want to store the day
                    Positive=positive,
                    Neutral=neutral,
                    Negative=negative,
                    Commercial=commercial
                ))

                topics_data.append({"topic": topic, "frequency": frequency})

            # # Fetch sentiment data
            # cursor.execute("""
            #     SELECT group_name, 
            #         COALESCE(SUM((sentiment_data->>'Positive')::int), 0) AS Positive,
            #         COALESCE(SUM((sentiment_data->>'Neutral')::int), 0) AS Neutral,
            #         COALESCE(SUM((sentiment_data->>'Negative')::int), 0) AS Negative,
            #         COALESCE(SUM((sentiment_data->>'Commercial')::int), 0) AS Commercial
            #     FROM whatsapp_sentiment
            #     WHERE group_name = %s AND tenant_id = %s
            # """, (group_name_str, tenant_id))
            # sentiment_data = [
            #     SentimentData(
            #         day=datetime.strftime(message_time, '%A'),
            #         Positive=positive,
            #         Neutral=neutral,
            #         Negative=negative,
            #         Commercial=commercial
            #     )
            #     for message_time, positive, neutral, negative, commercial in cursor.fetchall()
            # ] or None  # Set to None if empty

            # # Fetch topics data
            # cursor.execute("""
            #     SELECT topic_data::text AS topic, COUNT(*) AS frequency
            #     FROM whatsapp_sentiment
            #     WHERE group_name = %s AND tenant_id = %s
            #     GROUP BY topic_data::text
            #     ORDER BY frequency DESC
            #     LIMIT 10
            # """, (group_name_str, tenant_id))
            # topics_data = [{"topic": topic, "frequency": frequency} for topic, frequency in cursor.fetchall()] or None

            # Engagement data calculation
            seven_days_ago = datetime.now() - timedelta(days=7)

            # Active members
            cursor.execute("""
                SELECT DISTINCT phone_number
                FROM whatsapp_messages
                WHERE group_name = %s AND tenant_id = %s AND message_time >= %s
            """, (group_name_str, tenant_id, seven_days_ago))
            active_members_count = len(cursor.fetchall())

            # Total members
            cursor.execute("""
                SELECT COUNT(DISTINCT phone_number)
                FROM whatsapp_group_members
                WHERE group_id = (
                    SELECT group_id FROM whatsapp_groups WHERE group_name = %s AND tenant_id = %s
                )
            """, (group_name_str, tenant_id))
            total_members = cursor.fetchone()[0] or 0

            # Active member score
            active_member_score = (active_members_count / total_members * 100) if total_members > 0 else 0

            # Engagement rate
            cursor.execute("""
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE group_name = %s AND tenant_id = %s AND message_time >= %s
            """, (group_name_str, tenant_id, seven_days_ago))
            total_messages_last_7_days = cursor.fetchone()[0] or 0
            engagement_rate = (active_members_count / total_messages_last_7_days * 100) if total_messages_last_7_days > 0 else 0

            # Response rate
            cursor.execute("""
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE group_name = %s AND tenant_id = %s AND message_time >= %s
            """, (group_name_str, tenant_id, seven_days_ago))
            response_messages = cursor.fetchone()[0] or 0
            response_rate = (response_messages / total_messages_last_7_days * 100) if total_messages_last_7_days > 0 else 0

            engagement_data = [
                {"metric": "Active Members", "score": active_member_score},
                {"metric": "Engagement Rate", "score": engagement_rate},
                {"metric": "Response Rate", "score": response_rate}
            ] or None

            dashboard_data.append(DashboardResponse(
                name=group_name_str,
                sentimentData=sentiment_data,
                engagementData=engagement_data,
                topicsData=topics_data
            ))

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

    finally:
        if conn:
            conn.close()

# # Initialize the router
# dashboard_router = APIRouter()

# @dashboard_router.get("/dashboard", response_model=List[DashboardResponse])
# async def get_dashboard(tenant:Request):
#     try:
#         tenant_id = tenant.headers.get("X-tenant-id")
#         if not tenant_id:
#             raise HTTPException(status_code=400, detail="tenant_id header is missing.")
#         # Connect to the PostgreSQL database
#         conn = psycopg2.connect(**conn_config)
#         cursor = conn.cursor()

#         # Fetch all group names from the database
#         cursor.execute("SELECT DISTINCT group_name FROM whatsapp_messages WHERE tenant_id = %s;",(tenant_id,))
#         group_names = cursor.fetchall()  # Use fetchall() instead of fetchone() to get all groups

#         if not group_names:
#             raise HTTPException(status_code=404, detail="No group names found")

#         # Prepare a list to hold the data for each group
#         dashboard_data = []

#         # Iterate through each group name
#         for group_name in group_names:
#             group_name_str = group_name[0]

#             # Fetch sentiment data for the group
#             cursor.execute("""
#                 SELECT message_time, 
#                     COALESCE(SUM((sentiment_data->>'Positive')::int), 0) AS Positive,
#                     COALESCE(SUM((sentiment_data->>'Neutral')::int), 0) AS Neutral,
#                     COALESCE(SUM((sentiment_data->>'Negative')::int), 0) AS Negative,
#                     COALESCE(SUM((sentiment_data->>'Commercial')::int), 0) AS Commercial
#                 FROM whatsapp_messages
#                 WHERE group_name = %s AND tenant_id = %s
#                 GROUP BY message_time
#                 ORDER BY message_time
#             """, (group_name_str,tenant_id,))

#             sentiment_data = [
#                 SentimentData(
#                     day=datetime.strftime(message_time, '%A'),  # Convert the datetime object to the full day name
#                     Positive=positive,
#                     Neutral=neutral,
#                     Negative=negative,
#                     Commercial=commercial
#                 )
#                 for message_time, positive, neutral, negative, commercial in cursor.fetchall()
#             ]

#             # Fetch the last 10 topics data (from the same table)
#             cursor.execute("""
#                 SELECT topic_data::text AS topic, COUNT(*) AS frequency
#                 FROM whatsapp_messages
#                 WHERE group_name = %s AND tenant_id = %s
#                 GROUP BY topic_data::text
#                 ORDER BY frequency DESC
#                 LIMIT 10
#             """, (group_name_str,tenant_id))

#             topics_data = [{"topic": topic, "frequency": frequency} for topic, frequency in cursor.fetchall()]

#             # Engagement Data Calculation
#             seven_days_ago = datetime.now() - timedelta(days=7)
#             cursor.execute("""
#                 SELECT DISTINCT phone_number
#                 FROM whatsapp_messages
#                 WHERE group_name = %s AND tenant_id = %s AND message_time >= %s
#             """, (group_name_str,tenant_id, seven_days_ago))

#             active_members = cursor.fetchall()
#             active_members_count = len(active_members)

#             # Total Members: Assuming there is a "members" table or data to get the total number of group members
#             cursor.execute("""
#                 SELECT COUNT(DISTINCT phone_number)
#                 FROM whatsapp_group_members
#                 WHERE group_id = (SELECT group_id FROM whatsapp_groups WHERE group_name = %s AND tenant_id = %s)
#             """, (group_name_str,tenant_id))
#             total_members = cursor.fetchone()[0]

#             # Active Member Score Calculation
#             if total_members > 0:
#                 active_member_score = (active_members_count / total_members) * 100
#             else:
#                 active_member_score = 0

#             # Engagement Rate: Assuming it's the ratio of active messages to total messages in the last 7 days
#             cursor.execute("""
#                 SELECT COUNT(*)
#                 FROM whatsapp_messages
#                 WHERE group_name = %s AND tenant_id = %s AND message_time >= %s
#             """, (group_name_str,tenant_id, seven_days_ago))
#             total_messages_last_7_days = cursor.fetchone()[0]

#             if total_messages_last_7_days > 0:
#                 engagement_rate = (active_members_count / total_messages_last_7_days) * 100
#             else:
#                 engagement_rate = 0


#             cursor.execute("""
#                 SELECT COUNT(*)
#                 FROM whatsapp_messages
#                 WHERE group_name = %s  AND tenant_id = %s AND message_time >= %s
#             """, (group_name_str,tenant_id, seven_days_ago))
#             response_messages = cursor.fetchone()[0]

#             if total_messages_last_7_days > 0:
#                 response_rate = (response_messages / total_messages_last_7_days) * 100
#             else:
#                 response_rate = 0

#             # Create engagement data
#             engagement_data = [
#                 {"metric": "Active Members", "score": active_member_score},
#                 {"metric": "Engagement Rate", "score": engagement_rate},
#                 {"metric": "Response Rate", "score": response_rate}
#             ]

#             # Append the group data to the response list
#             dashboard_data.append(DashboardResponse(
#                 name=group_name_str,
#                 sentimentData=sentiment_data,
#                 engagementData=engagement_data, 
#                 topicsData=topics_data
#             ))

#         return dashboard_data

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         if conn:
#             cursor.close()
#             conn.close()
