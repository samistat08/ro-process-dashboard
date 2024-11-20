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

# Add custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
    }
    .main {
        padding: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
df = load_data(use_real_time=True)

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
    height=800,
    margin=dict(l=0, r=0, t=30, b=0),
    showlegend=False,
)

# Main page content
st.sidebar.image('assets/veolia-logo.svg', use_column_width=True)

# Date filter in sidebar
st.sidebar.header('Filters')
dates = df['timestamp'].dt.date.unique()
start_date = st.sidebar.date_input('Start Date', min(dates))
end_date = st.sidebar.date_input('End Date', max(dates))

# Site filter in sidebar
sites = sorted(df['site_name'].unique())
selected_sites = st.sidebar.multiselect('Select Sites', sites, default=sites)

# Filter data based on selection
mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
filtered_df = df[mask]
if selected_sites:
    filtered_df = filtered_df[filtered_df['site_name'].isin(selected_sites)]

# Update map with filtered data
fig.data[0].lon = filtered_df['Longitude']
fig.data[0].lat = filtered_df['Latitude']
fig.data[0].text = filtered_df.apply(
    lambda row: f"{row['site_name']}<br>Recovery: {row['recovery_rate']:.1f}%<br>Pressure: {row['pressure']:.1f} psi",
    axis=1
)

# Display the map
st.plotly_chart(fig, use_container_width=True)
