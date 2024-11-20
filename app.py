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
    external_stylesheets=[dbc.themes.BOOTSTRAP, "https://use.fontawesome.com/releases/v5.15.4/css/all.css"],
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
        html.Div([  # Wrap site filter in div with ID
            html.Label("Site Filter", style={'margin-top': '1rem'}),
            dcc.Dropdown(
                id='site-filter',
                options=[{'label': site, 'value': site} for site in df['site_name'].unique()],
                multi=True,
                placeholder="Select sites..."
            )
        ], id='sidebar-site-filter')
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
        mode="gauge+number+delta",
        value=value,
        title={'text': f"{title} - {site}", 'font': {'size': 16}},
        number={'font': {'size': 24, 'color': color}, 'suffix': '%'},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 60], 'color': 'rgba(231, 76, 60, 0.2)'},
                {'range': [60, 80], 'color': 'rgba(241, 196, 15, 0.2)'},
                {'range': [80, 100], 'color': 'rgba(46, 204, 113, 0.2)'}
            ],
            'threshold': {
                'line': {'color': color, 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    )).update_layout(height=250, margin=dict(l=30, r=30, t=50, b=30))

def create_status_indicators(site_data):
    # Calculate values
    pressure_trend = site_data['pressure'].rolling(window=24).mean().diff()
    flow_difference = abs(site_data['flow-ID-001_feed'] - site_data['flow-ID-001_product'] - site_data['flow-ID-001_waste'])
    
    # Calculate status with specific values
    status = {
        'membrane_fouling': {
            'value': f"{pressure_trend.iloc[-1]:.2f} psi/day",
            'status': 'danger' if pressure_trend.iloc[-1] > 5 else 'success',
            'alert': "High membrane fouling rate detected" if pressure_trend.iloc[-1] > 5 else None
        },
        'pump_faults': {
            'value': f"{site_data['flow-ID-001_feed'].iloc[-1]:.1f} gpm",
            'status': 'danger' if site_data['flow-ID-001_feed'].iloc[-1] < 40 else 'success',
            'alert': "Low flow rate indicates possible pump fault" if site_data['flow-ID-001_feed'].iloc[-1] < 40 else None
        },
        'flow_imbalances': {
            'value': f"{flow_difference.iloc[-1]:.1f} gpm",
            'status': 'danger' if flow_difference.iloc[-1] > 5 else 'success',
            'alert': "Flow imbalance detected" if flow_difference.iloc[-1] > 5 else None
        }
    }
    return status

def create_kpi_section(title, metrics, site_data):
    site_data = site_data.copy()
    
    # Calculate derived metrics
    if 'pressure_differential' not in site_data.columns:
        site_data['pressure_differential'] = site_data['pressure'].diff().fillna(0)
    if 'specific_energy' not in site_data.columns:
        site_data['specific_energy'] = site_data['energy_consumption'] / site_data['flow-ID-001_product']
        
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.H4(title.replace('_', ' ').title(), className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H6(f"{metric_name}", className="kpi-title"),
                            html.H4(f"{site_data[metric_col].iloc[-1]:.1f} {unit}")
                        ], className="kpi-box mb-3")
                    ], width=6)
                    for metric_name, metric_col, unit in metrics
                ])
            ]),
            className="mb-4",
            style={"backgroundColor": "#fff1f1"}
        )
    ])

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

# Updated Performance layout with simplified filters
performance_layout = html.Div([
    html.H2("Site Performance", className="mb-4"),
    dbc.Row([
        dbc.Col([
            html.Label("Select Site:"),
            dcc.Dropdown(
                id='performance-site-select',
                options=[{'label': site, 'value': site} for site in sorted(df['site_name'].unique())],
                value=df['site_name'].iloc[0],
                multi=False
            )
        ], width=6),
        dbc.Col([
            html.Label("Select KPI Category:"),
            dcc.Dropdown(
                id='kpi-category-select',
                options=[
                    {'label': 'Operational Performance', 'value': 'operational'},
                    {'label': 'Pressure Metrics', 'value': 'pressure'},
                    {'label': 'Water Quality', 'value': 'water'},
                    {'label': 'Energy Metrics', 'value': 'energy'},
                    {'label': 'Maintenance Indicators', 'value': 'maintenance'}
                ],
                value='operational'
            )
        ], width=6)
    ], className="mb-4"),
    
    # Current Values section
    html.Div(id='current-kpi-values', className="mb-4"),
    
    # Trend Analysis section
    html.H3("Trend Analysis", className="mb-4"),
    html.Div(id='trend-plots')
])

