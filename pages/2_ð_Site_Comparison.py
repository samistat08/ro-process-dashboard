import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.data_processor import load_data
from datetime import datetime, timedelta

st.set_page_config(page_title="Site Comparison", page_icon="📊", layout="wide")

def create_comparison_chart(df, sites, metric):
    """Create a comparison chart for selected sites and metric"""
    fig = go.Figure()
    
    for site in sites:
        site_data = df[df['site_name'] == site]
        fig.add_trace(go.Scatter(
            x=site_data['timestamp'],
            y=site_data[metric],
            name=site,
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title=f'{metric} Comparison',
        xaxis_title='Time',
        yaxis_title=metric,
        height=400,
        showlegend=True,
        hovermode='x unified'
    )
    return fig

def create_radar_chart(df, sites, metrics):
    """Create a radar chart comparing multiple metrics across sites"""
    fig = go.Figure()
    
    # Calculate the mean values for each metric for normalization
    max_values = {metric: df[metric].max() for metric in metrics}
    
    for site in sites:
        site_data = df[df['site_name'] == site].mean()
        # Normalize the values to 0-100 scale for better comparison
        values = [(site_data[metric] / max_values[metric]) * 100 if max_values[metric] != 0 else 0 
                 for metric in metrics]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            name=site,
            fill='toself'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title='Multi-metric Site Comparison (Normalized %)',
        height=500
    )
    return fig

try:
    st.title("📊 Site Comparison Analysis")
    
    # Load data
    df = load_data(use_real_time=True)
    
    if df.empty:
        st.error("No data available. Please check the data source.")
        st.stop()
    
    # Sidebar controls
    st.sidebar.header("Comparison Settings")
    
    # Site selection
    available_sites = sorted(df['site_name'].unique())
    selected_sites = st.sidebar.multiselect(
        "Select Sites to Compare",
        options=available_sites,
        default=available_sites[:2]
    )
    
    if len(selected_sites) < 2:
        st.warning("Please select at least two sites for comparison")
        st.stop()
    
    # Time range selection
    time_options = {
        'Last 24 Hours': timedelta(days=1),
        'Last Week': timedelta(days=7),
        'Last Month': timedelta(days=30),
        'All Time': None
    }
    selected_time = st.sidebar.selectbox("Select Time Range", options=list(time_options.keys()))
    
    # Filter data based on time selection
    if time_options[selected_time] is not None:
        cutoff_time = datetime.now() - time_options[selected_time]
        df = df[df['timestamp'] >= cutoff_time]
    
    # Available metrics for comparison
    metrics = ['pressure', 'flow-ID-001_feed', 'recovery_rate', 'temperature', 'pH']
    metric_labels = {
        'pressure': 'Pressure (psi)',
        'flow-ID-001_feed': 'Flow Rate (gpm)',
        'recovery_rate': 'Recovery Rate (%)',
        'temperature': 'Temperature (°C)',
        'pH': 'pH Level'
    }
    
    # Create tabs for different comparison views
    tab1, tab2, tab3 = st.tabs(["Trend Comparison", "Multi-metric Analysis", "Performance Summary"])
    
    with tab1:
        st.subheader("Trend Comparison")
        selected_metric = st.selectbox(
            "Select Metric for Comparison",
            options=metrics,
            format_func=lambda x: metric_labels[x]
        )
        
        if selected_metric:
            trend_fig = create_comparison_chart(df, selected_sites, selected_metric)
            st.plotly_chart(trend_fig, use_container_width=True)
    
    with tab2:
        st.subheader("Multi-metric Analysis")
        selected_metrics = st.multiselect(
            "Select Metrics for Radar Chart",
            options=metrics,
            default=metrics[:4],
            format_func=lambda x: metric_labels[x]
        )
        
        if selected_metrics:
            radar_fig = create_radar_chart(df, selected_sites, selected_metrics)
            st.plotly_chart(radar_fig, use_container_width=True)
    
    with tab3:
        st.subheader("Performance Summary")
        summary_data = []
        
        for site in selected_sites:
            site_data = df[df['site_name'] == site]
            summary = {
                'Site': site,
                'Recovery Rate': f"{site_data['recovery_rate'].mean():.1f}%",
                'Pressure': f"{site_data['pressure'].mean():.1f} psi",
                'Flow Rate': f"{site_data['flow-ID-001_feed'].mean():.1f} gpm",
                'Temperature': f"{site_data['temperature'].mean():.1f}°C"
            }
            summary_data.append(summary)
        
        st.dataframe(pd.DataFrame(summary_data))

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.stop()