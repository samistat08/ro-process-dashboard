import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from utils.data_processor import load_data
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd

# Initialize Dash app with proper theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    routes_pathname_prefix='/'
)

server = app.server  # Expose Flask server for Replit

# Load data
df = load_data()

# Create the map
fig = go.Figure(data=go.Scattergeo(
    lon=df['Longitude'],
    lat=df['Latitude'],
    text=df.apply(lambda row: f"{row['site_name']}<br>Recovery: {row['recovery_rate']:.1f}%<br>Pressure: {row['pressure']:.1f} psi", axis=1),
    mode='markers',
    marker=dict(
        size=12,
        color='red',
        opacity=0.8,
        symbol='circle'
    ),
    hoverinfo='text'
))

fig.update_layout(
    title="Smart RO - V0",
    title_x=0.5,
    geo=dict(
        projection_type='natural earth',
        showland=True,
        showcountries=True,
        showocean=True,
        countrycolor='rgb(240, 240, 240)',
        oceancolor='rgb(250, 250, 255)',
        landcolor='rgb(255, 255, 255)',
        center=dict(lon=0, lat=20),
        projection_scale=1.8
    ),
    height=900,
    margin=dict(l=0, r=0, t=30, b=0),
    showlegend=False,
)

# Sidebar style
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "250px",
    "padding": "2rem 1rem",
    "background-color": "#f0f0f0",
    "box-shadow": "2px 0px 5px rgba(0,0,0,0.1)"
}

CONTENT_STYLE = {
    "margin-left": "250px",
    "padding": "0",
}

# Create sidebar
sidebar = html.Div([
    # Logo
    html.Img(src='/assets/veolia-logo.svg', style={'width': '100%', 'margin-bottom': '2rem'}),
    
    # Pages section - simplified
    html.H6("Pages:", style={'margin-bottom': '1rem', 'color': '#333'}),
    html.Div([
        dcc.Link("Site Map", href="/", style={'color': '#ff4444', 'text-decoration': 'none', 'display': 'block'}),
        dcc.Link("Overview", href="/overview", style={'color': '#333', 'text-decoration': 'none', 'display': 'block'}),
        dcc.Link("Site Performance", href="/performance", style={'color': '#333', 'text-decoration': 'none', 'display': 'block'})
    ], style={'margin-bottom': '2rem'}),
    
    html.Hr(),
    
    # Filters
    html.Label("Date Filter", style={'color': '#333', 'display': 'block', 'margin-bottom': '0.5rem'}),
    dcc.DatePickerRange(
        id='date-filter',
        style={'margin-bottom': '1rem'}
    ),
    html.Label("Site Filter", style={'color': '#333', 'display': 'block', 'margin-bottom': '0.5rem'}),
    dcc.Dropdown(
        id='site-filter',
        style={'margin-bottom': '1rem'}
    )
], style=SIDEBAR_STYLE)

# Main app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar,
    html.Div(id='page-content', style=CONTENT_STYLE)
])

# Page layouts
map_layout = html.Div([
    dcc.Graph(
        id='world-map',
        figure=fig,
        style={'height': 'calc(100vh - 20px)'}
    )
])

def create_kpi_card(title, value, unit=""):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle mb-2 text-muted"),
            html.H4(f"{value}{unit}", className="card-title")
        ]),
        className="mb-3"
    )

overview_layout = html.Div([
    html.H2("Overview", className="mb-4"),
    dbc.Row([
        dbc.Col([
            create_kpi_card("Average Recovery Rate", f"{df['recovery_rate'].mean():.1f}", "%"),
        ], width=3),
        dbc.Col([
            create_kpi_card("Average Pressure", f"{df['pressure'].mean():.1f}", " psi"),
        ], width=3),
        dbc.Col([
            create_kpi_card("Average Flow Rate", f"{df['flow-ID-001_feed'].mean():.1f}", " gpm"),
        ], width=3),
        dbc.Col([
            create_kpi_card("Total Sites", len(df['site_name'].unique())),
        ], width=3),
    ])
])

def create_performance_charts(site_data):
    metrics = {
        'recovery_rate': 'Recovery Rate (%)',
        'pressure': 'Pressure (psi)',
        'flow-ID-001_feed': 'Feed Flow Rate (gpm)',
        'temperature': 'Temperature (°C)'
    }
    
    charts = []
    for metric, label in metrics.items():
        fig = px.line(site_data, x='timestamp', y=metric, title=label)
        fig.update_layout(height=300)
        charts.append(dcc.Graph(figure=fig, className="mb-4"))
    
    return charts

performance_layout = html.Div([
    html.H2("Site Performance", className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.Label("Select Site:"),
            dcc.Dropdown(
                id='performance-site-select',
                options=[{'label': site, 'value': site} for site in sorted(df['site_name'].unique())],
                value=df['site_name'].iloc[0]
            )
        ], width=6)
    ], className="mb-4"),
    html.Div(id='performance-charts')
])

# Callbacks
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/overview':
        return overview_layout
    elif pathname == '/performance':
        return performance_layout
    return map_layout

@app.callback(
    Output('performance-charts', 'children'),
    [Input('performance-site-select', 'value')]
)
def update_performance_charts(selected_site):
    if not selected_site:
        return []
    
    site_data = df[df['site_name'] == selected_site]
    return create_performance_charts(site_data)

@app.callback(
    Output('url', 'pathname'),
    [Input('world-map', 'clickData')]
)
def handle_map_click(clickData):
    if clickData:
        return '/performance'
    return dash.no_update

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=False)