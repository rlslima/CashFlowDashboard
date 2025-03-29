import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.google_sheets import fetch_google_sheet_data
from utils.data_processor import process_data
from views.monthly_view import show_monthly_view
from views.period_view import show_period_view
from views.yearly_view import show_yearly_view
from views.company_view import show_company_view

# Set page configuration
st.set_page_config(
    page_title="Combrasen Group Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define session state for data
if 'data' not in st.session_state:
    st.session_state.data = None
    st.session_state.last_refresh = None

# App title and header
st.title("Combrasen Group Financial Dashboard")
st.markdown("---")

# Function to load and process data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    try:
        # Google Sheet URL
        sheet_url = "https://docs.google.com/spreadsheets/d/1XRy39MblVtmWLpggz1cC_qIRdqE40vIx/edit?usp=sharing&ouid=110344857582375962786&rtpof=true&sd=true"
        
        # Fetch data from Google Sheets
        raw_data = fetch_google_sheet_data(sheet_url)
        
        if raw_data is not None and not raw_data.empty:
            # Process the data
            processed_data = process_data(raw_data)
            return processed_data
        else:
            st.error("Failed to load data from Google Sheets or the sheet is empty.")
            return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Sidebar - Data Refresh
with st.sidebar:
    st.title("Dashboard Controls")
    
    # Refresh data button
    if st.button("Refresh Data", use_container_width=True):
        with st.spinner("Refreshing data..."):
            st.session_state.data = load_data()
            st.session_state.last_refresh = datetime.now()
        st.success("Data refreshed successfully!")
    
    # Show last refresh time
    if st.session_state.last_refresh:
        st.info(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("Views")
    view = st.radio(
        "Select View",
        options=["Monthly Cash Flow", "Period Analysis", "Yearly Summary", "Company Comparison"],
        label_visibility="collapsed"
    )

# Load data if not already loaded
if st.session_state.data is None:
    with st.spinner("Loading data for the first time..."):
        st.session_state.data = load_data()
        st.session_state.last_refresh = datetime.now()

# Show data or error message
if st.session_state.data is not None:
    df = st.session_state.data
    
    # Global Filters
    with st.expander("Global Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # Company filter
        with col1:
            all_companies = ["All"] + sorted(df["Company"].unique().tolist())
            selected_company = st.selectbox("Company", all_companies)
        
        # Type filter (Expense/Income)
        with col2:
            all_types = ["All"] + sorted(df["Type"].unique().tolist())
            selected_type = st.selectbox("Type", all_types)
            
        # Work code filter
        with col3:
            all_works = ["All"] + sorted(df["Work"].unique().tolist())
            selected_work = st.selectbox("Work Code", all_works)
    
    # Apply global filters
    filtered_df = df.copy()
    
    if selected_company != "All":
        filtered_df = filtered_df[filtered_df["Company"] == selected_company]
    
    if selected_type != "All":
        filtered_df = filtered_df[filtered_df["Type"] == selected_type]
    
    if selected_work != "All":
        filtered_df = filtered_df[filtered_df["Work"] == selected_work]
    
    # Display selected view
    if view == "Monthly Cash Flow":
        show_monthly_view(filtered_df)
    elif view == "Period Analysis":
        show_period_view(filtered_df)
    elif view == "Yearly Summary":
        show_yearly_view(filtered_df)
    elif view == "Company Comparison":
        show_company_view(filtered_df)
    
else:
    st.error("No data available. Please check the connection to Google Sheets or try refreshing.")
    st.info("""
        Expected data format:
        - Company: e.g. "Range 1"
        - Type: "Expense" or "Income"
        - Work: e.g. "INC01"
        - Supplier/Client: e.g. "35 - JOSE ELIAS FERNANDES JÚNIOR"
        - Value: e.g. "35,600.00"
        - Date: e.g. "03/24/2025"
    """)

# Footer
st.markdown("---")
st.caption("Combrasen Group Financial Dashboard © 2023")
