import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from utils.data_processor import load_data
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd

# Initialize Dash app with proper theme and configuration
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
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "250px",
    "padding": "0rem",
}

# Create sidebar
sidebar = html.Div(
    [
        html.Img(src='/assets/veolia-logo.svg', style={'width': '100%', 'margin-bottom': '2rem'}),
        html.H6("Pages:", className="text-muted"),
        dbc.Nav(
            [
                dbc.NavLink("Site Map", href="/", id="site-map-link", className="nav-link"),
                dbc.NavLink("Overview", href="/overview", id="overview-link", className="nav-link"),
                dbc.NavLink("Site Performance", href="/performance", id="performance-link", className="nav-link"),
            ],
            vertical=True,
            pills=True,
        ),
        html.Hr(),
        html.Div([
            html.Label("Date Filter", className="text-muted mb-2"),
            dcc.DatePickerRange(
                id='date-filter',
                start_date=df['timestamp'].min(),
                end_date=df['timestamp'].max(),
                className="mb-3"
            ),
            html.Label("Site Filter", className="text-muted mb-2"),
            dcc.Dropdown(
                id='site-filter',
                options=[{'label': site, 'value': site} for site in sorted(df['site_name'].unique())],
                multi=True,
                placeholder="Select sites...",
                className="mb-3"
            ),
        ])
    ],
    style=SIDEBAR_STYLE,
)

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
        style={'height': '100vh'}
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
    [Output('page-content', 'children'),
     Output('site-map-link', 'active'),
     Output('overview-link', 'active'),
     Output('performance-link', 'active')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/overview':
        return overview_layout, False, True, False
    elif pathname == '/performance':
        return performance_layout, False, False, True
    else:
        return map_layout, True, False, False

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

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Smart RO - V0</title>
        {%favicon%}
        {%css%}
        <style>
            .nav-link { color: #333; }
            .nav-link.active { background-color: #ff4444 !important; }
            .nav-link:hover { color: #ff4444; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    # Use port 5000 for Replit compatibility
    app.run_server(host='0.0.0.0', port=5000, debug=False)
