import psycopg2
from modules.config.database import conn_config
from fastapi import HTTPException
from typing import Optional, List, Dict

# New function to get group details by ID
from typing import Optional, Dict, List
import psycopg2

from typing import Optional, Dict
import psycopg2

def get_group_details_by_id(group_id: int, tenant_id: str) -> Optional[Dict]:
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Fetch group details and member details in a single query
        cursor.execute("""
            SELECT 
                g.id AS group_id, 
                g.group_name, 
                g.group_description,
                g.botconfig_id,
                m.member_id,
                m.name AS member_name,
                m.phone_number,
                m.role,
                m.status,
                m.rating,
                m.avatar
            FROM whatsapp_groups g
            LEFT JOIN whatsapp_group_members m ON g.id = m.group_id
            WHERE g.id = %s AND g.tenant_id = %s
        """, (group_id, tenant_id))

        rows = cursor.fetchall()

        # If no rows are returned, the group doesn't exist
        if not rows:
            return None

        # Process the first row for group-level details
        group_details = {
            "group_id": rows[0][0],
            "group_name": rows[0][1],
            "group_description": rows[0][2],
            "botconfig_id": rows[0][3],
            "members": []
        }

        # Process member-level details
        members = [
            {
                "member_id": row[4],
                "name": row[5],
                "phone_number": row[6],
                "role": row[7],
                "status": row[8],
                "rating": row[9],
                "avatar": row[10]
            }
            for row in rows if row[4]  # Only include rows with a valid member_id
        ]

        group_details["members"] = members
        return group_details

    except Exception as e:
        print(f"Error fetching group details from database: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    
def get_messages_per_day(group_name, tenant_id):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to get messages sent each day
        query = """
            SELECT DATE(message_time) AS message_date, COUNT(*) AS message_count
            FROM whatsapp_messages
            WHERE group_name = %s AND tenant_id = %s
            GROUP BY DATE(message_time)
            ORDER BY message_date;
        """
        cursor.execute(query, (group_name, tenant_id))
        rows = cursor.fetchall()

        messages_per_day = [{"message_date": row[0], "message_count": row[1]} for row in rows]

        conn.close()
        return messages_per_day
    except Exception as e:
        print(f"Error fetching messages per day: {e}")
        return []

def get_total_messages(group_name, tenant_id):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to get the total message count
        query = """
            SELECT COUNT(*) 
            FROM whatsapp_messages
            WHERE group_name = %s AND tenant_id = %s;
        """
        cursor.execute(query, (group_name, tenant_id))
        total_messages = cursor.fetchone()[0]

        conn.close()
        return total_messages
    except Exception as e:
        print(f"Error fetching total messages: {e}")
        return 0

def get_active_members(group_name, tenant_id, days=2):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to find members who posted every day in the past 'days'
        query = f"""
            SELECT sender
            FROM whatsapp_messages
            WHERE group_name = %s AND tenant_id = %s AND message_time >= (CURRENT_TIMESTAMP + INTERVAL '5 hours 30 minutes') - %s * INTERVAL '1 day'
            GROUP BY sender, DATE(message_time)
            HAVING COUNT(DISTINCT DATE(message_time)) = %s;
        """
        cursor.execute(query, (group_name, tenant_id, days, days))
        active_members = [row[0] for row in cursor.fetchall()]

        conn.close()
        return active_members
    except Exception as e:
        print(f"Error fetching active members: {e}")
        return []

def get_top_member(group_name, tenant_id):
    try:
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # SQL Query to get the member who sent the most messages
        query = """
            SELECT sender, COUNT(*) AS message_count
            FROM whatsapp_messages
            WHERE group_name = %s AND tenant_id = %s
            GROUP BY sender
            ORDER BY message_count DESC
            LIMIT 1;
        """
        cursor.execute(query, (group_name, tenant_id))
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

def get_group_activity(group_name, tenant_id):
    try:
        # Get messages per day
        messages_per_day = get_messages_per_day(group_name, tenant_id)

        # Get total messages
        total_messages = get_total_messages(group_name, tenant_id)

        # Get active members (who posted at least once every day in the last 'days')
        active_members = get_active_members(group_name, tenant_id)

        # Get top member (who sent the most messages)
        top_member = get_top_member(group_name, tenant_id)

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
def get_members_from_db(tenant_id):
    try:
        # Establishing connection to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Query to get all members and their associated group
        cursor.execute("""
            SELECT m.member_id, m.name, m.phone_number, m.role, m.status, m.rating, m.avatar, g.group_name
            FROM whatsapp_group_members m
            JOIN whatsapp_groups g ON m.group_id = g.id
            WHERE tenant_id = %s;
        """,(tenant_id,))
        
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
def get_groups_from_db(tenant_id):
    try:
        # Establishing connection to the database
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Query to get all groups and their members
        cursor.execute("""
            SELECT g.id, g.group_name, g.group_description, 
                m.member_id, m.name, m.phone_number, m.role, m.status, m.rating, m.avatar
            FROM whatsapp_groups g
            LEFT JOIN whatsapp_group_members m ON g.id = m.group_id
            WHERE g.tenant_id = %s;
        """,(tenant_id,))
        
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
            
            if any(field is not None for field in [member_id, member_name, phone_number, role, status, rating, avatar]):
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


# Function to update the botconfig_id in the database
def update_botconfig_in_db(group_id: int, tenant_id: str, botconfig_id: int):
    conn = None
    cursor = None
    try:
        # Establish a database connection
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Update the botconfig_id for the specified group and tenant
        cursor.execute("""
            UPDATE whatsapp_groups
            SET botconfig_id = %s
            WHERE id = %s AND tenant_id = %s;
        """, (botconfig_id, group_id, tenant_id))

        # Check if any rows were updated
        if cursor.rowcount == 0:
            return {"status": "error", "detail": "Group not found or botconfig_id not updated."}

        # Commit the changes
        conn.commit()
        print(f"Updated botconfig_id for group ID {group_id} and tenant {tenant_id}.")
        return {"status": "success", "message": f"botconfig_id updated successfully for group ID {group_id}"}

    except Exception as e:
        # Rollback on error and return the exception details
        if conn:
            conn.rollback()
        error_message = f"Error updating botconfig_id in DB: {e}"
        print(error_message)
        return {"status": "error", "detail": error_message}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_group(group_name: str, tenant_id: str):
    try:
        # Establish a database connection
        conn = psycopg2.connect(**conn_config)
        cursor = conn.cursor()

        # Delete the group from the database
        cursor.execute("""
            DELETE FROM whatsapp_groups
            WHERE group_name = %s AND tenant_id = %s;
        """, (group_name, tenant_id))

        # Commit the changes
        conn.commit()

        # Check if any rows were deleted
        if cursor.rowcount == 0:
            return None  # No group was deleted

        print(f"Deleted group {group_name} for tenant {tenant_id}.")
        return group_name  # Return the deleted group's name

    except Exception as e:
        print(f"Error deleting group from DB: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed.")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
