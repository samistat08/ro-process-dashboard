import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_processor import load_data, process_site_data

def render_kpi_analysis():
    st.title("KPI Analysis Dashboard")
    
    # Load data
    df = load_data()
    sites_data = process_site_data(df)
    
    # Time period selector
    time_period = st.selectbox(
        "Select Time Period",
        ["Last 24 Hours", "Last Week", "Last Month", "Last Year"]
    )
    
    # Create KPI comparisons
    st.subheader("Site Performance Comparison")
    
    # Recovery Rate Comparison
    fig_recovery = px.bar(
        sites_data,
        x='site_name',
        y='recovery_rate',
        title='Recovery Rate by Site'
    )
    st.plotly_chart(fig_recovery)
    
    # Efficiency Matrix
    st.subheader("Efficiency Matrix")
    fig_matrix = px.scatter(
        sites_data,
        x='pressure',
        y='flow_rate',
        size='recovery_rate',
        color='site_name',
        title='Pressure-Flow-Recovery Matrix'
    )
    st.plotly_chart(fig_matrix)
    
    # Site Rankings
    st.subheader("Site Rankings")
    rankings = sites_data.sort_values('recovery_rate', ascending=False)
    st.dataframe(
        rankings[['site_name', 'recovery_rate', 'pressure', 'flow_rate']]
        .style.highlight_max(axis=0)
    )

if __name__ == "__main__":
    render_kpi_analysis()
