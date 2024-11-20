import streamlit as st
from utils.data_processor import load_data
import plotly.graph_objects as go
import plotly.express as px

# Configure the page
st.set_page_config(
    page_title="Smart RO - V0",
    page_icon="💧",
    layout="wide"
)

# Add custom CSS to match the requested styling
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    .main {
        padding: 0rem;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f0f0f0;
        box-shadow: 2px 0px 5px rgba(0,0,0,0.1);
        padding: 2rem 1rem;
    }
    /* Navigation styling */
    .nav-link {
        color: #333;
        font-weight: 500;
        padding: 0.5rem 1rem;
        margin: 0.2rem 0;
        border-radius: 0.25rem;
    }
    .nav-link:hover {
        background-color: #f8f9fa;
        color: #ff4444;
        text-decoration: none;
    }
    .nav-link.active {
        background-color: #ff4444 !important;
        color: white !important;
    }
    /* Clean filters look */
    .stSelectbox, .stMultiSelect {
        background-color: white;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
df = load_data(use_real_time=True)

# Sidebar content
with st.sidebar:
    st.image('assets/veolia-logo.svg', use_column_width=True)
    st.markdown("<h6 style='color: #666; margin-bottom: 1rem;'>Pages:</h6>", unsafe_allow_html=True)
    
    # Create navigation menu
    selected_page = st.radio(
        "",
        ["Site Map", "Overview", "Site Performance"],
        label_visibility="collapsed",
        key="navigation"
    )
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Filters section
    st.markdown("<h6 style='color: #666; margin-bottom: 1rem;'>Filters</h6>", unsafe_allow_html=True)
    
    # Date filter
    dates = df['timestamp'].dt.date.unique()
    start_date = st.date_input('Start Date', min(dates))
    end_date = st.date_input('End Date', max(dates))
    
    # Site filter
    sites = sorted(df['site_name'].unique())
    selected_sites = st.multiselect('Select Sites', sites, default=sites)

# Filter data based on selection
mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
filtered_df = df[mask]
if selected_sites:
    filtered_df = filtered_df[filtered_df['site_name'].isin(selected_sites)]

# Create the map
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
    height=800,
    margin=dict(l=0, r=0, t=30, b=0),
    showlegend=False,
)

# Display the map
st.plotly_chart(fig, use_container_width=True)
