import streamlit as st
import pandas as pd
import json
import io
from auth import check_authentication, hash_password, check_admin_access
from database import get_db_connection
from models import User, ReferenceData, Task
from utils import can_upload_bulk_data, parse_excel_upload, parse_csv_upload

# Page configuration
st.set_page_config(
    page_title="Bulk Upload - Data Governance Platform",
    page_icon="📤",
    layout="wide"
)

# Check authentication
if not check_authentication():
    st.warning("Please login to access this page")
    st.stop()

# Check permissions
if not can_upload_bulk_data():
    st.error("You do not have permission to access this page")
    st.stop()

# Page header
st.title("Bulk Data Upload")
st.write("Upload multiple users or reference data entries at once")

# Tabs for different upload types
tabs = st.tabs(["User Upload", "Reference Data Upload", "Upload History"])

# Sample data templates for download
with st.sidebar:
    st.header("Download Templates")
    
    # User template
    user_template = pd.DataFrame({
        'username': ['user1', 'user2'],
        'password': ['password1', 'password2'],
        'role': ['data_analyst', 'data_analyst'],
        'email': ['user1@example.com', 'user2@example.com'],
        'full_name': ['User One', 'User Two'],
        'department': ['Department A', 'Department B']
    })
    
    user_buffer = io.BytesIO()
    try:
        user_template.to_excel(user_buffer, index=False, engine='openpyxl')
        user_buffer.seek(0)
        
        st.download_button(
            label="Download User Template",
            data=user_buffer,
            file_name="user_template.xlsx",
            mime="application/vnd.ms-excel",
            key="download_user_template"
        )
    except Exception as e:
        st.error(f"Could not generate Excel template: {e}")
        # Provide CSV as fallback
        user_csv = user_template.to_csv(index=False)
        st.download_button(
            label="Download User Template (CSV)",
            data=user_csv,
            file_name="user_template.csv",
            mime="text/csv",
            key="download_user_template_csv"
        )
    
    # Reference data template
    ref_template = pd.DataFrame({
        'data_type': ['Country', 'Country', 'Currency', 'Currency'],
        'code': ['US', 'UK', 'USD', 'EUR'],
        'value': ['United States', 'United Kingdom', 'US Dollar', 'Euro'],
        'description': ['USA', 'Great Britain', 'United States Dollar', 'European Euro']
    })
    
    ref_buffer = io.BytesIO()
    try:
        ref_template.to_excel(ref_buffer, index=False, engine='openpyxl')
        ref_buffer.seek(0)
        
        st.download_button(
            label="Download Reference Data Template",
            data=ref_buffer,
            file_name="reference_data_template.xlsx",
            mime="application/vnd.ms-excel",
            key="download_ref_template"
        )
    except Exception as e:
        st.error(f"Could not generate Excel template: {e}")
        # Provide CSV as fallback
        ref_csv = ref_template.to_csv(index=False)
        st.download_button(
            label="Download Reference Data Template (CSV)",
            data=ref_csv,
            file_name="reference_data_template.csv",
            mime="text/csv",
            key="download_ref_template_csv"
        )

