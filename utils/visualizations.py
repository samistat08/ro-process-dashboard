import plotly.graph_objects as go
import folium
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        site_df = df[df['site_name'] == site_name].copy()
        logger.info(f"Processing trends for site {site_name} with {len(site_df)} records")
        
        # Ensure timestamp is datetime
        site_df['timestamp'] = pd.to_datetime(site_df['timestamp'])
        
        # Daily aggregation using pd.Grouper
        daily_metrics = site_df.groupby(pd.Grouper(key='timestamp', freq='D')).agg({
            'recovery_rate': 'mean',
            'flow_rate': 'mean'
        }).reset_index()
        
        # Remove any NaN values
        daily_metrics = daily_metrics.dropna()
        
        # Debug print
        print(f"Number of data points: {len(daily_metrics)}")
        print("Date range:", daily_metrics['timestamp'].min(), "to", daily_metrics['timestamp'].max())
        
        # Create Recovery Rate trend plot
        fig_recovery = go.Figure()
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['recovery_rate'],
            mode='lines+markers',
            name='Recovery Rate',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig_recovery.update_layout(
            title='Daily Average Recovery Rate',
            xaxis_title='Date',
            yaxis_title='Recovery Rate (%)',
            xaxis=dict(
                type='date',
                tickformat='%Y-%m-%d %H:%M',
                tickangle=45,
                gridcolor='lightgrey',
                showgrid=True,
                tickmode='auto',
                nticks=10
            ),
            yaxis=dict(showgrid=True),
            showlegend=True,
            hovermode='x unified',
            height=400
        )
        
        # Create Flow Rate trend plot
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['flow_rate'],
            mode='lines+markers',
            name='Flow Rate',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))
        
        fig_flow.update_layout(
            title='Daily Average Flow Rate',
            xaxis_title='Date',
            yaxis_title='Flow Rate (m³/h)',
            xaxis=dict(
                type='date',
                tickformat='%Y-%m-%d %H:%M',
                tickangle=45,
                gridcolor='lightgrey',
                showgrid=True,
                tickmode='auto',
                nticks=10
            ),
            yaxis=dict(showgrid=True),
            showlegend=True,
            hovermode='x unified',
            height=400
        )
        
        return fig_recovery, fig_flow
        
    except Exception as e:
        logger.error(f"Error in create_kpi_trends: {str(e)}")
        raise

def create_performance_gauge(value, title):
    """Create gauge chart for performance metrics"""
    try:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "blue"},
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
