import sqlite3
import os
import pandas as pd

DB_PATH = 'data_governance.db'

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initialize the database with required tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we need to perform migration for the users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # If users table doesn't exist, create it
    if not columns:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            department TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    # If users table exists but doesn't have created_by column, add it
    elif 'created_by' not in columns:
        print("Migrating users table: Adding created_by column")
        cursor.execute('ALTER TABLE users ADD COLUMN created_by TEXT')
        
    # Create users table (this is now a safe operation as SQLite will ignore it if exists)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        full_name TEXT,
        department TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create reference_data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reference_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_type TEXT NOT NULL,
        code TEXT NOT NULL,
        value TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'active',
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(data_type, code)
    )
    ''')
    
    # Create tasks table for approval workflow
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        data_json TEXT,
        status TEXT DEFAULT 'pending',
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_by TEXT,
        approved_at TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_users():
    """Get all users from the database"""
    conn = get_db_connection()
    users = pd.read_sql_query("SELECT id, username, role, email, full_name, department, created_by, created_at FROM users", conn)
    conn.close()
    return users

def get_reference_data(data_type=None):
    """Get reference data, optionally filtered by data_type"""
    conn = get_db_connection()
    if data_type:
        reference_data = pd.read_sql_query(
            "SELECT * FROM reference_data WHERE data_type = ?", 
            conn, 
            params=[data_type]
        )
    else:
        reference_data = pd.read_sql_query("SELECT * FROM reference_data", conn)
    conn.close()
    return reference_data

def get_tasks(status=None):
    """Get tasks, optionally filtered by status"""
    conn = get_db_connection()
    if status:
        tasks = pd.read_sql_query(
            "SELECT * FROM tasks WHERE status = ?", 
            conn, 
            params=[status]
        )
    else:
        tasks = pd.read_sql_query("SELECT * FROM tasks", conn)
    conn.close()
    return tasks
