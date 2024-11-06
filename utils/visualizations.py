import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_world_map(sites_data):
    """Create interactive world map with site markers"""
    try:
        # Initialize map centered at mean coordinates
        center_lat = sites_data['latitude'].mean()
        center_lon = sites_data['longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=2)
        
        # Add site markers
        for _, site in sites_data.iterrows():
            folium.Marker(
                location=[site['latitude'], site['longitude']],
                popup=f"""
                    <b>{site['site_name']}</b><br>
                    Recovery Rate: {site['recovery_rate']:.1f}%<br>
                    Flow Rate: {site['flow_rate']:.1f} m³/h
                """,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        return m
    except Exception as e:
        raise Exception(f"Error creating world map: {str(e)}")

def create_kpi_trends(df, site_name):
    """Create KPI trend visualizations with daily aggregation"""
    try:
        if df.empty:
            raise ValueError("No data available for visualization")
            
        site_df = df[df['site_name'] == site_name].copy()
        
        if site_df.empty:
            raise ValueError(f"No data available for site: {site_name}")
        
        # Ensure timestamp is datetime
        site_df['timestamp'] = pd.to_datetime(site_df['timestamp'])
        
        # Daily aggregation
        daily_metrics = site_df.groupby(site_df['timestamp'].dt.date).agg({
            'recovery_rate': 'mean',
            'flow_rate': 'mean'
        }).reset_index()
        
        # Convert timestamp to datetime for proper plotting
        daily_metrics['timestamp'] = pd.to_datetime(daily_metrics['timestamp'])
        
        # Create Recovery Rate trend plot
        fig_recovery = go.Figure()
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['recovery_rate'],
            mode='lines+markers',
            name='Daily Values',
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        fig_recovery.update_layout(
            title='Recovery Rate Trend',
            xaxis_title='Date',
            yaxis_title='Recovery Rate (%)',
            xaxis=dict(
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=10
            ),
            hovermode='x unified'
        )
        
        # Create Flow Rate trend plot
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['flow_rate'],
            mode='lines+markers',
            name='Daily Values',
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        fig_flow.update_layout(
            title='Flow Rate Trend',
            xaxis_title='Date',
            yaxis_title='Flow Rate (m³/h)',
            xaxis=dict(
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=10
            ),
            hovermode='x unified'
        )
        
        return fig_recovery, fig_flow
    except Exception as e:
        raise Exception(f"Error creating KPI trends: {str(e)}")

def create_performance_gauge(value, title):
    """Create gauge chart for performance metrics"""
    try:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            title = {'text': title},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "gray"},
                    {'range': [75, 100], 'color': "darkgray"}
                ]
            }
        ))
        
        return fig
    except Exception as e:
        raise Exception(f"Error creating performance gauge: {str(e)}")
