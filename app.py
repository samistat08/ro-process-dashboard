import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define threshold values for KPI health indicators
THRESHOLDS = {
    'pressure': {'low': 480, 'high': 520},
    'flow_rate': {'low': 40, 'high': 60},
    'salt_rejection': {'low': 97, 'high': 99},
    'temperature': {'low': 20, 'high': 30},
    'ph_level': {'low': 6.5, 'high': 7.5}
}

def load_data():
    """Load data from CSV file"""
    try:
        df = pd.read_csv('RO_system_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def create_map(df):
    """Create interactive map with site markers"""
    try:
        fig = go.Figure()
        
        for site in df['Site'].unique():
            site_data = df[df['Site'] == site].iloc[-1]
            fig.add_trace(go.Scattergeo(
                lon=[site_data['Longitude']],
                lat=[site_data['Latitude']],
                text=[f"<b>{site}</b>"],
                mode='markers',
                marker=dict(
                    size=15,
                    color='blue',
                    opacity=0.8,
                    symbol='circle'
                ),
                hoverinfo='text',
                name=site
            ))
        
        fig.update_layout(
            geo=dict(
                projection_type='equirectangular',
                showland=True,
                showcountries=True,
                countrycolor='rgb(204, 204, 204)',
                showocean=True,
                oceancolor='rgb(230, 230, 250)',
                center=dict(lon=0, lat=20),
                projection_scale=1.5
            ),
            height=500,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False
        )
        
        return fig
    except Exception as e:
        print(f"Error creating map: {str(e)}")
        return go.Figure()

def create_site_kpi_cards(df, site):
    """Create KPI cards for a site"""
    site_data = df[df['Site'] == site].iloc[-1]
    
    # Calculate recovery rate
    recovery_rate = site_data['Salt Rejection (%)']
    
    # Determine maintenance state
    needs_maintenance = (
        site_data['Pressure (psi)'] > THRESHOLDS['pressure']['high'] or
        site_data['Flow Rate (gpm)'] < THRESHOLDS['flow_rate']['low'] or
        recovery_rate < THRESHOLDS['salt_rejection']['low']
    )
    
    # Create KPI card
    return dbc.Card([
        dbc.CardHeader(site, className='h5'),
        dbc.CardBody([
            html.Div([
                html.H6("Recovery Rate"),
                html.H4(f"{recovery_rate:.1f}%", 
                       className=f"text-{'success' if recovery_rate > 97 else 'warning'}")
            ], className='mb-3'),
            html.Div([
                html.H6("Maintenance Status"),
                html.H4("Maintenance Required" if needs_maintenance else "Operating Normally",
                       className=f"text-{'danger' if needs_maintenance else 'success'}")
            ], className='mb-3'),
            html.Div([
                html.H6("Current Performance"),
                dbc.Progress(
                    value=min(100, (recovery_rate - 90) * 10),
                    color="success" if recovery_rate > 97 else "warning",
                    className="mb-3",
                )
            ])
        ])
    ], className='mb-4')

# Load initial data
df = load_data()

# Create the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("RO Process Monitoring Dashboard", className='text-center mb-4'), width=12)
    ]),
    
    # World Map
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Site Locations", className='mb-3'),
                    dcc.Graph(id='site-map', style={'height': '60vh'})
                ])
            ], className='mb-4')
        ], width=12)
    ]),
    
    # KPI Overview
    dbc.Row([
        dbc.Col([
            html.H4("Site Performance Overview", className='mb-3'),
            dbc.Row(id='site-kpi-cards')
        ], width=12)
    ], className='mb-4'),
    
    # Controls and Analysis
    dbc.Row([
        # Left Panel - Controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Sites'),
                    dcc.Checklist(
                        id='site-selector',
                        options=[
                            {'label': ' Site A', 'value': 'Site_A'},
                            {'label': ' Site B', 'value': 'Site_B'},
                            {'label': ' Site C', 'value': 'Site_C'}
                        ],
                        value=['Site_A', 'Site_B'],
                        className='mb-3'
                    ),
                    html.H4('Metrics'),
                    dcc.Checklist(
                        id='metric-selector',
                        options=[
                            {'label': ' Pressure', 'value': 'Pressure (psi)'},
                            {'label': ' Flow Rate', 'value': 'Flow Rate (gpm)'},
                            {'label': ' Salt Rejection', 'value': 'Salt Rejection (%)'},
                            {'label': ' Temperature', 'value': 'Temperature (C)'},
                            {'label': ' pH Level', 'value': 'pH Level'}
                        ],
                        value=['Pressure (psi)', 'Flow Rate (gpm)'],
                        className='mb-3'
                    ),
                    html.H4('Date Range'),
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=datetime(2024, 5, 17),
                        max_date_allowed=datetime(2024, 6, 23),
                        start_date=datetime(2024, 5, 17),
                        end_date=datetime(2024, 6, 23),
                        className='mb-3'
                    )
                ])
            ], className='mb-4')
        ], width=3),
        
        # Main Content Area
        dbc.Col([
            dcc.Tabs([
                dcc.Tab(label='Performance Trends', children=[
                    dbc.Card(dbc.CardBody([
                        dcc.Loading(
                            id="loading-trends",
                            type="circle",
                            children=html.Div(id='trend-graphs')
                        )
                    ]))
                ]),
                dcc.Tab(label='Statistical Analysis', children=[
                    dbc.Card(dbc.CardBody([
                        dcc.Loading(
                            id="loading-stats",
                            type="circle",
                            children=html.Div(id='stats-graphs')
                        )
                    ]))
                ]),
                dcc.Tab(label='Correlation Analysis', children=[
                    dbc.Card(dbc.CardBody([
                        dcc.Loading(
                            id="loading-correlation",
                            type="circle",
                            children=html.Div(id='correlation-graphs')
                        )
                    ]))
                ])
            ])
        ], width=9)
    ])
], fluid=True)

