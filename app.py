import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Load data
def load_data():
    """Load data from CSV file"""
    try:
        df = pd.read_csv('RO_system_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

# Create the layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("RO Process Monitoring - Site Comparison", 
                className='text-center mb-4 mt-4'))
    ]),
    
    # Main content
    dbc.Row([
        # Left Panel - Controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('Sites'),
                    dcc.Checklist(
                        id='site-selector',
                        options=[
                            {'label': f' Site {chr(65+i)}', 'value': f'Site_{chr(65+i)}'}
                            for i in range(3)
                        ],
                        value=['Site_A', 'Site_B'],
                        className='mb-3'
                    ),
                    html.H4('Metrics'),
                    dcc.Checklist(
                        id='metric-selector',
                        options=[
                            {'label': ' Pressure (psi)', 'value': 'Pressure (psi)'},
                            {'label': ' Flow Rate (gpm)', 'value': 'Flow Rate (gpm)'},
                            {'label': ' Salt Rejection (%)', 'value': 'Salt Rejection (%)'},
                            {'label': ' Temperature (C)', 'value': 'Temperature (C)'},
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
                        html.H3('Site Performance Comparison'),
                        dcc.Loading(
                            id="loading-trends",
                            type="circle",
                            children=html.Div(id='trend-graphs')
                        )
                    ]))
                ]),
                dcc.Tab(label='Statistical Analysis', children=[
                    dbc.Card(dbc.CardBody([
                        html.H3('Statistical Comparison'),
                        dcc.Loading(
                            id="loading-stats",
                            type="circle",
                            children=html.Div(id='stats-graphs')
                        )
                    ]))
                ]),
                dcc.Tab(label='Correlation Analysis', children=[
                    dbc.Card(dbc.CardBody([
                        html.H3('Metric Correlations'),
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
        if df.empty:
            return html.Div("Error loading data. Please check the data source.")
            
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
                    name=f'{site} - Actual',
                    mode='lines+markers'
                ))
                
                if len(site_data) > 1:
                    x_numeric = np.arange(len(site_data))
                    y_array = site_data[metric].astype(float).to_numpy()
                    coefficients = np.polyfit(x_numeric, y_array, 1)
                    trend_line = np.poly1d(coefficients)
                    
                    fig.add_trace(go.Scatter(
                        x=site_data['Date'],
                        y=trend_line(x_numeric),
                        name=f'{site} - Trend',
                        line=dict(dash='dash')
                    ))
            
            fig.update_layout(
                title=f'{metric} Comparison',
                xaxis_title='Date',
                yaxis_title=metric,
                height=400,
                showlegend=True,
                hovermode='x unified'
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
        if df.empty:
            return html.Div("Error loading data. Please check the data source.")
            
        df_filtered = df[df['Site'].isin(selected_sites)]
        
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['Date'] >= start_date) & 
                (df_filtered['Date'] <= end_date)
            ]
        
        graphs = []
        
        # Box plots for distribution comparison
        for metric in selected_metrics:
            fig = go.Figure()
            for site in selected_sites:
                site_data = df_filtered[df_filtered['Site'] == site]
                fig.add_trace(go.Box(
                    y=site_data[metric].astype(float),
                    name=site,
                    boxpoints='outliers'
                ))
            
            fig.update_layout(
                title=f'{metric} Distribution by Site',
                yaxis_title=metric,
                height=400,
                showlegend=False
            )
            graphs.append(dcc.Graph(figure=fig))
        
        # Add summary statistics table
        stats_data = []
        for site in selected_sites:
            for metric in selected_metrics:
                site_data = df_filtered[df_filtered['Site'] == site][metric].astype(float)
                stats = {
                    'Site': site,
                    'Metric': metric,
                    'Mean': f"{site_data.mean():.2f}",
                    'Std Dev': f"{site_data.std():.2f}",
                    'Min': f"{site_data.min():.2f}",
                    'Max': f"{site_data.max():.2f}"
                }
                stats_data.append(stats)
        
        stats_df = pd.DataFrame(stats_data)
        stats_table = dbc.Table.from_dataframe(
            stats_df,
            striped=True,
            bordered=True,
            hover=True,
            className='mt-4'
        )
        
        graphs.append(html.Div([
            html.H4('Summary Statistics', className='mt-4'),
            stats_table
        ]))
        
        return graphs
    except Exception as e:
        return html.Div(f"Error generating statistical graphs: {str(e)}")

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
        if df.empty:
            return html.Div("Error loading data. Please check the data source.")
            
        df_filtered = df[df['Site'].isin(selected_sites)]
        
        if start_date and end_date:
            df_filtered = df_filtered[
                (df_filtered['Date'] >= start_date) & 
                (df_filtered['Date'] <= end_date)
            ]
        
        graphs = []
        
        # Correlation matrix for each site
        for site in selected_sites:
            site_data = df_filtered[df_filtered['Site'] == site]
            
            metric_arrays = [site_data[metric].astype(float).to_numpy() for metric in selected_metrics]
            metric_arrays = np.array(metric_arrays)
            corr_matrix = np.corrcoef(metric_arrays)
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix,
                x=selected_metrics,
                y=selected_metrics,
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
