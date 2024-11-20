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
        color='#ff4444',
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
    "padding": "2rem",
}

# Create sidebar
sidebar = html.Div([
    # Logo
    html.Img(src='/assets/veolia-logo.svg', style={'width': '100%', 'margin-bottom': '2rem'}),
    
    # Pages section
    html.H6("Pages:", style={'margin-bottom': '1rem', 'color': '#333', 'font-weight': 'normal'}),
    dbc.Nav([
        dbc.NavLink("Site Map", href="/", id="page-1", style={'color': '#ff4444', 'padding': '0.2rem 0'}),
        dbc.NavLink("Overview", href="/overview", id="page-2", style={'color': '#333', 'padding': '0.2rem 0'}),
        dbc.NavLink("Site Performance", href="/performance", id="page-3", style={'color': '#333', 'padding': '0.2rem 0'})
    ],
    vertical=True,
    pills=False,
    style={'margin-bottom': '2rem', 'background': 'none'}
    ),
    
    html.Hr(),
    
    # Filters
    html.Div([
        html.Label("Date Filter", style={'margin-top': '1rem'}),
        dcc.DatePickerRange(id='date-filter'),
        html.Label("Site Filter", style={'margin-top': '1rem'}),
        dcc.Dropdown(
            id='site-filter',
            options=[{'label': site, 'value': site} for site in df['site_name'].unique()],
            multi=True,
            placeholder="Select sites..."
        )
    ])
], style=SIDEBAR_STYLE)

def create_gauge(value, title, site):
    colors = {
        'good': '#2ECC71',
        'warning': '#F1C40F',
        'danger': '#E74C3C'
    }
    
    if value < 60:
        color = colors['danger']
    elif value < 80:
        color = colors['warning']
    else:
        color = colors['good']
    
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': f"{title} - {site}"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 60], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [60, 80], 'color': 'rgba(241, 196, 15, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(46, 204, 113, 0.2)'}
            ]
        }
    )).update_layout(height=200, margin=dict(l=30, r=30, t=50, b=30))

def create_status_indicators(site_data):
    thresholds = {
        'membrane_fouling': lambda x: x['pressure'] > 500,
        'pump_faults': lambda x: x['flow-ID-001_feed'] < 40,
        'flow_imbalances': lambda x: abs(x['flow-ID-001_feed'] - x['flow-ID-001_product'] - x['flow-ID-001_waste']) > 5
    }
    
    status = {}
    for indicator, check in thresholds.items():
        status[indicator] = 'danger' if check(site_data.iloc[-1]) else 'success'
    
    return status

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

# Updated Overview layout
overview_layout = html.Div([
    html.H2("Overview", className="mb-4"),
    html.Div(id='overview-content')
])

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

@app.callback(
    Output('overview-content', 'children'),
    [Input('site-filter', 'value')]
)
def update_overview(selected_sites):
    if not selected_sites:
        return html.Div("Please select at least one site from the sidebar.", className="alert alert-info")
    
    if not isinstance(selected_sites, list):
        selected_sites = [selected_sites]
    
    content = []
    for site in selected_sites:
        site_data = df[df['site_name'] == site]
        if site_data.empty:
            continue
            
        # Create gauge charts row
        gauge_row = dbc.Row([
            dbc.Col(dcc.Graph(figure=create_gauge(
                site_data['recovery_rate'].iloc[-1],
                "Recovery rate",
                site
            )), width=6),
            dbc.Col(dcc.Graph(figure=create_gauge(
                site_data['pressure'].iloc[-1] / 10,  # Normalize pressure to 0-100 scale
                "Differential Pressure",
                site
            )), width=6),
        ], className="mb-4")
        
        # Create status indicators
        status = create_status_indicators(site_data)
        status_row = dbc.Row([
            html.H4(f"Site {site} Status", className="mb-3"),
            dbc.Col([
                html.Div([
                    html.I(className=f"fas fa-circle text-{status['membrane_fouling']}", style={'marginRight': '10px'}),
                    "Membrane Fouling"
                ], className="mb-2"),
                html.Div([
                    html.I(className=f"fas fa-circle text-{status['pump_faults']}", style={'marginRight': '10px'}),
                    "Pump or Motor Faults"
                ], className="mb-2"),
                html.Div([
                    html.I(className=f"fas fa-circle text-{status['flow_imbalances']}", style={'marginRight': '10px'}),
                    "Flow Imbalances"
                ], className="mb-2"),
            ])
        ], className="mb-4")
        
        content.extend([gauge_row, status_row, html.Hr()])
    
    return html.Div(content)

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
    [Output('page-1', 'style'),
     Output('page-2', 'style'),
     Output('page-3', 'style')],
    [Input('url', 'pathname')]
)
def update_nav_styles(pathname):
    styles = []
    for path in ['/', '/overview', '/performance']:
        if pathname == path:
            styles.append({'color': '#ff4444', 'padding': '0.2rem 0'})
        else:
            styles.append({'color': '#333', 'padding': '0.2rem 0'})
    return styles

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=False)