# User upload tab
with tabs[0]:
    st.header("Upload Users")
    
    upload_type = st.radio("Select Upload Format", ["Excel", "CSV"])
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"] if upload_type == "Both" else 
             ["xlsx"] if upload_type == "Excel" else 
             ["csv"]
    )
    
    if uploaded_file:
        if upload_type == "Excel" or (upload_type == "Both" and uploaded_file.name.endswith(('.xlsx', '.xls'))):
            df, error = parse_excel_upload(uploaded_file)
        else:
            df, error = parse_csv_upload(uploaded_file)
        
        if error:
            st.error(f"Error parsing file: {error}")
        elif df is not None:
            # Validate required columns
            required_columns = ["username", "password", "role"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                st.success("File parsed successfully")
                st.write(f"Found {len(df)} user records")
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(df, use_container_width=True)
                
                # Validation checks
                st.subheader("Validation Results")
                
                # Username uniqueness check
                if df['username'].duplicated().any():
                    st.warning("Duplicate usernames found in the file")
                
                # Role validation
                invalid_roles = df[~df['role'].isin(['super_admin', 'data_analyst'])]['role'].unique()
                if len(invalid_roles) > 0:
                    st.warning(f"Invalid roles found: {', '.join(invalid_roles)}. Valid roles are 'super_admin' and 'data_analyst'")
                
                # Process button for task creation
                if st.button("Submit for Super Admin Approval", type="primary", key="user_task_button"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Create task for bulk user upload
                    task_data = {
                        'file_name': uploaded_file.name,
                        'record_count': len(df),
                        'records': df.to_dict(orient='records')
                    }
                    
                    task_id = Task.create(
                        'bulk_upload', 
                        'user', 
                        None, 
                        task_data, 
                        st.session_state.username
                    )
                    
                    status_text.info(f"User bulk upload task created (Task ID: {task_id}). The upload will be processed after Super Admin approval.")
                    progress_bar.progress(100)
                
                # Information message about process
                st.info("All bulk uploads require Super Admin approval before being processed. You can check the status of your upload in the Upload History tab.")

# Reference data upload tab
with tabs[1]:
    st.header("Upload Reference Data")
    
    upload_type = st.radio("Select Upload Format", ["Excel", "CSV"], key="ref_upload_type")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["xlsx", "csv"] if upload_type == "Both" else 
             ["xlsx"] if upload_type == "Excel" else 
             ["csv"],
        key="ref_data_upload"
    )
    
    if uploaded_file:
        if upload_type == "Excel" or (upload_type == "Both" and uploaded_file.name.endswith(('.xlsx', '.xls'))):
            df, error = parse_excel_upload(uploaded_file)
        else:
            df, error = parse_csv_upload(uploaded_file)
        
        if error:
            st.error(f"Error parsing file: {error}")
        elif df is not None:
            # Validate required columns
            required_columns = ["data_type", "code", "value"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                st.success("File parsed successfully")
                st.write(f"Found {len(df)} reference data records")
                
                # Display preview
                st.subheader("Preview")
                st.dataframe(df, use_container_width=True)
                
                # Validation checks
                st.subheader("Validation Results")
                
                # Check for unique data_type + code combinations
                df['type_code'] = df['data_type'] + '-' + df['code']
                if df['type_code'].duplicated().any():
                    st.warning("Duplicate data_type and code combinations found in the file")
                
                # Remove the temporary type_code column we added for validation
                if 'type_code' in df.columns:
                    df = df.drop(columns=['type_code'])
                
                # Process button for task creation
                if st.button("Submit for Super Admin Approval", type="primary", key="ref_task_button"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Create task for bulk reference data upload
                    task_data = {
                        'file_name': uploaded_file.name,
                        'record_count': len(df),
                        'records': df.to_dict(orient='records')
                    }
                    
                    task_id = Task.create(
                        'bulk_upload', 
                        'reference_data', 
                        None, 
                        task_data, 
                        st.session_state.username
                    )
                    
                    status_text.info(f"Reference data bulk upload task created (Task ID: {task_id}). The upload will be processed after Super Admin approval.")
                    progress_bar.progress(100)
                
                # Information message about process
                st.info("All bulk uploads require Super Admin approval before being processed. You can check the status of your upload in the Upload History tab.")

# Upload history tab
with tabs[2]:
    st.header("Upload History")
    
    # Get bulk upload tasks
    conn = get_db_connection()
    tasks_df = pd.read_sql_query(
        "SELECT id, task_type, entity_type, status, created_by, created_at, approved_by, approved_at FROM tasks WHERE task_type = 'bulk_upload'",
        conn
    )
    conn.close()
    
    if not tasks_df.empty:
        # Display tasks
        st.dataframe(
            tasks_df,
            column_config={
                "id": "Task ID",
                "entity_type": "Data Type",
                "status": "Status",
                "created_by": "Created By",
                "created_at": st.column_config.DatetimeColumn("Created At", format="MMM DD, YYYY HH:mm"),
                "approved_by": "Processed By",
                "approved_at": st.column_config.DatetimeColumn("Processed At", format="MMM DD, YYYY HH:mm")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # View details
        selected_task_id = st.selectbox(
            "Select Task to View Details",
            options=tasks_df["id"].tolist(),
            format_func=lambda x: f"Task ID: {x} - {tasks_df[tasks_df['id'] == x]['entity_type'].iloc[0]} upload on {tasks_df[tasks_df['id'] == x]['created_at'].iloc[0]}"
        )
        
        if selected_task_id:
            # Get task details
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (selected_task_id,))
            task = cursor.fetchone()
            conn.close()
            
            if task:
                task_dict = dict(task)
                data = json.loads(task_dict['data_json'])
                
                st.subheader("Upload Details")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**File Name:**", data.get('file_name', 'N/A'))
                    st.write("**Record Count:**", data.get('record_count', 0))
                    st.write("**Status:**", task_dict['status'].capitalize())
                
                with col2:
                    st.write("**Uploaded By:**", task_dict['created_by'])
                    st.write("**Uploaded At:**", task_dict['created_at'])
                    if task_dict['approved_by']:
                        st.write("**Processed By:**", task_dict['approved_by'])
                        st.write("**Processed At:**", task_dict['approved_at'])
                
                # Preview records
                if 'records' in data:
                    st.subheader("Records Preview")
                    records_df = pd.DataFrame(data['records'])
                    st.dataframe(records_df, use_container_width=True)
                    
                    # Add approval/rejection buttons for pending tasks only for super admins
                    if task_dict['status'] == 'pending':
                        # Check if current user is a super admin
                        if check_admin_access():
                            st.subheader("Super Admin Actions")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("Approve Task", key=f"approve_history_{selected_task_id}", type="primary"):
                                    success = Task.approve(selected_task_id, st.session_state.username)
                                    if success:
                                        st.success("Task approved and processed successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to approve task")
                            
                            with col2:
                                if st.button("Reject Task", key=f"reject_history_{selected_task_id}"):
                                    success = Task.reject(selected_task_id, st.session_state.username)
                                    if success:
                                        st.success("Task rejected successfully")
                                        st.rerun()
                                    else:
                                        st.error("Failed to reject task")
                        else:
                            st.info("This bulk upload is pending Super Admin approval. Only Super Admins can approve or reject bulk uploads.")
    else:
        st.info("No upload history found")
