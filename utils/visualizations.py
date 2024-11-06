import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins
import pandas as pd

def create_world_map(sites_data):
    """Create interactive world map with site markers"""
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

def create_kpi_trends(df, site_name):
    """Create KPI trend visualizations with daily aggregation"""
    site_df = df[df['site_name'] == site_name].copy()
    
    # Convert timestamp to date for daily aggregation
    site_df['date'] = site_df['timestamp'].dt.date
    
    # Daily aggregation
    daily_metrics = site_df.groupby('date').agg({
        'recovery_rate': 'mean',
        'pressure': 'mean',
        'flow_rate': 'mean',
        'temperature': 'mean'
    }).reset_index()
    
    # Convert date back to datetime for better plotting
    daily_metrics['date'] = pd.to_datetime(daily_metrics['date'])
    
    # Recovery Rate Trend with smoothed line
    fig_recovery = go.Figure()
    
    # Add scatter points for actual values
    fig_recovery.add_trace(go.Scatter(
        x=daily_metrics['date'],
        y=daily_metrics['recovery_rate'],
        mode='markers',
        name='Daily Values',
        marker=dict(size=8)
    ))
    
    # Add smoothed line
    fig_recovery.add_trace(go.Scatter(
        x=daily_metrics['date'],
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
    
    fig_pressure_flow.add_trace(go.Scatter(
        x=daily_metrics['pressure'],
        y=daily_metrics['flow_rate'],
        mode='markers',
        name='Daily Average',
        marker=dict(
            size=10,
            color=daily_metrics['date'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Date')
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

def create_performance_gauge(value, title):
    """Create gauge chart for performance metrics"""
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
