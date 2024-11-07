import streamlit as st
import pandas as pd
from utils.data_processor import load_data, calculate_kpis
from utils.visualizations import create_kpi_trends, create_performance_gauge
from utils.predictive_maintenance import MaintenancePredictor
# from utils.export_utils import export_data_to_csv, export_plot_to_html, get_download_link

def render_maintenance_alerts(site_df):
    """Render maintenance alerts section"""
    predictor = MaintenancePredictor()
    maintenance_info = predictor.predict_maintenance_needs(site_df)
    
    # Display status with appropriate color
    status_colors = {
        'normal': 'green',
        'attention': 'blue',
        'warning': 'orange',
        'critical': 'red'
    }
    
    st.subheader("🔔 Maintenance Alerts")
    status_color = status_colors.get(maintenance_info['status'], 'gray')
    st.markdown(f"<h3 style='color: {status_color};'>Status: {maintenance_info['status'].upper()}</h3>", unsafe_allow_html=True)
    
    # Display next maintenance date
    st.write("Next Recommended Maintenance:", maintenance_info['next_maintenance'].strftime("%Y-%m-%d"))
    
    # Display alerts if any
    if maintenance_info['alerts']:
        st.write("Active Alerts:")
        for alert in maintenance_info['alerts']:
            with st.expander(f"{alert['parameter']} - {alert['message']}"):
                st.write(f"Severity: {alert['severity'].upper()}")
                st.write(f"Recommendation: {alert['recommendation']}")
    else:
        st.success("No active alerts - System operating normally")
    
    # Export maintenance report
    # if st.button("Export Maintenance Report"):
    #     report_data = pd.DataFrame({
    #         'Status': [maintenance_info['status']],
    #         'Next Maintenance': [maintenance_info['next_maintenance'].strftime("%Y-%m-%d")],
    #         'Alert Count': [len(maintenance_info['alerts'])]
    #     })
    #     href, filename = export_data_to_csv(report_data, "maintenance_report")
    #     st.markdown(
    #         get_download_link(href, filename, "📥 Download Maintenance Report (CSV)"),
    #         unsafe_allow_html=True
    #     )

def render_site_details():
    st.title("Site Details Analysis")
    
    # Get selected site from session state
    if 'selected_site' not in st.session_state:
        st.warning("Please select a site from the main dashboard")
        return
    
    site_name = st.session_state['selected_site']
    st.header(f"📍 {site_name}")
    
    # Load data
    df = load_data(use_real_time=True)  # Enable real-time data
    site_df = df[df['site_name'] == site_name].copy()
    
    # Calculate KPIs
    kpis = calculate_kpis(df, site_name)
    
    # Create layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Recovery Rate", f"{kpis['avg_recovery']:.1f}%")
    with col2:
        st.metric("Average Pressure", f"{kpis['avg_pressure']:.1f} bar")
    with col3:
        st.metric("Average Flow", f"{kpis['avg_flow']:.1f} m³/h")
    
    # Export KPI data
    # if st.button("Export KPI Data"):
    #     kpi_df = pd.DataFrame([kpis])
    #     href, filename = export_data_to_csv(kpi_df, f"{site_name}_kpi_data")
    #     st.markdown(
    #         get_download_link(href, filename, "📥 Download KPI Data (CSV)"),
    #         unsafe_allow_html=True
    #     )
    
    # Maintenance Alerts Section
    render_maintenance_alerts(site_df)
    
    # Performance Score Gauge
    st.subheader("Overall Performance Score")
    gauge_fig = create_performance_gauge(
        kpis['efficiency_score'],
        "Efficiency Score"
    )
    st.plotly_chart(gauge_fig, use_container_width=True)
    
    # Export performance visualization
    # if st.button("Export Performance Gauge"):
    #     href, filename = export_plot_to_html(gauge_fig, f"{site_name}_performance_gauge")
    #     st.markdown(
    #         get_download_link(href, filename, "📥 Download Performance Gauge (HTML)"),
    #         unsafe_allow_html=True
    #     )
    
    # Trend Analysis
    st.subheader("Trend Analysis")
    fig_recovery, fig_flow = create_kpi_trends(df, site_name)
    
    # Create two columns for plots
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_recovery, use_container_width=True)
        # if st.button("Export Recovery Trend"):
        #     href, filename = export_plot_to_html(fig_recovery, f"{site_name}_recovery_trend")
        #     st.markdown(
        #         get_download_link(href, filename, "📥 Download Recovery Trend (HTML)"),
        #         unsafe_allow_html=True
        #     )
    
    with col2:
        st.plotly_chart(fig_flow, use_container_width=True)
        # if st.button("Export Flow Trend"):
        #     href, filename = export_plot_to_html(fig_flow, f"{site_name}_flow_trend")
        #     st.markdown(
        #         get_download_link(href, filename, "📥 Download Flow Trend (HTML)"),
        #         unsafe_allow_html=True
        #     )
    
    # Display last update time
    st.text(f"Last Updated: {kpis['last_updated']}")

if __name__ == "__main__":
    render_site_details()