import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.data_processor import load_data, process_site_data, calculate_kpis

# Initialize the Dash app with bootstrap theme
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define threshold values for KPI health indicators
THRESHOLDS = {
    'pressure': {'low': 480, 'high': 520},
    'flow-ID-001_feed': {'low': 40, 'high': 60},
    'recovery_rate': {'low': 97, 'high': 99},
    'temperature': {'low': 20, 'high': 30},
    'pH': {'low': 6.5, 'high': 7.5}
}

def create_map(df):
    """Create interactive map with site markers"""
    fig = go.Figure()

    # Add site markers
    for _, site in df.groupby(['site_name', 'Latitude', 'Longitude']).first().iterrows():
        kpis = calculate_kpis(df, site['site_name'])
        
        # Create tooltip content
        tooltip = f"""
        <b>{site['site_name']}</b><br>
        Recovery Rate: {kpis['avg_recovery']:.1f}%<br>
        Pressure: {kpis['avg_pressure']:.1f} psi<br>
        Flow Rate: {kpis['avg_flow']:.1f} gpm<br>
        Last Updated: {kpis['last_updated']}
        """

        fig.add_trace(go.Scattergeo(
            lon=[site['Longitude']],
            lat=[site['Latitude']],
            text=[tooltip],
            mode='markers',
            marker=dict(
                size=12,
                color='blue',
                opacity=0.8,
                symbol='circle'
            ),
            hoverinfo='text',
            name=site['site_name']
        ))

    fig.update_layout(
        geo=dict(
            projection_type='equirectangular',
            showland=True,
            showcountries=True,
            countrycolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 230, 250)'
        ),
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )

    return fig

def create_kpi_indicators(df, site_name):
    """Create color-coded KPI indicators"""
    latest_data = df[df['site_name'] == site_name].iloc[-1]
    
    kpi_cards = []
    metrics = {
        'pressure': ('Pressure', 'psi'),
        'flow-ID-001_feed': ('Flow Rate', 'gpm'),
        'recovery_rate': ('Recovery Rate', '%'),
        'temperature': ('Temperature', '°C'),
        'pH': ('pH Level', '')
    }
    
    for metric, (label, unit) in metrics.items():
        value = latest_data[metric]
        thresholds = THRESHOLDS[metric]
        
        # Determine color based on thresholds
        if value < thresholds['low']:
            color = 'warning'
        elif value > thresholds['high']:
            color = 'danger'
        else:
            color = 'success'
            
        kpi_cards.append(
            dbc.Card([
                dbc.CardBody([
                    html.H6(label, className='card-title'),
                    html.H4(f"{value:.1f} {unit}", className=f"text-{color}"),
                ])
            ], className='mb-3')
        )
    
    return kpi_cards

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("RO Process Monitoring Dashboard", className='text-center mb-4'), width=12)
    ]),
    
    # Left Panel - Controls
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Time Range", className='mb-3'),
                    dcc.RadioItems(
                        id='time-range-preset',
                        options=[
                            {'label': ' Last 7 Days', 'value': '7d'},
                            {'label': ' Last 30 Days', 'value': '30d'},
                            {'label': ' Last 6 Months', 'value': '180d'},
                            {'label': ' Custom Range', 'value': 'custom'},
                        ],
                        value='7d',
                        className='mb-3'
                    ),
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=datetime(2024, 5, 17),
                        max_date_allowed=datetime(2024, 11, 12),
                        initial_visible_month=datetime(2024, 5, 17),
                        className='mb-3'
                    ),
                ])
            ], className='mb-4'),
            
            # Site Selection
            dbc.Card([
                dbc.CardBody([
                    html.H4("Site Selection", className='mb-3'),
                    dcc.Dropdown(
                        id='site-selector',
                        options=[
                            {'label': f'Site {site}', 'value': f'Site_{site}'}
                            for site in ['A', 'B', 'C']
                        ],
                        value='Site_A',
                        clearable=False
                    )
                ])
            ])
        ], width=3),
        
        # Main Content Area
        dbc.Col([
            # Map
            dbc.Card([
                dbc.CardBody([
                    html.H4("Site Locations", className='mb-3'),
                    dcc.Graph(id='site-map')
                ])
            ], className='mb-4'),
            
            # KPI Dashboard
            dbc.Card([
                dbc.CardBody([
                    html.H4("Key Performance Indicators", className='mb-3'),
                    dbc.Row(id='kpi-indicators')
                ])
            ], className='mb-4'),
            
            # Detailed Analysis Tabs
            dbc.Card([
                dbc.CardBody([
                    dcc.Tabs([
                        dcc.Tab(label='Time Series Analysis', children=[
                            dcc.Loading(
                                id='loading-time-series',
                                children=html.Div(id='time-series-graphs')
                            )
                        ]),
                        dcc.Tab(label='Performance Metrics', children=[
                            dcc.Loading(
                                id='loading-performance',
                                children=html.Div(id='performance-metrics')
                            )
                        ]),
                        dcc.Tab(label='Site Comparison', children=[
                            dcc.Loading(
                                id='loading-comparison',
                                children=html.Div(id='site-comparison')
                            )
                        ])
                    ])
                ])
            ])
        ], width=9)
    ])
], fluid=True)

# Callbacks
@app.callback(
    [Output('date-range', 'start_date'),
     Output('date-range', 'end_date')],
    Input('time-range-preset', 'value')
)
def update_date_range(preset):
    end_date = datetime.now()
    if preset == '7d':
        start_date = end_date - timedelta(days=7)
    elif preset == '30d':
        start_date = end_date - timedelta(days=30)
    elif preset == '180d':
        start_date = end_date - timedelta(days=180)
    else:
        return dash.no_update, dash.no_update
    return start_date.date(), end_date.date()

@app.callback(
    [Output('site-map', 'figure'),
     Output('kpi-indicators', 'children'),
     Output('time-series-graphs', 'children'),
     Output('performance-metrics', 'children'),
     Output('site-comparison', 'children')],
    [Input('site-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_dashboard(selected_site, start_date, end_date):
    try:
        # Load and filter data
        df = load_data()
        if df.empty:
            raise Exception("No data available")
            
        if start_date and end_date:
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
            
        # Create map
        map_fig = create_map(df)
        
        # Create KPI indicators
        kpi_cards = create_kpi_indicators(df, selected_site)
        
        # Create time series analysis
        time_series = []
        metrics = ['pressure', 'flow-ID-001_feed', 'recovery_rate', 'temperature', 'pH']
        for metric in metrics:
            fig = px.line(
                df[df['site_name'] == selected_site],
                x='timestamp',
                y=metric,
                title=f'{metric.replace("_", " ").title()} Over Time'
            )
            time_series.append(dcc.Graph(figure=fig))
            
        # Create performance metrics
        site_kpis = calculate_kpis(df, selected_site)
        performance_metrics = dbc.Table.from_dataframe(
            pd.DataFrame([site_kpis]),
            striped=True,
            bordered=True,
            hover=True
        )
        
        # Create site comparison
        comparison_fig = go.Figure()
        for site in df['site_name'].unique():
            site_data = df[df['site_name'] == site]
            comparison_fig.add_trace(go.Box(
                y=site_data['recovery_rate'],
                name=site,
                boxpoints='outliers'
            ))
        comparison_fig.update_layout(
            title='Recovery Rate Distribution by Site',
            yaxis_title='Recovery Rate (%)'
        )
        
        return map_fig, kpi_cards, time_series, performance_metrics, dcc.Graph(figure=comparison_fig)
        
    except Exception as e:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=5001)
