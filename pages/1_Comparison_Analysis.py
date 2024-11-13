import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_processor import load_data
from datetime import datetime, timedelta

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
        title=f'{metric.replace("_", " ").title()} Comparison',
        xaxis_title='Time',
        yaxis_title=metric.replace("_", " ").title(),
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
            theta=[metric.replace("_", " ").title() for metric in metrics],
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

def create_bar_comparison(df, sites, metric):
    """Create a bar chart comparing average values across sites"""
    site_averages = []
    for site in sites:
        site_data = df[df['site_name'] == site]
        site_averages.append({
            'site': site,
            'average': site_data[metric].mean()
        })
    
    fig = go.Figure(data=[
        go.Bar(
            x=[data['site'] for data in site_averages],
            y=[data['average'] for data in site_averages],
            text=[f"{data['average']:.2f}" for data in site_averages],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=f'Average {metric.replace("_", " ").title()} by Site',
        xaxis_title='Site',
        yaxis_title=f'Average {metric.replace("_", " ").title()}',
        height=400
    )
    return fig

st.title("📊 Site Comparison Analysis")

try:
    # Load data
    df = load_data(use_real_time=True)
    
    if df.empty:
        st.error("No data available. Please check the data source.")
        st.stop()
    
    # Get unique sites
    sites = df['site_name'].unique()
    
    # Site selection
    st.sidebar.header("Comparison Settings")
    selected_sites = st.sidebar.multiselect(
        "Select Sites to Compare",
        options=sites,
        default=list(sites)[:2]  # Default to first two sites
    )
    
    if len(selected_sites) < 2:
        st.warning("Please select at least two sites for comparison")
        st.stop()
    
    # Available metrics for comparison (only numeric columns)
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    metrics = [col for col in numeric_columns if col not in ['site_id', 'Latitude', 'Longitude']]
    
    # Time range selection
    st.sidebar.subheader("Time Range")
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
    
    # Create tabs for different comparison views
    tab1, tab2, tab3 = st.tabs(["Trend Comparison", "Multi-metric Analysis", "Average Comparison"])
    
    with tab1:
        st.subheader("Trend Comparison")
        selected_metric = st.selectbox(
            "Select Metric for Trend Comparison",
            options=metrics,
            format_func=lambda x: x.replace("_", " ").title()
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
            format_func=lambda x: x.replace("_", " ").title()
        )
        if selected_metrics:
            radar_fig = create_radar_chart(df, selected_sites, selected_metrics)
            st.plotly_chart(radar_fig, use_container_width=True)
        else:
            st.info("Please select at least one metric for comparison")
    
    with tab3:
        st.subheader("Average Values Comparison")
        selected_metric_avg = st.selectbox(
            "Select Metric for Average Comparison",
            options=metrics,
            format_func=lambda x: x.replace("_", " ").title(),
            key="avg_metric"
        )
        if selected_metric_avg:
            bar_fig = create_bar_comparison(df, selected_sites, selected_metric_avg)
            st.plotly_chart(bar_fig, use_container_width=True)
    
    # Summary statistics
    st.subheader("Summary Statistics")
    summary_data = []
    for site in selected_sites:
        site_data = df[df['site_name'] == site]
        summary = {
            'Site': site,
            'Average Recovery Rate': f"{site_data['recovery_rate'].mean():.2f}%",
            'Average Pressure': f"{site_data['pressure'].mean():.2f} psi",
            'Average Feed Flow': f"{site_data['flow-ID-001_feed'].mean():.2f} gpm"
        }
        summary_data.append(summary)
    
    st.dataframe(pd.DataFrame(summary_data), hide_index=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.stop()
