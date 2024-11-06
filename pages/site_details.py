import streamlit as st
import pandas as pd
from utils.data_processor import load_data, calculate_kpis
from utils.visualizations import create_kpi_trends, create_performance_gauge

def render_site_details():
    st.title("Site Details Analysis")
    
    # Get selected site from session state
    if 'selected_site' not in st.session_state:
        st.warning("Please select a site from the main dashboard")
        return
    
    site_name = st.session_state['selected_site']
    st.header(f"📍 {site_name}")
    
    # Load data
    df = load_data()
    site_df = df[df['site_name'] == site_name].copy()
    
    # Calculate KPIs
    kpis = calculate_kpis(df, site_name)
    
    # Create layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Recovery Rate", f"{kpis['avg_recovery']:.1f}%")
    with col2:
        st.metric("Average Pressure", f"{kpis['avg_pressure']:.1f} bar")
    with col3:
        st.metric("Average Flow", f"{kpis['avg_flow']:.1f} m³/h")
    
    # Performance Score Gauge
    st.subheader("Overall Performance Score")
    gauge_fig = create_performance_gauge(
        kpis['efficiency_score'],
        "Efficiency Score"
    )
    st.plotly_chart(gauge_fig)
    
    # Trend Analysis
    st.subheader("Trend Analysis")
    fig_recovery, fig_pressure_flow = create_kpi_trends(df, site_name)
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_recovery)
    with col2:
        st.plotly_chart(fig_pressure_flow)

if __name__ == "__main__":
    render_site_details()
