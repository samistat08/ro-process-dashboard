import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from utils.data_processor import load_data, process_site_data
from utils.visualizations import create_world_map

# Page configuration
st.set_page_config(
    page_title="RO Process Monitoring Dashboard",
    page_icon="🌊",
    layout="wide"
)

def main():
    st.title("🌊 RO Process Monitoring Dashboard")
    
    # Load and process data
    try:
        df = load_data()
        sites_data = process_site_data(df)
        
        # Create two columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Global RO Facilities")
            # Create and display interactive map
            m = create_world_map(sites_data)
            folium_static(m)
        
        with col2:
            st.subheader("Site Overview")
            # Display summary metrics
            total_sites = len(sites_data['site_id'].unique())
            avg_recovery = sites_data['recovery_rate'].mean()
            
            st.metric("Total Active Sites", total_sites)
            st.metric("Average Recovery Rate", f"{avg_recovery:.1f}%")
            
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
