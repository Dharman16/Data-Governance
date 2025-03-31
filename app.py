import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import datetime
from auth import check_authentication, authenticate_user, create_default_users
from database import initialize_database
from utils import get_user_role, get_user_stats, get_reference_data_stats, get_task_stats

# Page configuration
st.set_page_config(
    page_title="Data Governance Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
initialize_database()
create_default_users()

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        color: #2C5282;
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .sub-header {
        color: #1A202C;
        font-size: 1.5rem;
        font-weight: 500;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .success-text {
        color: #48BB78;
    }
    .warning-text {
        color: #F6AD55;
    }
    .dashboard-container {
        background-color: #F7FAFC;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
        border: 1px solid #E2E8F0;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2C5282;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 1rem;
        color: #4A5568;
        font-weight: 500;
    }
    .metric-icon {
        font-size: 1.5rem;
        margin-bottom: 10px;
    }
    .sidebar-user {
        padding: 10px;
        background-color: #EDF2F7;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .activity-item {
        padding: 10px;
        border-left: 3px solid #2C5282;
        margin-bottom: 10px;
        background-color: white;
    }
    /* For status badges */
    .status-badge {
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: 500;
        font-size: 0.8rem;
        display: inline-block;
    }
    .status-pending {
        background-color: #FEF3C7;
        color: #92400E;
    }
    .status-approved {
        background-color: #DEF7EC;
        color: #046C4E;
    }
    .status-rejected {
        background-color: #FEE2E2;
        color: #9B1C1C;
    }
    /* Improve form inputs */
    div[data-testid="stTextInput"] label, div[data-testid="stSelectbox"] label {
        font-size: 1rem;
        font-weight: 500;
        color: #4A5568;
    }
    div.stButton > button {
        font-weight: 500;
    }
    /* Dividers */
    hr {
        margin: 2rem 0;
        border-color: #E2E8F0;
    }
    /* Tables styling */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Authentication
if not check_authentication():
    st.markdown('<p class="main-header">Welcome to Data Governance Platform</p>', unsafe_allow_html=True)
    
    # Login container with styling
    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    
    with login_col2:
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        
        # Platform logo
        logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
        with logo_col2:
            st.image("assets/logo.svg", width=150)
        
        st.markdown("<h3 style='text-align: center; margin-bottom: 30px;'>Login to Your Account</h3>", unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Sign In")
            
            if submit_button:
                if authenticate_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("<p style='text-align: center; margin-top: 20px; color: #718096; font-size: 0.9rem;'>Default credentials: admin/admin (Super Admin) or analyst/analyst (Data Analyst)</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Information about the platform
        st.markdown('<div class="dashboard-container" style="margin-top: 30px;">', unsafe_allow_html=True)
        st.markdown("<h4>About the Platform</h4>", unsafe_allow_html=True)
        st.markdown("""
        This enterprise Data Governance platform provides:
        - Comprehensive Reference Data Management
        - Master Data Management with approval workflows
        - Role-based access control
        - Task tracking and audit trails
        """)
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # Main application after authentication
    role = get_user_role()
    
    # Get statistics
    user_stats = get_user_stats()
    ref_data_stats = get_reference_data_stats()
    task_stats = get_task_stats()
    
    # Sidebar for navigation (handled by Streamlit pages)
    st.sidebar.title("Data Governance Platform")
    
    # Display user info with better styling
    st.sidebar.markdown('<div class="sidebar-user">', unsafe_allow_html=True)
    st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #2C5282; color: white; 
                    display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 10px;">
            {st.session_state.username[0].upper()}
        </div>
        <div>
            <div style="font-weight: 600;">{st.session_state.username}</div>
            <div style="font-size: 0.8rem; color: #4A5568;">{role.replace('_', ' ').title()}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Current time
    current_time = datetime.datetime.now().strftime("%B %d, %Y %H:%M")
    st.sidebar.markdown(f"<div style='font-size: 0.8rem; color: #718096;'>Last login: {current_time}</div>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Logout button
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()
    
    # Sidebar divider
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    
    # Main content with native components
    st.title("Data Governance Dashboard")
    
    # Dashboard overview with enhanced metrics using Streamlit's native components
    st.subheader("Dashboard Metrics")
    
    # Use Streamlit's native metrics
    metric_cols = st.columns(4)
    
    # User metric with icon
    with metric_cols[0]:
        st.markdown("### 👥")
        st.metric(
            label="Total Users",
            value=user_stats["total_users"],
            delta=None
        )
    
    # Reference data metric
    with metric_cols[1]:
        st.markdown("### 📊")
        st.metric(
            label="Reference Data Entries",
            value=ref_data_stats["total_entries"],
            delta=None
        )
    
    # Task metrics
    with metric_cols[2]:
        st.markdown("### ✅")
        st.metric(
            label="Approved Tasks",
            value=task_stats["approved_count"],
            delta=None
        )
    
    # Pending tasks
    with metric_cols[3]:
        st.markdown("### ⏳")
        st.metric(
            label="Pending Approvals",
            value=task_stats["pending_count"],
            delta=None
        )
    
    # Data statistics and charts
    col1, col2 = st.columns(2)
    
    # Reference Data Types with cleaner presentation
    with col1:
        st.markdown("### Reference Data by Type")
        
        if ref_data_stats["type_counts"]:
            # Create a bar chart of data types
            chart_data = pd.DataFrame({
                'Type': list(ref_data_stats["type_counts"].keys()),
                'Count': list(ref_data_stats["type_counts"].values())
            })
            chart_data = chart_data.sort_values('Count', ascending=False)
            
            # Use Streamlit's native bar chart with custom colors
            st.bar_chart(
                chart_data.set_index('Type'),
                use_container_width=True
            )
        else:
            st.info("No reference data available")
    
    # Recent Tasks with native components
    with col2:
        st.markdown("### Recent Activity")
        
        if task_stats.get("recent_tasks") and len(task_stats["recent_tasks"]) > 0:
            for task in task_stats["recent_tasks"]:
                task_dict = dict(task)
                status = task_dict['status']
                
                # Create a container for each task
                with st.container():
                    # Display status with appropriate color
                    if status == 'approved':
                        status_color = '#DEF7EC'
                    elif status == 'pending':
                        status_color = '#FEF3C7'
                    else:
                        status_color = '#FEE2E2'
                    
                    cols = st.columns([3, 1])
                    with cols[0]:
                        task_type_display = task_dict['task_type'].replace('_', ' ').title()
                        entity_type_display = task_dict['entity_type'].replace('_', ' ').title()
                        st.write(f"**Task #{task_dict['id']}**: {entity_type_display} {task_type_display}")
                        st.caption(f"By {task_dict['created_by']} on {task_dict['created_at'].split(' ')[0]}")
                    
                    with cols[1]:
                        st.write(f"**{status.capitalize()}**")
                    
                    st.divider()
        else:
            st.info("No recent activities")
    
    # Quick access cards using native Streamlit components
    st.subheader("Quick Access")
    quick_cols = st.columns(3)
    
    with quick_cols[0]:
        with st.container():
            st.markdown("### 👥")
            st.markdown("#### User Management")
            st.write("Manage users and roles")
            st.page_link("pages/1_User_Management.py", label="Go to User Management", icon="👥")
    
    with quick_cols[1]:
        with st.container():
            st.markdown("### 📊")
            st.markdown("#### Reference Data")
            st.write("Manage reference data entries")
            st.page_link("pages/2_Reference_Data_Management.py", label="Go to Reference Data", icon="📊")
    
    with quick_cols[2]:
        with st.container():
            st.markdown("### ✅")
            st.markdown("#### Task Operations")
            st.write("Approve or reject pending tasks")
            st.page_link("pages/3_Task_Operations.py", label="Go to Tasks", icon="✅")
    
    # Platform description with native components
    st.divider()
    st.header("About Data Governance Platform")
    
    st.markdown("""
    This enterprise-grade platform helps you manage and govern your organization's data through:
    
    - **Reference Data Management (RDM)**: Manage users and reference data with comprehensive CRUD operations
    - **Master Data Management (MDM)**: Efficiently upload and manage bulk data with approval workflows
    - **Task Operations**: Streamlined approval processes for maintaining data integrity
    - **Role-Based Access**: Secure permissions based on user roles (Super Admin and Data Analyst)
    
    Navigate through the modules using the sidebar menu according to your role permissions.
    """)