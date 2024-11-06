import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
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
    try:
        # Debug logging
        logger.info(f"Total records before filtering: {len(df)}")
        
        site_df = df[df['site_name'] == site_name].copy()
        logger.info(f"Records for site {site_name}: {len(site_df)}")
        
        # Ensure timestamp is datetime
        site_df['timestamp'] = pd.to_datetime(site_df['timestamp'])
        
        # Print date range
        logger.info(f"Date range: {site_df['timestamp'].min()} to {site_df['timestamp'].max()}")
        
        # Daily aggregation without any additional filtering
        daily_metrics = site_df.groupby(site_df['timestamp'].dt.date).agg({
            'recovery_rate': 'mean',
            'flow_rate': 'mean'
        }).reset_index()
        
        logger.info(f"Daily aggregated points: {len(daily_metrics)}")
        
        # Convert date back to datetime for proper plotting
        daily_metrics['timestamp'] = pd.to_datetime(daily_metrics['timestamp'])
        
        # Create Recovery Rate trend plot
        fig_recovery = go.Figure()
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['recovery_rate'],
            mode='lines+markers',
            name='Recovery Rate',
            line=dict(color='blue', width=2),
            marker=dict(color='blue', size=8)
        ))
        
        fig_recovery.update_layout(
            title='Daily Average Recovery Rate',
            xaxis_title='Date',
            yaxis_title='Recovery Rate (%)',
            xaxis=dict(
                type='date',
                tickformat='%Y-%m-%d',
                dtick='D1',  # Show daily ticks
                showgrid=True
            ),
            yaxis=dict(showgrid=True),
            showlegend=False,
            hovermode='x unified'
        )
        
        # Create Flow Rate trend plot
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['flow_rate'],
            mode='lines+markers',
            name='Flow Rate',
            line=dict(color='green', width=2),
            marker=dict(color='green', size=8)
        ))
        
        fig_flow.update_layout(
            title='Daily Average Flow Rate',
            xaxis_title='Date',
            yaxis_title='Flow Rate (m³/h)',
            xaxis=dict(
                type='date',
                tickformat='%Y-%m-%d',
                dtick='D1',  # Show daily ticks
                showgrid=True
            ),
            yaxis=dict(showgrid=True),
            showlegend=False,
            hovermode='x unified'
        )
        
        return fig_recovery, fig_flow
        
    except Exception as e:
        logger.error(f"Error in create_kpi_trends: {str(e)}")
        raise Exception(f"Error creating KPI trends: {str(e)}")

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