# Callbacks
@app.callback(
    Output('site-map', 'figure'),
    [Input('site-selector', 'value')]
)
def update_map(selected_sites):
    if not selected_sites:
        return create_map(df)
    filtered_df = df[df['Site'].isin(selected_sites)]
    return create_map(filtered_df)

@app.callback(
    Output('site-kpi-cards', 'children'),
    [Input('site-selector', 'value')]
)
def update_kpi_cards(selected_sites):
    if not selected_sites:
        return []
    
    cards = []
    for site in selected_sites:
        cards.append(dbc.Col(
            create_site_kpi_cards(df, site),
            width=12 // len(selected_sites)
        ))
    return cards

@app.callback(
    Output('trend-graphs', 'children'),
    [Input('site-selector', 'value'),
     Input('metric-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_trend_graphs(selected_sites, selected_metrics, start_date, end_date):
    if not selected_sites or not selected_metrics:
        return html.Div("Please select at least one site and metric")
    
    try:
        df_filtered = df[df['Site'].isin(selected_sites)]
        
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['Date'] >= start_date) & 
                (df_filtered['Date'] <= end_date)
            ]
        
        graphs = []
        for metric in selected_metrics:
            fig = go.Figure()
            
            for site in selected_sites:
                site_data = df_filtered[df_filtered['Site'] == site]
                fig.add_trace(go.Scatter(
                    x=site_data['Date'],
                    y=site_data[metric],
                    name=site,
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title=f'{metric} Over Time',
                xaxis_title='Date',
                yaxis_title=metric,
                height=400,
                showlegend=True
            )
            
            graphs.append(dcc.Graph(figure=fig))
        
        return graphs
    except Exception as e:
        return html.Div(f"Error generating trend graphs: {str(e)}")

@app.callback(
    Output('stats-graphs', 'children'),
    [Input('site-selector', 'value'),
     Input('metric-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_stats_graphs(selected_sites, selected_metrics, start_date, end_date):
    if not selected_sites or not selected_metrics:
        return html.Div("Please select at least one site and metric")
    
    try:
        df_filtered = df[df['Site'].isin(selected_sites)]
        
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['Date'] >= start_date) & 
                (df_filtered['Date'] <= end_date)
            ]
        
        stats_data = []
        for site in selected_sites:
            for metric in selected_metrics:
                site_data = df_filtered[df_filtered['Site'] == site][metric]
                stats = {
                    'Site': site,
                    'Metric': metric,
                    'Mean': f"{site_data.mean():.2f}",
                    'Std Dev': f"{site_data.std():.2f}",
                    'Min': f"{site_data.min():.2f}",
                    'Max': f"{site_data.max():.2f}"
                }
                stats_data.append(stats)
        
        return dbc.Table.from_records(
            stats_data,
            striped=True,
            bordered=True,
            hover=True
        )
    except Exception as e:
        return html.Div(f"Error generating statistics: {str(e)}")

@app.callback(
    Output('correlation-graphs', 'children'),
    [Input('site-selector', 'value'),
     Input('metric-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_correlation_graphs(selected_sites, selected_metrics, start_date, end_date):
    if not selected_sites or not selected_metrics or len(selected_metrics) < 2:
        return html.Div("Please select at least two metrics for correlation analysis")
    
    try:
        df_filtered = df[df['Site'].isin(selected_sites)]
        
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['Date'] >= start_date) & 
                (df_filtered['Date'] <= end_date)
            ]
        
        graphs = []
        for site in selected_sites:
            site_data = df_filtered[df_filtered['Site'] == site]
            
            corr_matrix = site_data[selected_metrics].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmin=-1,
                zmax=1
            ))
            
            fig.update_layout(
                title=f'Correlation Matrix - {site}',
                height=500
            )
            
            graphs.append(dcc.Graph(figure=fig))
        
        return graphs
    except Exception as e:
        return html.Div(f"Error generating correlation graphs: {str(e)}")

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000)
