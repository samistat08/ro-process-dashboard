import streamlit as st
from utils.data_processor import load_data
import plotly.graph_objects as go
import plotly.express as px

# Configure the page with minimal padding
st.set_page_config(
    page_title="Smart RO - V0",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for clean layout
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    .main {
        padding: 0rem;
    }
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
        padding-left: 0;
        padding-right: 0;
    }
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        box-shadow: 2px 0px 5px rgba(0,0,0,0.1);
        padding: 1rem;
    }
    
    /* Navigation styling */
    .nav-link {
        color: #333;
        padding: 0.5rem 1rem;
        margin: 0.2rem 0;
        border-radius: 0.25rem;
    }
    .nav-link:hover {
        background-color: #f8f9fa;
        color: #ff4444;
    }
    .nav-link.active {
        background-color: #ff4444 !important;
        color: white !important;
    }
    
    /* Filter styling */
    .filter-label {
        color: #666;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    /* Remove padding from containers */
    .element-container {
        padding: 0 !important;
    }
    .stPlotlyChart {
        padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
df = load_data(use_real_time=True)

# Sidebar content
with st.sidebar:
    # Logo at the top
    st.image('assets/veolia-logo.svg', use_column_width=True)
    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
    
    # Site filter directly under logo
    st.markdown("<div class='filter-label'>Site Filter</div>", unsafe_allow_html=True)
    sites = sorted(df['site_name'].unique())
    selected_sites = st.multiselect('', sites, default=sites, key='sites')
    
    st.markdown("<div style='margin: 1rem 0;'><hr></div>", unsafe_allow_html=True)
    
    # Date filter below
    st.markdown("<div class='filter-label'>Date Filter</div>", unsafe_allow_html=True)
    dates = df['timestamp'].dt.date.unique()
    start_date = st.date_input('Start Date', min(dates), key='start_date')
    end_date = st.date_input('End Date', max(dates), key='end_date')

# Filter data based on selection
mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
filtered_df = df[mask]
if selected_sites:
    filtered_df = filtered_df[filtered_df['site_name'].isin(selected_sites)]

# Create the map with clean styling
fig = go.Figure(data=go.Scattergeo(
    lon=filtered_df['Longitude'],
    lat=filtered_df['Latitude'],
    text=filtered_df.apply(lambda row: f"{row['site_name']}<br>Recovery: {row['recovery_rate']:.1f}%<br>Pressure: {row['pressure']:.1f} psi", axis=1),
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
    title=None,
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
    height=800,
    margin=dict(l=0, r=0, t=0, b=0),
    showlegend=False,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

# Display the map with full width
st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
