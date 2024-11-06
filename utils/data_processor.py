import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_data(use_real_time=True, start_date=None, end_date=None):
    """Load and validate RO process data"""
    try:
        # Initialize empty DataFrames
        historical_df = pd.DataFrame()
        real_time_df = pd.DataFrame()

        # Load real-time data if enabled
        if use_real_time:
            try:
                real_time_df = pd.read_csv('data/real_time_data.csv')
                if 'timestamp' in real_time_df.columns:
                    real_time_df['timestamp'] = pd.to_datetime(real_time_df['timestamp'])
            except FileNotFoundError:
                pass

        # Load historical data
        try:
            historical_df = pd.read_csv('sensor_data_output - sensor_data_output.csv')
            
            # Handle date and time columns
            if 'date' in historical_df.columns and 'time' in historical_df.columns:
                # Convert date and time to proper format
                historical_df['date'] = pd.to_datetime(historical_df['date']).dt.strftime('%Y-%m-%d')
                historical_df['time'] = pd.to_datetime(historical_df['time'], format='%H:%M:%S').dt.strftime('%H:%M:%S')
                # Combine date and time into timestamp
                historical_df['timestamp'] = pd.to_datetime(historical_df['date'] + ' ' + historical_df['time'])
                # Drop original date and time columns
                historical_df = historical_df.drop(['date', 'time'], axis=1)
            elif 'timestamp' in historical_df.columns:
                historical_df['timestamp'] = pd.to_datetime(historical_df['timestamp'])
            else:
                raise ValueError("No valid timestamp columns found in historical data")
        except FileNotFoundError:
            raise ValueError("Historical data file not found")

        # Combine real-time and historical data if both exist
        if not historical_df.empty and not real_time_df.empty and use_real_time:
            df = pd.concat([historical_df, real_time_df], ignore_index=True)
        else:
            df = historical_df

        # Remove duplicates and sort
        df = df.drop_duplicates(subset=['timestamp', 'site_id'])
        df = df.sort_values('timestamp')
        
        # Apply time filtering if dates are provided
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['timestamp'] >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['timestamp'] <= end_date]
            
        if df.empty:
            raise ValueError("No data available for the specified time range")
            
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

def process_site_data(df):
    """Process and aggregate site-level data"""
    site_data = df.groupby(['site_id', 'site_name', 'latitude', 'longitude']).agg({
        'pressure': 'mean',
        'flow_rate': 'mean',
        'conductivity': 'mean',
        'temperature': 'mean',
        'recovery_rate': 'mean',
        'timestamp': 'max'
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
    recovery_weight = 0.6
    pressure_weight = 0.4
    
    norm_recovery = (site_df['recovery_rate'] - 70) / 30  # Normalize to 0-1 scale
    norm_pressure = 1 - (site_df['pressure'] - 60) / 20
    
    score = (recovery_weight * norm_recovery + pressure_weight * norm_pressure).mean()
    return min(max(score * 100, 0), 100)  # Clamp to 0-100 range
