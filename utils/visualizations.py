import plotly.express as px
import plotly.graph_objects as go
import folium
from folium import plugins

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
    """Create KPI trend visualizations"""
    site_df = df[df['site_name'] == site_name].copy()
    
    # Recovery Rate Trend
    fig_recovery = px.line(
        site_df,
        x='timestamp',
        y='recovery_rate',
        title='Recovery Rate Trend'
    )
    
    # Pressure vs Flow Rate
    fig_pressure_flow = px.scatter(
        site_df,
        x='pressure',
        y='flow_rate',
        title='Pressure vs Flow Rate',
        trendline="ols"
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
