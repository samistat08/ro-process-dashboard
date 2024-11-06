import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_data(use_real_time=True, start_date=None, end_date=None):
    """Load and validate RO process data"""
    try:
        if use_real_time:
            try:
                df = pd.read_csv('data/real_time_data.csv', parse_dates=['timestamp'])
            except FileNotFoundError:
                # Fall back to sample data if real-time data is not available
                df = pd.read_csv('data/sample_ro_data.csv', parse_dates=['timestamp'])
        else:
            df = pd.read_csv('data/sample_ro_data.csv', parse_dates=['timestamp'])
        
        # Apply time filtering if dates are provided
        if start_date and end_date:
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        elif start_date:
            df = df[df['timestamp'] >= start_date]
        elif end_date:
            df = df[df['timestamp'] <= end_date]
            
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

def process_site_data(df):
    """Process and aggregate site-level data"""
    # Group by site and calculate latest metrics
    site_data = df.groupby(['site_id', 'site_name', 'latitude', 'longitude']).agg({
        'pressure': 'mean',
        'flow_rate': 'mean',
        'conductivity': 'mean',
        'temperature': 'mean',
        'recovery_rate': 'mean',
        'timestamp': 'max'  # Keep track of latest timestamp
    }).reset_index()
    
    return site_data

def calculate_kpis(df, site_name):
    """Calculate KPIs for a specific site"""
    site_df = df[df['site_name'] == site_name]
    
    kpis = {
        'avg_recovery': site_df['recovery_rate'].mean(),
        'avg_pressure': site_df['pressure'].mean(),
        'avg_flow': site_df['flow_rate'].mean(),
        'efficiency_score': calculate_efficiency_score(site_df),
        'last_updated': site_df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': f"{site_df['timestamp'].min().strftime('%Y-%m-%d')} to {site_df['timestamp'].max().strftime('%Y-%m-%d')}"
    }
    
    return kpis

def calculate_efficiency_score(site_df):
    """Calculate overall efficiency score"""
    # Normalized score based on recovery rate and pressure efficiency
    recovery_weight = 0.6
    pressure_weight = 0.4
    
    norm_recovery = (site_df['recovery_rate'] - 70) / 30  # Normalize to 0-1 scale
    norm_pressure = 1 - (site_df['pressure'] - 60) / 20
    
    score = (recovery_weight * norm_recovery + pressure_weight * norm_pressure).mean()
    return min(max(score * 100, 0), 100)  # Clamp to 0-100 range
