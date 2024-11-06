import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_data(use_real_time=True, start_date=None, end_date=None):
    """Load and validate RO process data"""
    try:
        # Load real-time data first
        if use_real_time:
            try:
                real_time_df = pd.read_csv('data/real_time_data.csv', parse_dates=['timestamp'])
            except FileNotFoundError:
                real_time_df = pd.DataFrame()

        # Load historical data from sensor_data_output
        try:
            historical_df = pd.read_csv('sensor_data_output - sensor_data_output.csv', parse_dates=['timestamp'])
        except FileNotFoundError:
            historical_df = pd.DataFrame()

        # Combine real-time and historical data if both exist
        if not historical_df.empty and not real_time_df.empty and use_real_time:
            df = pd.concat([historical_df, real_time_df], ignore_index=True)
        elif not historical_df.empty:
            df = historical_df
        elif not real_time_df.empty and use_real_time:
            df = real_time_df
        else:
            # Fallback to sample data if no other data is available
            df = pd.read_csv('data/sample_ro_data.csv', parse_dates=['timestamp'])

        # Remove duplicates based on timestamp and site_id
        df = df.drop_duplicates(subset=['timestamp', 'site_id'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Apply time filtering if dates are provided
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['timestamp'] >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
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
