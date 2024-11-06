import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

class RODataSimulator:
    def __init__(self):
        # Load initial data to get site information
        self.base_data = pd.read_csv('data/sample_ro_data.csv')
        self.sites = self.base_data[['site_id', 'site_name', 'latitude', 'longitude']].drop_duplicates()
        
    def generate_sensor_data(self):
        """Generate synthetic sensor data for all sites"""
        current_time = datetime.now()
        
        # Generate data for each site
        rows = []
        for _, site in self.sites.iterrows():
            # Add random variations to base metrics
            pressure = np.random.normal(65, 2)  # Normal distribution around 65 bar
            flow_rate = np.random.normal(118, 3)  # Normal distribution around 118 m³/h
            conductivity = np.random.normal(460, 15)  # Normal distribution around 460 µS/cm
            temperature = np.random.normal(25, 1.5)  # Normal distribution around 25°C
            recovery_rate = np.random.normal(75, 2)  # Normal distribution around 75%
            
            # Ensure values are within realistic ranges
            row = {
                'timestamp': current_time,
                'site_id': site['site_id'],
                'site_name': site['site_name'],
                'latitude': site['latitude'],
                'longitude': site['longitude'],
                'pressure': max(min(pressure, 80), 50),
                'flow_rate': max(min(flow_rate, 130), 100),
                'conductivity': max(min(conductivity, 500), 400),
                'temperature': max(min(temperature, 30), 20),
                'recovery_rate': max(min(recovery_rate, 85), 65)
            }
            rows.append(row)
            
        return pd.DataFrame(rows)

    def save_data(self, df):
        """Save data to CSV file"""
        df.to_csv('data/real_time_data.csv', index=False)
        
    def run_simulation(self, interval=5):
        """Run continuous data simulation"""
        while True:
            new_data = self.generate_sensor_data()
            self.save_data(new_data)
            time.sleep(interval)  # Wait for specified interval

if __name__ == "__main__":
    simulator = RODataSimulator()
    simulator.run_simulation()
