import streamlit as st
import pandas as pd
from auth import check_authentication
from database import get_db_connection, get_reference_data
from models import ReferenceData
from utils import can_manage_reference_data, can_view_users, get_data_types

# Page configuration
st.set_page_config(
    page_title="Reference Data Management - Data Governance Platform",
    page_icon="📚",
    layout="wide"
)

# Check authentication
if not check_authentication():
    st.warning("Please login to access this page")
    st.stop()

# Check access rights - all authenticated users can access this page
if not can_view_users():
    st.error("You do not have permission to view this page")
    st.stop()

# Page header
st.title("Reference Data Management")

# Tabs for different actions
tabs = st.tabs(["Reference Data List", "Create Reference Data", "Edit Reference Data"])

with tabs[0]:
    st.header("Reference Data List")
    
    # Refresh button
    if st.button("Refresh Reference Data List", key="refresh_ref_data_list"):
        st.rerun()
    
    # Get data types for filtering
    data_types = get_data_types()
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        type_filter = st.selectbox(
            "Filter by Data Type",
            options=["All"] + data_types,
            index=0,
            key="ref_data_type_filter"
        )
    
    with col2:
        search_term = st.text_input("Search by Code or Value", key="ref_data_search")
    
    # Get reference data based on filter
    if type_filter != "All":
        reference_data_df = get_reference_data(type_filter)
    else:
        reference_data_df = get_reference_data()
    
    # Apply search filter
    if not reference_data_df.empty and search_term:
        reference_data_df = reference_data_df[
            reference_data_df["code"].str.contains(search_term, case=False) |
            reference_data_df["value"].str.contains(search_term, case=False)
        ]
    
    # Display reference data
    if not reference_data_df.empty:
        st.dataframe(
            reference_data_df,
            column_config={
                "id": "ID",
                "data_type": "Data Type",
                "code": "Code",
                "value": "Value",
                "description": "Description",
                "status": "Status",
                "created_by": "Created By",
                "created_at": st.column_config.DatetimeColumn("Created At", format="MMM DD, YYYY")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Reference data actions (only if can manage)
        if can_manage_reference_data():
            st.subheader("Reference Data Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                ref_id_to_edit = st.selectbox(
                    "Select Reference Data to Edit",
                    options=reference_data_df["id"].tolist(),
                    format_func=lambda x: f"{reference_data_df[reference_data_df['id'] == x]['code'].iloc[0]} - {reference_data_df[reference_data_df['id'] == x]['value'].iloc[0]} (ID: {x})",
                    key="ref_edit_select_list"
                )
                
                if st.button("Edit Selected Reference Data", key="edit_selected_ref_btn"):
                    # Set session state for edit tab
                    st.session_state.ref_to_edit = ref_id_to_edit
                    st.session_state.active_tab = "Edit Reference Data"
                    st.rerun()
            
            with col2:
                ref_id_to_delete = st.selectbox(
                    "Select Reference Data to Delete",
                    options=reference_data_df["id"].tolist(),
                    format_func=lambda x: f"{reference_data_df[reference_data_df['id'] == x]['code'].iloc[0]} - {reference_data_df[reference_data_df['id'] == x]['value'].iloc[0]} (ID: {x})",
                    key="ref_delete_select_list"
                )
                
                if st.button("Delete Selected Reference Data", type="primary", key="delete_selected_ref_btn"):
                    # Confirm deletion
                    if st.session_state.get('confirm_delete_ref', False):
                        # Delete the reference data or create task
                        success = ReferenceData.delete(
                            ref_id_to_delete, 
                            True,  # Always create a task for reference data deletion
                            st.session_state.username
                        )
                        
                        if success:
                            st.success("Reference data deletion request submitted for approval")
                            st.session_state.confirm_delete_ref = False
                            st.rerun()
                        else:
                            st.error("Failed to create deletion request")
                    else:
                        st.session_state.confirm_delete_ref = True
                        st.warning(f"Are you sure you want to delete this reference data? Click 'Delete Selected Reference Data' again to confirm.")
    else:
        if type_filter != "All":
            st.info(f"No reference data found for type: {type_filter}")
        else:
            st.info("No reference data found in the database")

with tabs[1]:
    st.header("Create Reference Data")
    
    # Check if user has permission to create reference data
    if not can_manage_reference_data():
        st.warning("You don't have permission to create reference data")
    else:
        # Reference data creation form
        with st.form("create_reference_data_form"):
            # Get existing data types for dropdown
            existing_types = get_data_types()
            
            # Option to select existing type or create new
            use_existing_type = st.checkbox("Use existing data type", value=True if existing_types else False, key="create_use_existing_type")
            
            if use_existing_type and existing_types:
                data_type = st.selectbox("Data Type*", options=existing_types, key="create_data_type_select")
            else:
                data_type = st.text_input("Data Type*", help="Category of reference data (e.g., Country, Currency)", key="create_data_type_input")
            
            code = st.text_input("Code*", help="Unique identifier for this reference data", key="create_code")
            value = st.text_input("Value*", help="Display value for this reference data", key="create_value")
            description = st.text_area("Description", help="Additional information about this reference data", key="create_description")
            
            submit_button = st.form_submit_button("Create Reference Data")
            
            if submit_button:
                # Validate inputs
                if not data_type or not code or not value:
                    st.error("Data Type, Code, and Value are required")
                else:
                    # Create reference data or task
                    success = ReferenceData.create(
                        data_type, 
                        code, 
                        value, 
                        description,
                        True,  # Always create a task for reference data creation
                        st.session_state.username
                    )
                    
                    if success:
                        st.success(f"Reference data creation request submitted for approval")
                    else:
                        st.error(f"Failed to create reference data. Code may already exist for this data type.")

with tabs[2]:
    st.header("Edit Reference Data")
    
    # Check if user has permission to edit reference data
    if not can_manage_reference_data():
        st.warning("You don't have permission to edit reference data")
    else:
        # Get reference data to edit from session state or select
        ref_to_edit = st.session_state.get("ref_to_edit", None)
        
        if not ref_to_edit:
            reference_data_df = get_reference_data()
            if not reference_data_df.empty:
                ref_to_edit = st.selectbox(
                    "Select Reference Data to Edit",
                    options=reference_data_df["id"].tolist(),
                    format_func=lambda x: f"{reference_data_df[reference_data_df['id'] == x]['code'].iloc[0]} - {reference_data_df[reference_data_df['id'] == x]['value'].iloc[0]} (ID: {x})",
                    key="ref_edit_tab_select"
                )
        
        if ref_to_edit:
            # Get reference data details
            ref_data = ReferenceData.get(ref_to_edit)
            
            if ref_data:
                # Reference data edit form
                with st.form("edit_reference_data_form"):
                    st.write(f"Editing Reference Data: {ref_data['code']} - {ref_data['value']}")
                    
                    # Data type cannot be edited
                    st.info(f"Data Type: {ref_data['data_type']} (cannot be changed)")
                    
                    # Code cannot be edited
                    st.info(f"Code: {ref_data['code']} (cannot be changed)")
                    
                    # Created by information
                    if ref_data.get('created_by'):
                        st.info(f"Created By: {ref_data['created_by']}")
                    
                    new_value = st.text_input("Value*", value=ref_data['value'], key="edit_value")
                    new_description = st.text_area("Description", value=ref_data.get('description', ''), key="edit_description")
                    new_status = st.selectbox("Status", options=["active", "inactive"], index=0 if ref_data['status'] == "active" else 1, key="edit_status")
                    
                    submit_button = st.form_submit_button("Update Reference Data")
                    
                    if submit_button:
                        # Validate inputs
                        if not new_value:
                            st.error("Value is required")
                        else:
                            # Prepare data for update
                            update_data = {
                                'value': new_value,
                                'description': new_description,
                                'status': new_status
                            }
                            
                            # Update reference data or create task
                            success = ReferenceData.update(
                                ref_to_edit, 
                                update_data,
                                True,  # Always create a task for reference data update
                                st.session_state.username
                            )
                            
                            if success:
                                st.success(f"Reference data update request submitted for approval")
                                
                                # Clear session state
                                if 'ref_to_edit' in st.session_state:
                                    del st.session_state.ref_to_edit
                            else:
                                st.error(f"Failed to update reference data")
            else:
                st.error("Reference data not found")
        else:
            st.info("Select reference data to edit")

# Set the active tab based on session state
if 'active_tab' in st.session_state:
    if st.session_state.active_tab == "Edit Reference Data":
        st.session_state.tabs_selected = 2
        del st.session_state.active_tab
