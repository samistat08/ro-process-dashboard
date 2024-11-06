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
        # Initialize empty DataFrames
        historical_df = pd.DataFrame()
        real_time_df = pd.DataFrame()

        # Load historical data from the new CSV
        try:
            historical_df = pd.read_csv('RO_System_Sensors_Hourly_Report_May_to_October_2024 - RO_System_Sensors_Hourly_Report_May_to_October_2024 (2).csv')
            logger.info("Debug - CSV columns: %s", historical_df.columns.tolist())
            
            # Handle missing values before processing
            historical_df = historical_df.fillna({
                'pres-ID-001_feed': historical_df['pres-ID-001_feed'].median(),
                'flow-ID-001_feed': historical_df['flow-ID-001_feed'].median(),
                'flow-ID-001_product': historical_df['flow-ID-001_product'].median()
            })
            
            # Convert the specific columns from the CSV to match our expected format
            historical_df = historical_df.rename(columns={
                'pres-ID-001_feed': 'pressure',
                'flow-ID-001_feed': 'flow_rate',
                'location': 'site_name'
            })
            
            # Convert Date and Time columns to timestamp
            historical_df['timestamp'] = pd.to_datetime(
                historical_df['Date'] + ' ' + historical_df['Time'],
                format='%d/%m/%Y %H:%M:%S',
                dayfirst=True
            )
            
            # Calculate recovery rate from available metrics
            historical_df['recovery_rate'] = (
                historical_df['flow-ID-001_product'] / historical_df['flow-ID-001_feed']
            ) * 100
            
            # Add missing columns for compatibility with real-time data
            if 'site_id' not in historical_df.columns:
                historical_df['site_id'] = historical_df.groupby('site_name').ngroup() + 1
            
            if 'latitude' not in historical_df.columns:
                # Update site coordinates mapping based on the new data
                site_coords = {
                    'amsterdam': (52.3676, 4.9041),
                    'singapore': (1.3521, 103.8198),
                    'dubai': (25.2048, 55.2708),
                    'california': (34.0522, -118.2437)
                }
                historical_df['latitude'] = historical_df['site_name'].map(lambda x: site_coords.get(x.lower(), (0, 0))[0])
                historical_df['longitude'] = historical_df['site_name'].map(lambda x: site_coords.get(x.lower(), (0, 0))[1])
            
            if 'conductivity' not in historical_df.columns:
                historical_df['conductivity'] = historical_df['elect-ID-001_feed']
            
            if 'temperature' not in historical_df.columns:
                historical_df['temperature'] = np.nan

        except FileNotFoundError:
            logger.warning("Historical data file not found")
            raise

        # Load real-time data if enabled
        if use_real_time:
            try:
                real_time_df = pd.read_csv('data/real_time_data.csv')
                logger.info("Debug - Real-time CSV columns: %s", real_time_df.columns.tolist())
                real_time_df['timestamp'] = pd.to_datetime(real_time_df['timestamp'])
            except FileNotFoundError:
                logger.warning("Real-time data file not found")

        # Combine historical and real-time data if both exist
        if not historical_df.empty and not real_time_df.empty and use_real_time:
            logger.info("Combining historical and real-time data")
            df = pd.concat([historical_df, real_time_df], ignore_index=True)
        else:
            df = historical_df if not historical_df.empty else real_time_df

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
