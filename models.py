import json
import pandas as pd
import sqlite3
from database import get_db_connection
from datetime import datetime
from auth import hash_password

class User:
    @staticmethod
    def create(username, password_hash, role, email=None, full_name=None, department=None, create_task=False, created_by=None):
        """Create a new user or a task for user creation"""
        if create_task:
            # Create a task for user creation
            data = {
                'username': username,
                'password_hash': password_hash,
                'role': role,
                'email': email,
                'full_name': full_name,
                'department': department
            }
            
            Task.create('create', 'user', None, data, created_by)
            return True
        else:
            # Create the user directly
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, email, full_name, department, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, role, email, full_name, department, created_by)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()
    
    @staticmethod
    def update(user_id, data, create_task=False, created_by=None):
        """Update a user or create a task for user update"""
        if create_task:
            # Create a task for user update
            Task.create('update', 'user', user_id, data, created_by)
            return True
        else:
            # Update the user directly
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create SET part of the SQL dynamically
            set_clauses = []
            values = []
            
            for key, value in data.items():
                if key not in ['id', 'created_at']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add user_id as the last parameter
            values.append(user_id)
            
            try:
                cursor.execute(
                    f"""
                    UPDATE users
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                    """,
                    values
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    @staticmethod
    def delete(user_id, create_task=False, created_by=None):
        """Delete a user or create a task for user deletion"""
        if create_task:
            # Create a task for user deletion
            Task.create('delete', 'user', user_id, {}, created_by)
            return True
        else:
            # Delete the user directly
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    @staticmethod
    def get(user_id):
        """Get a user by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, username, role, email, full_name, department, created_by, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None


class ReferenceData:
    @staticmethod
    def create(data_type, code, value, description=None, create_task=False, created_by=None):
        """Create a new reference data entry or a task for creation"""
        if create_task:
            # Create a task for reference data creation
            data = {
                'data_type': data_type,
                'code': code,
                'value': value,
                'description': description
            }
            
            Task.create('create', 'reference_data', None, data, created_by)
            return True
        else:
            # Create the reference data directly
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    """
                    INSERT INTO reference_data (data_type, code, value, description, created_by)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (data_type, code, value, description, created_by)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
            finally:
                conn.close()
    
    @staticmethod
    def update(ref_id, data, create_task=False, created_by=None):
        """Update a reference data entry or create a task for update"""
        if create_task:
            # Create a task for reference data update
            Task.create('update', 'reference_data', ref_id, data, created_by)
            return True
        else:
            # Update the reference data directly
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create SET part of the SQL dynamically
            set_clauses = []
            values = []
            
            for key, value in data.items():
                if key not in ['id', 'created_at', 'created_by']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add ref_id as the last parameter
            values.append(ref_id)
            
            try:
                cursor.execute(
                    f"""
                    UPDATE reference_data
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                    """,
                    values
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    @staticmethod
    def delete(ref_id, create_task=False, created_by=None):
        """Delete a reference data entry or create a task for deletion"""
        if create_task:
            # Create a task for reference data deletion
            Task.create('delete', 'reference_data', ref_id, {}, created_by)
            return True
        else:
            # Delete the reference data directly
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("DELETE FROM reference_data WHERE id = ?", (ref_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
    
    @staticmethod
    def get(ref_id):
        """Get a reference data entry by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT *
            FROM reference_data
            WHERE id = ?
            """,
            (ref_id,)
        )
        
        ref_data = cursor.fetchone()
        conn.close()
        
        if ref_data:
            return dict(ref_data)
        return None


class Task:
    @staticmethod
    def create(task_type, entity_type, entity_id, data, created_by):
        """Create a new task"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO tasks (task_type, entity_type, entity_id, data_json, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_type, entity_type, entity_id, json.dumps(data), created_by)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    @staticmethod
    def approve(task_id, approved_by):
        """Approve a task and execute the related action using direct SQL operations"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get the task details
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            
            if not task:
                print(f"Task approval failed: Task {task_id} not found")
                return False
            
            task_dict = dict(task)
            data = json.loads(task_dict['data_json'])
            
            print(f"Approving task: {task_id}, Type: {task_dict['task_type']}, Entity: {task_dict['entity_type']}")
            
            # Process based on task type and entity type
            success = False
            
            # User creation
            if task_dict['task_type'] == 'create' and task_dict['entity_type'] == 'user':
                try:
                    # Hash the password if it's not already hashed
                    password_hash = data.get('password_hash')
                    if not password_hash and 'password' in data:
                        password_hash = hash_password(data['password'])
                    
                    # Insert directly into users table
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role, email, full_name, department, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            data['username'],
                            password_hash,
                            data['role'],
                            data.get('email'),
                            data.get('full_name'),
                            data.get('department'),
                            task_dict['created_by']
                        )
                    )
                    success = True
                except sqlite3.IntegrityError:
                    print(f"User creation failed: Username {data.get('username')} already exists")
                    success = False
            
            # Reference data creation
            elif task_dict['task_type'] == 'create' and task_dict['entity_type'] == 'reference_data':
                try:
                    cursor.execute(
                        """
                        INSERT INTO reference_data (data_type, code, value, description, created_by)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            data['data_type'],
                            data['code'],
                            data['value'],
                            data.get('description'),
                            task_dict['created_by']
                        )
                    )
                    success = True
                except sqlite3.IntegrityError:
                    print(f"Reference data creation failed: {data.get('data_type')}-{data.get('code')} already exists")
                    success = False
            
            # User update
            elif task_dict['task_type'] == 'update' and task_dict['entity_type'] == 'user':
                # Build SET clause and values dynamically
                set_clauses = []
                values = []
                
                for key, value in data.items():
                    if key not in ['id', 'username', 'created_at', 'created_by']:  # Skip immutable fields
                        if key == 'password':
                            set_clauses.append("password_hash = ?")
                            values.append(hash_password(value))
                        elif key != 'password_hash':  # Skip password_hash if present, we've handled password
                            set_clauses.append(f"{key} = ?")
                            values.append(value)
                
                if set_clauses:
                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    values.append(task_dict['entity_id'])
                    
                    # Execute update
                    cursor.execute(
                        f"""
                        UPDATE users
                        SET {', '.join(set_clauses)}
                        WHERE id = ?
                        """,
                        values
                    )
                    success = cursor.rowcount > 0
                else:
                    success = True  # No changes to make
            
            # Reference data update
            elif task_dict['task_type'] == 'update' and task_dict['entity_type'] == 'reference_data':
                # Build SET clause and values dynamically
                set_clauses = []
                values = []
                
                for key, value in data.items():
                    if key not in ['id', 'created_at', 'created_by']:  # Skip immutable fields
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if set_clauses:
                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    values.append(task_dict['entity_id'])
                    
                    # Execute update
                    cursor.execute(
                        f"""
                        UPDATE reference_data
                        SET {', '.join(set_clauses)}
                        WHERE id = ?
                        """,
                        values
                    )
                    success = cursor.rowcount > 0
                else:
                    success = True  # No changes to make
            
            # User deletion
            elif task_dict['task_type'] == 'delete' and task_dict['entity_type'] == 'user':
                cursor.execute("DELETE FROM users WHERE id = ?", (task_dict['entity_id'],))
                success = cursor.rowcount > 0
            
            # Reference data deletion
            elif task_dict['task_type'] == 'delete' and task_dict['entity_type'] == 'reference_data':
                cursor.execute("DELETE FROM reference_data WHERE id = ?", (task_dict['entity_id'],))
                success = cursor.rowcount > 0
            
            # Bulk upload for users
            elif task_dict['task_type'] == 'bulk_upload' and task_dict['entity_type'] == 'user':
                # Process each record in the bulk upload
                success = True  # Assume success until a failure occurs
                
                if 'records' in data and isinstance(data['records'], list):
                    for record in data['records']:
                        try:
                            # Hash the password if it's not already hashed
                            password_hash = record.get('password_hash')
                            if not password_hash and 'password' in record:
                                password_hash = hash_password(record['password'])
                            
                            # Insert user record
                            cursor.execute(
                                """
                                INSERT INTO users (username, password_hash, role, email, full_name, department, created_by)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    record['username'],
                                    password_hash,
                                    record['role'],
                                    record.get('email'),
                                    record.get('full_name'),
                                    record.get('department'),
                                    task_dict['created_by']
                                )
                            )
                        except sqlite3.IntegrityError:
                            print(f"User creation failed during bulk upload: Username {record.get('username')} already exists")
                            # Continue with other records rather than failing the entire task
                else:
                    print("Bulk upload failed: No records found in data")
                    success = False
            
            # Bulk upload for reference data
            elif task_dict['task_type'] == 'bulk_upload' and task_dict['entity_type'] == 'reference_data':
                # Process each record in the bulk upload
                success = True  # Assume success until a failure occurs
                
                if 'records' in data and isinstance(data['records'], list):
                    for record in data['records']:
                        try:
                            cursor.execute(
                                """
                                INSERT INTO reference_data (data_type, code, value, description, created_by)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    record['data_type'],
                                    record['code'],
                                    record['value'],
                                    record.get('description'),
                                    task_dict['created_by']
                                )
                            )
                        except sqlite3.IntegrityError:
                            print(f"Reference data creation failed during bulk upload: {record.get('data_type')}-{record.get('code')} already exists")
                            # Continue with other records rather than failing the entire task
                else:
                    print("Bulk upload failed: No records found in data")
                    success = False
            
            # Update task status
            if success:
                print(f"Task completed successfully, updating status to approved")
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (approved_by, task_id)
                )
                conn.commit()
                return True
            else:
                print(f"Task failed, updating status to failed")
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = 'failed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (task_id,)
                )
                conn.commit()
                return False
                
        except Exception as e:
            print(f"Error in task approval: {str(e)}")
            conn.rollback()
            
            # Update task status to failed
            try:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET status = 'failed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (task_id,)
                )
                conn.commit()
            except Exception as update_err:
                print(f"Error updating task status: {str(update_err)}")
            
            return False
        finally:
            conn.close()
    
    @staticmethod
    def reject(task_id, rejected_by):
        """Reject a task"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Make sure task exists and is pending
            cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
            task = cursor.fetchone()
            
            if not task:
                print(f"Task rejection failed: Task {task_id} not found")
                return False
                
            if task['status'] != 'pending':
                print(f"Task rejection failed: Task {task_id} is not in pending status")
                return False
                
            # Update task status to rejected
            cursor.execute(
                """
                UPDATE tasks
                SET status = 'rejected', approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (rejected_by, task_id)
            )
            conn.commit()
            print(f"Task {task_id} rejected successfully")
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error in task rejection: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get(task_id):
        """Get a task by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        conn.close()
        
        if task:
            task_dict = dict(task)
            task_dict['data'] = json.loads(task_dict['data_json'])
            return task_dict
        return None
