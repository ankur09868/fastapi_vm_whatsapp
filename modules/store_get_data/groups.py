import psycopg2
from modules.config.database import conn_config
from fastapi import HTTPException
from typing import Optional, List, Dict

# New function to get group details by ID
def get_group_details_by_id(group_id: int) -> Optional[Dict]:
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Fetch group details along with member details
        cursor.execute("""
            SELECT 
                g.id, g.group_name, g.group_description,
                m.id AS member_id, m.name, m.phone_number, m.role, m.status, m.rating, m.avatar
            FROM whatsapp_groups g
            LEFT JOIN whatsapp_group_members m ON g.id = m.group_id
            WHERE g.id = %s
        """, (group_id,))

        rows = cursor.fetchall()

        if rows:
            # Initialize group dictionary
            group_details = {
                "group_name": rows[0][1],  # group_name from the first row
                "group_description": rows[0][2],  # group_description from the first row
                "members": []
            }

            # Loop through the results and structure the members
            for row in rows:
                # Extract member details, check if they are available
                member = {
                    "id": row[3] if row[3] else None,  # member_id
                    "name": row[4] if row[4] else None,
                    "phone_number": row[5] if row[5] else None,
                    "role": row[6] if row[6] else None,
                    "status": row[7] if row[7] else None,
                    "rating": row[8] if row[8] else None,
                    "avatar": row[9] if row[9] else None
                }
                group_details["members"].append(member)

            return group_details
        else:
            return None

    except Exception as e:
        print(f"Error fetching group details from database: {e}")
        return None

    finally:
        if conn:
            cursor.close()
            conn.close()
    
def get_messages_per_day(group_name):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to get messages sent each day
        query = """
            SELECT DATE(message_time) AS message_date, COUNT(*) AS message_count
            FROM whatsapp_messages
            WHERE group_name = %s
            GROUP BY DATE(message_time)
            ORDER BY message_date;
        """
        cursor.execute(query, (group_name,))
        rows = cursor.fetchall()

        messages_per_day = [{"message_date": row[0], "message_count": row[1]} for row in rows]

        conn.close()
        return messages_per_day
    except Exception as e:
        print(f"Error fetching messages per day: {e}")
        return []

def get_total_messages(group_name):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to get the total message count
        query = """
            SELECT COUNT(*) 
            FROM whatsapp_messages
            WHERE group_name = %s;
        """
        cursor.execute(query, (group_name,))
        total_messages = cursor.fetchone()[0]

        conn.close()
        return total_messages
    except Exception as e:
        print(f"Error fetching total messages: {e}")
        return 0

def get_active_members(group_name, days=2):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to find members who posted every day in the past 'days' (default 7)
        query = f"""
            SELECT sender
            FROM whatsapp_messages
            WHERE group_name = %s AND message_time >= (CURRENT_TIMESTAMP + INTERVAL '5 hours 30 minutes') - %s * INTERVAL '1 day'
            GROUP BY sender, DATE(message_time)
            HAVING COUNT(DISTINCT DATE(message_time)) = %s;
        """
        cursor.execute(query, (group_name,days,days))
        active_members = [row[0] for row in cursor.fetchall()]

        conn.close()
        return active_members
    except Exception as e:
        print(f"Error fetching active members: {e}")
        return []

def get_top_member(group_name):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to get the member who sent the most messages
        query = """
            SELECT sender, COUNT(*) AS message_count
            FROM whatsapp_messages
            WHERE group_name = %s
            GROUP BY sender
            ORDER BY message_count DESC
            LIMIT 1;
        """
        cursor.execute(query, (group_name,))
        top_member_row = cursor.fetchone()

        top_member = None
        if top_member_row:
            top_member = {
                "sender": top_member_row[0],
                "message_count": top_member_row[1]
            }

        conn.close()
        return top_member
    except Exception as e:
        print(f"Error fetching top member: {e}")
        return None

def get_group_activity(group_name):
    try:

        # Get messages per day
        messages_per_day = get_messages_per_day(group_name)

        # Get total messages
        total_messages = get_total_messages(group_name)

        # Get active members (who posted at least once every day in the last 7 days)
        active_members = get_active_members(group_name)

        # Get top member (who sent the most messages)
        top_member = get_top_member(group_name)

        # Prepare response
        group_activity = {
            "group_name": group_name,
            "messages_per_day": messages_per_day,
            "total_messages": total_messages,
            "active_members": active_members,
            "top_member": top_member
        }

        return group_activity
    except Exception as e:
        print(f"Error fetching group activity: {e}")
        return None


# Function to fetch member data
def get_members_from_db():
    try:
        # Establishing connection to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Query to get all members and their associated group
        cursor.execute("""
            SELECT m.id, m.name, m.phone_number, m.role, m.status, m.rating, m.avatar, g.group_name
            FROM whatsapp_group_members m
            JOIN whatsapp_groups g ON m.group_id = g.id;
        """)
        
        rows = cursor.fetchall()
        members = []
        
        for row in rows:
            member_id, name, phone_number, role, status, rating, avatar, group_name = row
            
            member = {
                "id": member_id,
                "name": name,
                "phone_number": phone_number,
                "role": role,
                "status": status,
                "rating": rating,
                "avatar": avatar
            }
            members.append(member)

        return members
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    
    finally:
        if conn:
            cursor.close()
            conn.close()

# Function to fetch group and member data
def get_groups_from_db():
    try:
        # Establishing connection to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Query to get all groups and their members
        cursor.execute("""
            SELECT g.id, g.group_name, g.group_description, 
                m.member_id, m.name, m.phone_number, m.role, m.status, m.rating, m.avatar
            FROM whatsapp_groups g
            LEFT JOIN whatsapp_group_members m ON g.id = m.group_id;
        """)
        
        rows = cursor.fetchall()
        groups = {}
        
        for row in rows:
            group_id, group_name, group_description, member_id, member_name, phone_number, role, status, rating, avatar = row
            
            if group_id not in groups:
                groups[group_id] = {
                    "id": group_id,
                    "name": group_name,
                    "description": group_description,
                    "members": []
                }
            
            member = {
                "id": member_id,
                "name": member_name,
                "phone_number": phone_number,
                "role": role,
                "status": status,
                "rating": rating,
                "avatar": avatar
            }
            
            groups[group_id]["members"].append(member)

        return list(groups.values())
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    
    finally:
        if conn:
            cursor.close()
            conn.close()