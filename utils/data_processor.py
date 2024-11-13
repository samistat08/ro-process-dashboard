import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data(use_real_time=True, start_date=None, end_date=None):
    """Load and validate RO process data"""
    try:
        # Load data from RO_system_data.csv
        df = pd.read_csv('RO_system_data.csv')
        df['timestamp'] = pd.to_datetime(df['Date'])
        
        # Rename columns to match the expected format
        df = df.rename(columns={
            'Site': 'site_name',
            'Pressure (psi)': 'pressure',
            'Flow Rate (gpm)': 'flow-ID-001_feed',
            'Salt Rejection (%)': 'recovery_rate',
            'Temperature (C)': 'temperature',
            'pH Level': 'pH'
        })
        
        # Calculate product and waste flows based on feed flow and recovery rate
        df['flow-ID-001_product'] = df['flow-ID-001_feed'] * (df['recovery_rate'] / 100)
        df['flow-ID-001_waste'] = df['flow-ID-001_feed'] - df['flow-ID-001_product']
        
        # Add site_id based on site_name
        site_mapping = {name: idx for idx, name in enumerate(df['site_name'].unique(), 1)}
        df['site_id'] = df['site_name'].map(site_mapping)
        
        # Apply date filtering if dates are provided
        if start_date:
            df = df[df['timestamp'] >= pd.to_datetime(start_date)]
            logger.info(f"Filtered data from {start_date}")
        if end_date:
            df = df[df['timestamp'] <= pd.to_datetime(end_date)]
            logger.info(f"Filtered data to {end_date}")

        # Remove duplicates and sort by timestamp
        df = df.drop_duplicates(subset=['timestamp', 'site_name'])
        df = df.sort_values('timestamp')

        logger.info(f"Successfully loaded data with {len(df)} records")
        return df

    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

def process_site_data(df):
    """Process and aggregate site-level data"""
    site_data = df.groupby(['site_id', 'site_name', 'Latitude', 'Longitude']).agg({
        'pressure': 'mean',
        'flow-ID-001_feed': 'mean',
        'flow-ID-001_product': 'mean',
        'flow-ID-001_waste': 'mean',
        'temperature': 'mean',
        'pH': 'mean',
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
        'avg_flow': site_df['flow-ID-001_feed'].mean(),
        'efficiency_score': calculate_efficiency_score(site_df),
        'last_updated': site_df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': f"{site_df['timestamp'].min().strftime('%Y-%m-%d')} to {site_df['timestamp'].max().strftime('%Y-%m-%d')}"
    }
    
    return kpis

def calculate_efficiency_score(site_df):
    """Calculate overall efficiency score"""
    recovery_weight = 0.6
    pressure_weight = 0.4
    
    # Normalize recovery rate (95-100% is ideal)
    norm_recovery = (site_df['recovery_rate'] - 95) / 5
    
    # Normalize pressure (490-510 psi is ideal)
    norm_pressure = 1 - abs(site_df['pressure'] - 500) / 20
    
    score = (recovery_weight * norm_recovery + pressure_weight * norm_pressure).mean()
    return min(max(score * 100, 0), 100)  # Clamp to 0-100 range
