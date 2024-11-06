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
        
        # Add site markers with updated flow rate columns
        for _, site in sites_data.iterrows():
            folium.Marker(
                location=[site['latitude'], site['longitude']],
                popup=f"""
                    <b>{site['site_name']}</b><br>
                    Recovery Rate: {site['recovery_rate']:.1f}%<br>
                    Feed Flow: {site['flow-ID-001_feed']:.1f} m³/h<br>
                    Product Flow: {site['flow-ID-001_product']:.1f} m³/h<br>
                    Waste Flow: {site['flow-ID-001_waste']:.1f} m³/h
                """,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
        
        return m
    except Exception as e:
        logger.error(f"Error in create_world_map: {str(e)}")
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
            'flow-ID-001_feed': 'mean',    # Feed water flow
            'flow-ID-001_product': 'mean', # Product water flow
            'flow-ID-001_waste': 'mean',   # Waste water flow
            'recovery_rate': 'mean'
        }).reset_index()
        
        # Remove any NaN values
        daily_metrics = daily_metrics.dropna()
        
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
        
        # Create combined Flow Rate trend plot
        fig_flow = go.Figure()

        # Add Feed Flow
        fig_flow.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['flow-ID-001_feed'],
            mode='lines+markers',
            name='Feed Flow',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))

        # Add Product Flow
        fig_flow.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['flow-ID-001_product'],
            mode='lines+markers',
            name='Product Flow',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))

        # Add Waste Flow
        fig_flow.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['flow-ID-001_waste'],
            mode='lines+markers',
            name='Waste Flow',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ))

        fig_flow.update_layout(
            title='Daily Average Flow Rates',
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
            height=400,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
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
