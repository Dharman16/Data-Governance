import streamlit as st
import pandas as pd
from auth import hash_password, check_authentication, check_admin_access
from database import get_db_connection, get_users
from models import User
from utils import can_manage_users, can_view_users

# Page configuration
st.set_page_config(
    page_title="User Management - Data Governance Platform",
    page_icon="👤",
    layout="wide"
)

# Check authentication
if not check_authentication():
    st.warning("Please login to access this page")
    st.stop()

# Check access rights
if not can_view_users():
    st.error("You do not have permission to view this page")
    st.stop()

# Page header
st.title("User Management")

# Tabs for different actions
tabs = st.tabs(["User List", "Create User", "Edit User"])

with tabs[0]:
    st.header("User List")
    
    # Refresh button
    if st.button("Refresh User List", key="refresh_user_list"):
        st.rerun()
    
    # Get users
    users_df = get_users()
    
    if not users_df.empty:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            role_filter = st.selectbox(
                "Filter by Role",
                options=["All"] + list(users_df["role"].unique()),
                index=0,
                key="role_filter_user_list"
            )
        
        with col2:
            search_term = st.text_input("Search by Username or Email", key="search_user_term")
        
        # Apply filters
        filtered_df = users_df.copy()
        if role_filter != "All":
            filtered_df = filtered_df[filtered_df["role"] == role_filter]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df["username"].str.contains(search_term, case=False) |
                filtered_df["email"].str.contains(search_term, case=False)
            ]
        
        # Display users table
        st.dataframe(
            filtered_df,
            column_config={
                "id": "ID",
                "username": "Username",
                "role": "Role",
                "email": "Email",
                "full_name": "Full Name",
                "department": "Department",
                "created_by": "Created By",
                "created_at": st.column_config.DatetimeColumn("Created At", format="MMM DD, YYYY")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # User actions (only for admin)
        if can_manage_users():
            st.subheader("User Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                user_id_to_edit = st.selectbox(
                    "Select User to Edit",
                    options=users_df["id"].tolist(),
                    format_func=lambda x: f"{users_df[users_df['id'] == x]['username'].iloc[0]} (ID: {x})",
                    key="user_edit_select_list"
                )
                
                if st.button("Edit Selected User", key="edit_selected_user_btn"):
                    # Set session state for edit user tab
                    st.session_state.user_to_edit = user_id_to_edit
                    st.session_state.active_tab = "Edit User"
                    st.rerun()
            
            with col2:
                user_id_to_delete = st.selectbox(
                    "Select User to Delete",
                    options=users_df["id"].tolist(),
                    format_func=lambda x: f"{users_df[users_df['id'] == x]['username'].iloc[0]} (ID: {x})",
                    key="user_delete_select_list"
                )
                
                if st.button("Delete Selected User", type="primary", key="delete_selected_user_btn"):
                    # Confirm deletion
                    if st.session_state.get('confirm_delete', False):
                        # Delete the user or create task
                        success = User.delete(
                            user_id_to_delete, 
                            not check_admin_access(),  # Create task if not admin
                            st.session_state.username
                        )
                        
                        if success:
                            if check_admin_access():
                                st.success("User deleted successfully")
                            else:
                                st.success("User deletion request submitted for approval")
                            st.session_state.confirm_delete = False
                            st.rerun()
                        else:
                            st.error("Failed to delete user")
                    else:
                        st.session_state.confirm_delete = True
                        st.warning(f"Are you sure you want to delete this user? Click 'Delete Selected User' again to confirm.")
    else:
        st.info("No users found in the database")

with tabs[1]:
    st.header("Create User")
    
    # Check if user has permission to create users
    if not can_manage_users():
        st.warning("You don't have permission to create users")
    else:
        # User creation form
        with st.form("create_user_form"):
            username = st.text_input("Username*", help="Unique username for the user", key="create_username")
            password = st.text_input("Password*", type="password", key="create_password")
            confirm_password = st.text_input("Confirm Password*", type="password", key="create_confirm_password")
            
            role = st.selectbox("Role*", options=["super_admin", "data_analyst"], key="create_role")
            
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", key="create_email")
                full_name = st.text_input("Full Name", key="create_full_name")
            
            with col2:
                department = st.text_input("Department", key="create_department")
            
            submit_button = st.form_submit_button("Create User")
            
            if submit_button:
                # Validate inputs
                if not username or not password or not role:
                    st.error("Username, password, and role are required")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Hash password
                    password_hash = hash_password(password)
                    
                    # Create user or task
                    success = User.create(
                        username, 
                        password_hash, 
                        role, 
                        email, 
                        full_name, 
                        department,
                        not check_admin_access(),  # Create task if not admin
                        st.session_state.username
                    )
                    
                    if success:
                        if check_admin_access():
                            st.success(f"User '{username}' created successfully")
                        else:
                            st.success(f"User creation request submitted for approval")
                    else:
                        st.error(f"Failed to create user. Username may already exist.")

with tabs[2]:
    st.header("Edit User")
    
    # Check if user has permission to edit users
    if not can_manage_users():
        st.warning("You don't have permission to edit users")
    else:
        # Get user to edit from session state or select
        user_to_edit = st.session_state.get("user_to_edit", None)
        
        if not user_to_edit:
            users_df = get_users()
            if not users_df.empty:
                user_to_edit = st.selectbox(
                    "Select User to Edit",
                    options=users_df["id"].tolist(),
                    format_func=lambda x: f"{users_df[users_df['id'] == x]['username'].iloc[0]} (ID: {x})",
                    key="user_edit_tab_select"
                )
        
        if user_to_edit:
            # Get user details
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, role, email, full_name, department, created_by FROM users WHERE id = ?", 
                (user_to_edit,)
            )
            user = cursor.fetchone()
            conn.close()
            
            if user:
                user_dict = dict(user)
                
                # User edit form
                with st.form("edit_user_form"):
                    st.write(f"Editing User: {user_dict['username']}")
                    if user_dict.get('created_by'):
                        st.info(f"This user was created by: {user_dict['created_by']}")
                    
                    # Cannot edit username
                    new_role = st.selectbox("Role*", options=["super_admin", "data_analyst"], index=0 if user_dict['role'] == "super_admin" else 1, key="edit_role")
                    
                    # Option to change password
                    change_password = st.checkbox("Change Password", key="edit_change_password")
                    
                    new_password = ""
                    confirm_password = ""
                    if change_password:
                        new_password = st.text_input("New Password", type="password", key="edit_new_password")
                        confirm_password = st.text_input("Confirm New Password", type="password", key="edit_confirm_password")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        new_email = st.text_input("Email", value=user_dict.get('email', ''), key="edit_email")
                        new_full_name = st.text_input("Full Name", value=user_dict.get('full_name', ''), key="edit_full_name")
                    
                    with col2:
                        new_department = st.text_input("Department", value=user_dict.get('department', ''), key="edit_department")
                    
                    submit_button = st.form_submit_button("Update User")
                    
                    if submit_button:
                        # Prepare data for update
                        update_data = {
                            'role': new_role,
                            'email': new_email,
                            'full_name': new_full_name,
                            'department': new_department
                        }
                        
                        # Add password if changed
                        if change_password:
                            if not new_password:
                                st.error("New password cannot be empty")
                                st.stop()
                            elif new_password != confirm_password:
                                st.error("Passwords do not match")
                                st.stop()
                            else:
                                update_data['password_hash'] = hash_password(new_password)
                        
                        # Update user or create task
                        success = User.update(
                            user_to_edit, 
                            update_data,
                            not check_admin_access(),  # Create task if not admin
                            st.session_state.username
                        )
                        
                        if success:
                            if check_admin_access():
                                st.success(f"User updated successfully")
                            else:
                                st.success(f"User update request submitted for approval")
                            
                            # Clear session state
                            if 'user_to_edit' in st.session_state:
                                del st.session_state.user_to_edit
                        else:
                            st.error(f"Failed to update user")
            else:
                st.error("User not found")
        else:
            st.info("Select a user to edit")

# Set the active tab based on session state
if 'active_tab' in st.session_state:
    if st.session_state.active_tab == "Edit User":
        st.session_state.tabs_selected = 2
        del st.session_state.active_tab
