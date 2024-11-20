import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.data_processor import load_data
from datetime import datetime, timedelta

st.set_page_config(page_title="Site Details", page_icon="🏢", layout="wide")

def create_metric_chart(df, metric, site):
    """Create a time series chart for a specific metric"""
    fig = px.line(
        df,
        x='timestamp',
        y=metric,
        title=f'{metric} Over Time'
    )
    fig.update_layout(height=300)
    return fig

try:
    st.title("🏢 Site Details")
    
    # Load data
    df = load_data(use_real_time=True)
    
    if df.empty:
        st.error("No data available. Please check the data source.")
        st.stop()
    
    # Site selection
    selected_site = st.sidebar.selectbox(
        "Select Site",
        options=sorted(df['site_name'].unique())
    )
    
    # Time range selection
    time_options = {
        'Last Hour': timedelta(hours=1),
        'Last 24 Hours': timedelta(days=1),
        'Last Week': timedelta(days=7),
        'Last Month': timedelta(days=30),
        'All Time': None
    }
    
    selected_time = st.sidebar.selectbox(
        "Time Range",
        options=list(time_options.keys())
    )
    
    # Filter data
    site_data = df[df['site_name'] == selected_site]
    if time_options[selected_time]:
        cutoff_time = datetime.now() - time_options[selected_time]
        site_data = site_data[site_data['timestamp'] >= cutoff_time]
    
    # Display site information
    st.header(f"Site: {selected_site}")
    
    # Current metrics
    latest_data = site_data.iloc[-1] if not site_data.empty else pd.Series()
    col1, col2, col3, col4 = st.columns(4)
    
    if not site_data.empty:
        with col1:
            st.metric("Recovery Rate", f"{latest_data['recovery_rate']:.1f}%")
        with col2:
            st.metric("Pressure", f"{latest_data['pressure']:.1f} psi")
        with col3:
            st.metric("Flow Rate", f"{latest_data['flow-ID-001_feed']:.1f} gpm")
        with col4:
            st.metric("Temperature", f"{latest_data['temperature']:.1f}°C")
    
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Performance Metrics", "Flow Analysis", "Maintenance"])
        
        with tab1:
            metrics = {
                'pressure': 'Pressure (psi)',
                'temperature': 'Temperature (°C)',
                'recovery_rate': 'Recovery Rate (%)'
            }
            for metric, label in metrics.items():
                fig = create_metric_chart(site_data, metric, selected_site)
                fig.update_layout(
                    title=f"{label} Over Time",
                    yaxis_title=label
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Flow Analysis")
            flow_fig = go.Figure()
            
            # Add feed, product, and waste flows
            flow_types = {
                'flow-ID-001_feed': 'Feed Flow',
                'flow-ID-001_product': 'Product Flow',
                'flow-ID-001_waste': 'Waste Flow'
            }
            
            for flow, label in flow_types.items():
                flow_fig.add_trace(go.Scatter(
                    x=site_data['timestamp'],
                    y=site_data[flow],
                    name=label
                ))
            
            flow_fig.update_layout(
                title="Flow Rates Over Time",
                xaxis_title="Time",
                yaxis_title="Flow Rate (gpm)",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(flow_fig, use_container_width=True)
        
        with tab3:
            st.subheader("Maintenance Status")
            
            # Define thresholds
            thresholds = {
                'pressure': {'low': 480, 'high': 520, 'unit': 'psi'},
                'flow-ID-001_feed': {'low': 40, 'high': 60, 'unit': 'gpm'},
                'temperature': {'low': 20, 'high': 30, 'unit': '°C'}
            }
            
            # Check current values against thresholds
            maintenance_issues = []
            
            for metric, limits in thresholds.items():
                current_value = latest_data[metric]
                if current_value < limits['low']:
                    maintenance_issues.append(
                        f"Low {metric.replace('flow-ID-001_', '')}: "
                        f"{current_value:.1f} {limits['unit']}"
                    )
                elif current_value > limits['high']:
                    maintenance_issues.append(
                        f"High {metric.replace('flow-ID-001_', '')}: "
                        f"{current_value:.1f} {limits['unit']}"
                    )
            
            if maintenance_issues:
                st.warning("Maintenance Required")
                for issue in maintenance_issues:
                    st.write(f"⚠️ {issue}")
            else:
                st.success("All systems operating normally")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.stop()