@app.callback(
    Output('url', 'pathname'),
    [Input('world-map', 'clickData')],
)
def handle_map_click(clickData):
    if clickData:
        return '/performance'
    return dash.no_update

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
                    html.I(className=f"fas fa-circle text-{status['membrane_fouling']['status']}", 
                          style={'marginRight': '10px'}),
                    html.Span([
                        "Membrane Fouling: ",
                        html.B(status['membrane_fouling']['value'], 
                              style={'fontSize': '18px', 'color': '#333'})
                    ]),
                    html.Div(status['membrane_fouling']['alert'], 
                            className="alert alert-danger mt-1") if status['membrane_fouling']['alert'] else None
                ], className="mb-3"),
                html.Div([
                    html.I(className=f"fas fa-circle text-{status['pump_faults']['status']}", 
                          style={'marginRight': '10px'}),
                    html.Span([
                        "Pump/Motor Faults: ",
                        html.B(status['pump_faults']['value'],
                              style={'fontSize': '18px', 'color': '#333'})
                    ]),
                    html.Div(status['pump_faults']['alert'], 
                            className="alert alert-danger mt-1") if status['pump_faults']['alert'] else None
                ], className="mb-3"),
                html.Div([
                    html.I(className=f"fas fa-circle text-{status['flow_imbalances']['status']}", 
                          style={'marginRight': '10px'}),
                    html.Span([
                        "Flow Imbalances: ",
                        html.B(status['flow_imbalances']['value'],
                              style={'fontSize': '18px', 'color': '#333'})
                    ]),
                    html.Div(status['flow_imbalances']['alert'], 
                            className="alert alert-danger mt-1") if status['flow_imbalances']['alert'] else None
                ], className="mb-3"),
            ])
        ], className="mb-4")
        
        content.extend([gauge_row, status_row, html.Hr()])
    
    return html.Div(content)

# Define KPI categories globally
kpi_categories = {
    'operational': [
        ('Feedwater Flow Rate', 'flow-ID-001_feed', 'm³/h'),
        ('Permeate Flow Rate', 'flow-ID-001_product', 'm³/h'),
        ('Concentrate/Reject Flow Rate', 'flow-ID-001_waste', 'm³/h'),
        ('Recovery Rate', 'recovery_rate', '%')
    ],
    'pressure': [
        ('Feed Pressure', 'pressure', 'bar'),
        ('Differential Pressure', 'pressure_differential', 'bar'),
        ('Concentrate Pressure', 'pressure_concentrate', 'bar')
    ],
    'water': [
        ('Feedwater Conductivity', 'conductivity_feed', 'µS/cm'),
        ('Permeate Conductivity', 'conductivity_permeate', 'µS/cm'),
        ('Salt Rejection Rate', 'salt_rejection', '%')
    ],
    'energy': [
        ('Energy Consumption', 'energy_consumption', 'kWh'),
        ('Specific Energy Consumption', 'specific_energy', 'kWh/m³')
    ],
    'maintenance': [
        ('Normalized Permeate Flow', 'normalized_flow', 'm³/h'),
        ('Membrane Fouling Factor', 'fouling_factor', '%'),
        ('Scaling Index', 'scaling_index', '')
    ]
}

@app.callback(
    Output('current-kpi-values', 'children'),
    [Input('performance-site-select', 'value'),
     Input('kpi-category-select', 'value')]
)
def update_current_values(selected_site, selected_category):
    if not selected_site or not selected_category:
        return []
        
    site_data = df[df['site_name'] == selected_site].copy()
    if selected_category not in kpi_categories:
        return []
        
    metrics = kpi_categories[selected_category]
    
    # Filter out metrics that don't exist in the data
    available_metrics = [
        (metric_name, metric_col, unit) 
        for metric_name, metric_col, unit in metrics 
        if metric_col in site_data.columns
    ]
    
    if not available_metrics:
        return html.Div("No data available for selected category", className="alert alert-warning")
    
    return dbc.Card(
        dbc.CardBody([
            html.H4("Current Values", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6(f"{metric_name}", className="kpi-title"),
                        html.H4(f"{site_data[metric_col].iloc[-1]:.1f} {unit}")
                    ], className="kpi-box mb-3")
                ], width=6)
                for metric_name, metric_col, unit in available_metrics
            ])
        ]),
        className="mb-4",
        style={"backgroundColor": "#fff1f1"}
    )

@app.callback(
    Output('trend-plots', 'children'),
    [Input('performance-site-select', 'value'),
     Input('kpi-category-select', 'value')]
)
def update_trend_plots(selected_site, selected_category):
    if not selected_site or not selected_category:
        return []
        
    site_data = df[df['site_name'] == selected_site].copy()
    trend_plots = []
    
    if selected_category in kpi_categories:
        for metric_name, metric_col, unit in kpi_categories[selected_category]:
            if metric_col in site_data.columns:  # Check if column exists
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=site_data['timestamp'],
                    y=site_data[metric_col],
                    name=f"{metric_name} ({unit})"
                ))
                fig.update_layout(
                    title=metric_name,
                    height=300,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                trend_plots.append(dcc.Graph(figure=fig, className="mb-4"))
    
    return html.Div(trend_plots)

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

@app.callback(
    Output('sidebar-site-filter', 'style'),
    [Input('url', 'pathname')]
)
def toggle_site_filter(pathname):
    if pathname == '/performance':
        return {'display': 'none'}
    return {'display': 'block'}

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=5000, debug=False)