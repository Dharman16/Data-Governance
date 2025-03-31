import streamlit as st
import pandas as pd
import json
from auth import check_authentication
from database import get_db_connection, get_tasks
from models import Task
from utils import can_approve_tasks, format_task_description

# Page configuration
st.set_page_config(
    page_title="Task Operations - Data Governance Platform",
    page_icon="✅",
    layout="wide"
)

# Check authentication
if not check_authentication():
    st.warning("Please login to access this page")
    st.stop()

# Page header
st.title("Task Operations")

# Check if user can approve tasks
can_approve = can_approve_tasks()

# Tabs for different task statuses
tabs = st.tabs(["Pending Tasks", "Approved Tasks", "Rejected Tasks", "All Tasks"])

# Helper function to display task details
def display_task_details(task_id):
    # Use the Task model to get the task details instead of direct DB access
    task_dict = Task.get(task_id)
    
    if task_dict:
        # Print task details for debugging
        print(f"Displaying task details for Task ID: {task_id}")
        print(f"Task status: {task_dict.get('status')}")
        print(f"Task data: {task_dict.get('data')}")
        
        st.subheader("Task Details")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Task ID:**", task_dict['id'])
            st.write("**Task Type:**", task_dict['task_type'].capitalize())
            st.write("**Entity Type:**", task_dict['entity_type'].replace('_', ' ').title())
            st.write("**Entity ID:**", task_dict['entity_id'] if task_dict['entity_id'] else "New entity")
            st.write("**Status:**", task_dict['status'].capitalize())
        
        with col2:
            st.write("**Created By:**", task_dict['created_by'])
            st.write("**Created At:**", task_dict['created_at'])
            if task_dict.get('approved_by'):
                st.write("**Processed By:**", task_dict['approved_by'])
                st.write("**Processed At:**", task_dict['approved_at'])
        
        st.subheader("Task Data")
        
        # Get data from the task dictionary
        data = task_dict.get('data', {})
        
        # Format data based on entity type
        if task_dict['entity_type'] == 'user':
            if 'password_hash' in data:
                data['password'] = "********"  # Hide password hash
                del data['password_hash']
            
            for key, value in data.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
        elif task_dict['entity_type'] == 'reference_data':
            for key, value in data.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # Approval/rejection buttons for pending tasks
        if task_dict['status'] == 'pending' and can_approve:
            col1, col2 = st.columns(2)
            
            with col1:
                # Use a more specific, unique key that includes tab name and task ID
                unique_approve_key = f"approve_task_details_{task_id}_{task_dict['entity_type']}"
                if st.button("Approve Task", key=unique_approve_key, type="primary"):
                    try:
                        success = Task.approve(task_id, st.session_state.username)
                        if success:
                            st.success("Task approved successfully")
                            st.rerun()
                        else:
                            st.error("Failed to approve task")
                    except Exception as e:
                        st.error(f"Error approving task: {str(e)}")
            
            with col2:
                # Use a more specific, unique key that includes tab name and task ID
                unique_reject_key = f"reject_task_details_{task_id}_{task_dict['entity_type']}"
                if st.button("Reject Task", key=unique_reject_key):
                    try:
                        success = Task.reject(task_id, st.session_state.username)
                        if success:
                            st.success("Task rejected successfully")
                            st.rerun()
                        else:
                            st.error("Failed to reject task")
                    except Exception as e:
                        st.error(f"Error rejecting task: {str(e)}")
    else:
        st.error("Task not found")

# Function to display task list
def display_task_list(tasks_df, status=None):
    if tasks_df.empty:
        if status:
            st.info(f"No {status} tasks found")
        else:
            st.info("No tasks found")
        return
    
    # Filter by status if specified
    if status:
        filtered_df = tasks_df[tasks_df['status'] == status]
    else:
        filtered_df = tasks_df
    
    if filtered_df.empty:
        st.info(f"No {status} tasks found")
        return
    
    # Add a description column
    filtered_df['description'] = filtered_df.apply(lambda x: format_task_description(x), axis=1)
    
    # Display tasks
    st.dataframe(
        filtered_df,
        column_config={
            "id": "ID",
            "description": "Description",
            "task_type": "Task Type",
            "entity_type": "Entity Type",
            "status": "Status",
            "created_by": "Created By",
            "created_at": st.column_config.DatetimeColumn("Created At", format="MMM DD, YYYY HH:mm")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Task selection for details
    selected_task_id = st.selectbox(
        "Select Task to View Details",
        options=filtered_df["id"].tolist(),
        format_func=lambda x: f"ID: {x} - {filtered_df[filtered_df['id'] == x]['description'].iloc[0]}",
        key=f"select_task_{status or 'all'}"
    )
    
    if selected_task_id:
        st.divider()
        display_task_details(selected_task_id)

# Get all tasks
tasks_df = get_tasks()

# Display tasks in tabs
with tabs[0]:
    st.header("Pending Tasks")
    if st.button("Refresh Pending Tasks", key="refresh_pending_tasks"):
        st.rerun()
    display_task_list(tasks_df, 'pending')

with tabs[1]:
    st.header("Approved Tasks")
    if st.button("Refresh Approved Tasks", key="refresh_approved_tasks"):
        st.rerun()
    display_task_list(tasks_df, 'approved')

with tabs[2]:
    st.header("Rejected Tasks")
    if st.button("Refresh Rejected Tasks", key="refresh_rejected_tasks"):
        st.rerun()
    display_task_list(tasks_df, 'rejected')

with tabs[3]:
    st.header("All Tasks")
    if st.button("Refresh All Tasks", key="refresh_all_tasks"):
        st.rerun()
    display_task_list(tasks_df)
