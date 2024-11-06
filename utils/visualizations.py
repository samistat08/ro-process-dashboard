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
            'pressure': 'mean',
            'flow_rate': 'mean',
            'temperature': 'mean'
        }).reset_index()
        
        # If we have less than 2 points, duplicate the last point
        if len(daily_metrics) == 1:
            last_point = daily_metrics.iloc[-1].copy()
            new_date = last_point['timestamp'] + pd.Timedelta(days=1)
            last_point['timestamp'] = new_date
            daily_metrics = pd.concat([daily_metrics, pd.DataFrame([last_point])], ignore_index=True)
        
        # Convert date column to datetime for proper plotting
        daily_metrics['timestamp'] = pd.to_datetime(daily_metrics['timestamp'])
        
        # Recovery Rate Trend with smoothed line
        fig_recovery = go.Figure()
        
        # Add scatter points for actual values
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=daily_metrics['recovery_rate'],
            mode='markers',
            name='Daily Values',
            marker=dict(
                size=8,
                color=list(range(len(daily_metrics))),  # Use sequential integers for color
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Time Progression')
            )
        ))
        
        # Update smoothing window based on available data
        smoothing_window = min(3, len(daily_metrics))
        if smoothing_window > 0:
            smoothed_values = daily_metrics['recovery_rate'].rolling(
                window=smoothing_window, 
                min_periods=1
            ).mean()
        else:
            smoothed_values = daily_metrics['recovery_rate']
        
        # Add smoothed line
        fig_recovery.add_trace(go.Scatter(
            x=daily_metrics['timestamp'],
            y=smoothed_values,
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
        
        # Add scatter points with time-based coloring
        fig_pressure_flow.add_trace(go.Scatter(
            x=daily_metrics['pressure'],
            y=daily_metrics['flow_rate'],
            mode='markers',
            name='Daily Average',
            marker=dict(
                size=10,
                color=list(range(len(daily_metrics))),  # Use sequential integers for color
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Time Progression')
            )
        ))
        
        # Add trendline if we have enough points
        if len(daily_metrics) >= 2:
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
