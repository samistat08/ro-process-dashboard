import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
import pandas as pd
import numpy as np
from datetime import datetime

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
        
        # Daily aggregation using timestamp
        daily_metrics = site_df.groupby(site_df['timestamp'].dt.date).agg({
            'recovery_rate': 'mean',
            'pressure': 'mean',
            'flow_rate': 'mean',
            'temperature': 'mean',
            'timestamp': 'last'  # Keep the last timestamp for proper time reference
        }).reset_index()
        
        # Ensure we have enough data points for visualization
        if len(daily_metrics) < 2:
            raise ValueError("Insufficient data points for trend visualization")
        
        # Recovery Rate Trend with smoothed line
        fig_recovery = go.Figure()
        
        # Add scatter points for actual values
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['recovery_rate'],
            mode='markers',
            name='Daily Values',
            marker=dict(size=8)
        ))
        
        # Add smoothed line
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['recovery_rate'].rolling(window=3, min_periods=1).mean(),
            mode='lines',
            name='Trend',
            line=dict(width=3, smoothing=1.3)
        ))
        
        fig_recovery.update_layout(
            title='Recovery Rate Trend (Daily Average)',
            xaxis_title='Date',
            yaxis_title='Recovery Rate (%)',
            hovermode='x unified',
            xaxis=dict(
                tickformat='%Y-%m-%d',
                tickmode='auto',
                nticks=10
            )
        )
        
        # Pressure vs Flow Rate with daily averages
        fig_pressure_flow = go.Figure()
        
        # Create color scale based on timestamps
        timestamp_nums = [(t - daily_metrics['timestamp'].min()).total_seconds() 
                         for t in daily_metrics['timestamp']]
        
        fig_pressure_flow.add_trace(go.Scatter(
            x=daily_metrics['pressure'],
            y=daily_metrics['flow_rate'],
            mode='markers',
            name='Daily Average',
            marker=dict(
                size=10,
                color=timestamp_nums,  # Use numerical timestamps for color
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Time Progress')
            )
        ))
        
        # Add trendline
        z = np.polyfit(daily_metrics['pressure'], daily_metrics['flow_rate'], 1)
        p = np.poly1d(z)
        x_range = np.linspace(daily_metrics['pressure'].min(), daily_metrics['pressure'].max(), 100)
        
        fig_pressure_flow.add_trace(go.Scatter(
            x=x_range,
            y=p(x_range),
            mode='lines',
            name='Trend Line',
            line=dict(color='red', dash='dash')
        ))
        
        fig_pressure_flow.update_layout(
            title='Pressure vs Flow Rate (Daily Average)',
            xaxis_title='Pressure (bar)',
            yaxis_title='Flow Rate (m³/h)',
            hovermode='closest'
        )
        
        return fig_recovery, fig_pressure_flow
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
