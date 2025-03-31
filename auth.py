import streamlit as st
import sqlite3
import hashlib
from database import get_db_connection

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_default_users():
    """Create default users if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if super admin exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        # Create super admin
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, email, full_name, department) VALUES (?, ?, ?, ?, ?, ?)",
            ('admin', hash_password('admin123'), 'super_admin', 'admin@example.com', 'Admin User', 'IT')
        )
    
    # Check if data analyst exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'analyst'")
    if cursor.fetchone()[0] == 0:
        # Create data analyst
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, email, full_name, department) VALUES (?, ?, ?, ?, ?, ?)",
            ('analyst', hash_password('analyst123'), 'data_analyst', 'analyst@example.com', 'Data Analyst', 'Business Intelligence')
        )
    
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    """Authenticate a user with username and password"""
    if not username or not password:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user from database
    cursor.execute(
        "SELECT username, password_hash, role FROM users WHERE username = ?", 
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user and user[1] == hash_password(password):
        # Set session variables
        st.session_state.authenticated = True
        st.session_state.username = user[0]
        st.session_state.role = user[2]
        return True
    
    return False

def check_authentication():
    """Check if the user is authenticated"""
    return st.session_state.get('authenticated', False)

def check_admin_access():
    """Check if the current user has admin access"""
    if not check_authentication():
        return False
    
    return st.session_state.role == 'super_admin'

def check_analyst_access():
    """Check if the current user has data analyst access"""
    if not check_authentication():
        return False
    
    return st.session_state.role == 'data_analyst' or st.session_state.role == 'super_admin'
