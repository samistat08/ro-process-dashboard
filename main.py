import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from utils.data_processor import load_data, process_site_data
from utils.visualizations import create_world_map
import time
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="RO Process Monitoring Dashboard",
    page_icon="🌊",
    layout="wide"
)

def main():
    st.title("🌊 RO Process Monitoring Dashboard")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Add auto-refresh checkbox
    auto_refresh = st.sidebar.checkbox("Enable Auto-refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 
                                    min_value=5, 
                                    max_value=60, 
                                    value=10)
    
    # Add date range picker
    st.sidebar.subheader("Time Filter")
    use_time_filter = st.sidebar.checkbox("Enable Time Filter")
    
    start_date = None
    end_date = None
    
    if use_time_filter:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start Date", 
                                     value=datetime.now() - timedelta(days=7),
                                     max_value=datetime.now())
        with col2:
            end_date = st.date_input("End Date", 
                                   value=datetime.now(),
                                   max_value=datetime.now())
        
        if start_date > end_date:
            st.sidebar.error("Start date must be before end date")
            return
            
        # Convert to datetime
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
    
    # Initialize last_refresh in session state
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Check if it's time to refresh
    current_time = time.time()
    should_refresh = auto_refresh and (current_time - st.session_state.last_refresh) >= refresh_interval
    
    if should_refresh:
        st.session_state.last_refresh = current_time
        st.rerun()
    
    # Load and process data
    try:
        df = load_data(use_real_time=True, start_date=start_date, end_date=end_date)
        sites_data = process_site_data(df)
        
        # Create two columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Global RO Facilities")
            # Create and display interactive map
            m = create_world_map(sites_data)
            st_folium(m, width=800)
        
        with col2:
            st.subheader("Site Overview")
            # Display summary metrics
            total_sites = len(sites_data['site_id'].unique())
            avg_recovery = sites_data['recovery_rate'].mean()
            
            st.metric("Total Active Sites", total_sites)
            st.metric("Average Recovery Rate", f"{avg_recovery:.1f}%")
            
            # Display time range
            if use_time_filter:
                st.info(f"Showing data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Last updated timestamp
            st.text(f"Last Updated: {df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Site selector
            selected_site = st.selectbox(
                "Select Site for Details",
                options=sites_data['site_name'].unique()
            )
            
            if st.button("View Site Details"):
                st.session_state['selected_site'] = selected_site
                st.switch_page("pages/site_details.py")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        
if __name__ == "__main__":
    main()
