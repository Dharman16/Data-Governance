import streamlit as st
import pandas as pd
import io
import json
from database import get_db_connection

def get_user_role():
    """Get the role of the current user"""
    if st.session_state.get('authenticated', False):
        return st.session_state.get('role', None)
    return None

def can_manage_users():
    """Check if the current user can manage users"""
    role = get_user_role()
    return role == 'super_admin'

def can_view_users():
    """Check if the current user can view users"""
    role = get_user_role()
    return role in ['super_admin', 'data_analyst']

def can_manage_reference_data():
    """Check if the current user can manage reference data"""
    role = get_user_role()
    return role in ['super_admin', 'data_analyst']

def can_approve_tasks():
    """Check if the current user can approve tasks"""
    role = get_user_role()
    return role == 'super_admin'

def can_upload_bulk_data():
    """Check if the current user can upload bulk data"""
    role = get_user_role()
    return role in ['super_admin', 'data_analyst']

def get_data_types():
    """Get distinct data types from reference data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT data_type FROM reference_data")
    data_types = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return data_types

def format_task_description(task):
    """Format task description for display"""
    if task['task_type'] == 'create':
        action = 'Create new'
    elif task['task_type'] == 'update':
        action = 'Update'
    elif task['task_type'] == 'delete':
        action = 'Delete'
    else:
        action = task['task_type']
    
    entity = task['entity_type'].replace('_', ' ').title()
    
    if task['entity_id']:
        return f"{action} {entity} (ID: {task['entity_id']})"
    else:
        return f"{action} {entity}"

def parse_excel_upload(uploaded_file, sheet_name=None):
    """Parse an uploaded Excel file"""
    try:
        if sheet_name:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        else:
            df = pd.read_excel(uploaded_file)
        return df, None
    except Exception as e:
        return None, str(e)

def parse_csv_upload(uploaded_file):
    """Parse an uploaded CSV file"""
    try:
        df = pd.read_csv(uploaded_file)
        return df, None
    except Exception as e:
        return None, str(e)

def get_user_stats():
    """Get user statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT role FROM users")
    roles = [row[0] for row in cursor.fetchall()]
    
    role_counts = {}
    for role in roles:
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,))
        role_counts[role] = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_users": user_count,
        "role_counts": role_counts
    }

def get_reference_data_stats():
    """Get reference data statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM reference_data")
    data_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT data_type FROM reference_data")
    data_types = [row[0] for row in cursor.fetchall()]
    
    type_counts = {}
    for data_type in data_types:
        cursor.execute("SELECT COUNT(*) FROM reference_data WHERE data_type = ?", (data_type,))
        type_counts[data_type] = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_entries": data_count,
        "type_counts": type_counts
    }

def get_task_stats():
    """Get task statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tasks")
    task_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'approved'")
    approved_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'rejected'")
    rejected_count = cursor.fetchone()[0]
    
    # Get task types breakdown
    cursor.execute("SELECT task_type, COUNT(*) FROM tasks GROUP BY task_type")
    task_types = {}
    for row in cursor.fetchall():
        task_types[row[0]] = row[1]
    
    # Get recent tasks
    cursor.execute("""
        SELECT id, task_type, entity_type, status, created_by, created_at 
        FROM tasks 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    recent_tasks = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_tasks": task_count,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "task_types": task_types,
        "recent_tasks": recent_tasks
    }
