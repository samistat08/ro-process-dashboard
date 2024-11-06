import pandas as pd
import plotly
import json
from datetime import datetime
import base64
import io

def export_data_to_csv(df, filename_prefix):
    """Export DataFrame to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"
    
    # Convert DataFrame to CSV string
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    
    # Create download link
    b64 = base64.b64encode(csv_str.encode()).decode()
    href = f'data:file/csv;base64,{b64}'
    
    return href, filename

def export_plot_to_html(fig, filename_prefix):
    """Export Plotly figure to HTML"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.html"
    
    # Convert plot to HTML string
    plot_html = plotly.io.to_html(fig, full_html=False)
    
    # Create download link
    b64 = base64.b64encode(plot_html.encode()).decode()
    href = f'data:text/html;base64,{b64}'
    
    return href, filename

def get_download_link(href, filename, button_text):
    """Generate HTML download link"""
    return f'<a href="{href}" download="{filename}" style="text-decoration:none;">\
        <div style="background-color:#4CAF50; color:white; padding:8px 12px; border-radius:4px; \
        cursor:pointer; display:inline-block; text-align:center;">{button_text}</div></a>'
