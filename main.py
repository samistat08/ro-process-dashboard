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

def get_data_date_range():
    """Get the full date range available in the data"""
    try:
        df = load_data(use_real_time=False)  # Load historical data only for range calculation
        min_date = df['timestamp'].min().date()
        max_date = datetime.now().date()
        return min_date, max_date
    except Exception:
        # Fallback to last week if can't determine range
        now = datetime.now().date()
        return now - timedelta(days=7), now

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
    
    start_datetime = None
    end_datetime = None
    
    try:
        if use_time_filter:
            # Get available date range
            min_date, max_date = get_data_date_range()
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=max_date - timedelta(days=7),
                    min_value=min_date,
                    max_value=max_date
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            if start_date > end_date:
                st.sidebar.error("Start date must be before end date")
                return
            
            # Convert to datetime with time component
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            st.sidebar.info(f"Data available from {min_date} to {max_date}")
    except Exception as e:
        st.sidebar.error(f"Error setting date range: {str(e)}")
        return
    
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
        df = load_data(use_real_time=True, start_date=start_datetime, end_date=end_datetime)
        if df.empty:
            st.warning("No data available for the selected time range")
            return
            
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
                st.info(f"Showing data from {start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}")
            
            # Last updated timestamp
            st.text(f"Last Updated: {df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Site selector and navigation buttons
            selected_site = st.selectbox(
                "Select Site for Details",
                options=sites_data['site_name'].unique()
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Site Details"):
                    st.session_state['selected_site'] = selected_site
                    st.switch_page("pages/site_details.py")
            with col2:
                if st.button("Compare Sites"):
                    st.switch_page("pages/comparison_analysis.py")

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        
if __name__ == "__main__":
    main()
