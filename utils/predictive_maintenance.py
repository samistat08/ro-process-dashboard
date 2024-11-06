import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenancePredictor:
    def __init__(self):
        # Define thresholds for different parameters
        self.thresholds = {
            'pressure': {'low': 55, 'high': 75, 'trend_threshold': 0.5},
            'flow_rate': {'low': 105, 'high': 125, 'trend_threshold': 0.3},
            'conductivity': {'low': 420, 'high': 490, 'trend_threshold': 2.0},
            'recovery_rate': {'low': 70, 'high': 80, 'trend_threshold': 0.5}
        }
        
    def calculate_trends(self, data, window_size=5):
        """Calculate trends in sensor data using rolling averages"""
        trends = {}
        for param in self.thresholds.keys():
            if param in data.columns:
                rolling_mean = data[param].rolling(window=window_size).mean()
                rolling_std = data[param].rolling(window=window_size).std()
                
                # Handle case when there's not enough data points
                if len(rolling_mean) < window_size:
                    trends[param] = {
                        'current_value': data[param].iloc[-1] if not data[param].empty else 0,
                        'mean': rolling_mean.iloc[-1] if not rolling_mean.empty else 0,
                        'std': rolling_std.iloc[-1] if not rolling_std.empty else 0,
                        'trend': 0  # Set trend to 0 when insufficient data
                    }
                else:
                    # Calculate trend only when we have enough data points
                    trends[param] = {
                        'current_value': data[param].iloc[-1],
                        'mean': rolling_mean.iloc[-1],
                        'std': rolling_std.iloc[-1],
                        'trend': (rolling_mean.iloc[-1] - rolling_mean.iloc[-window_size]) / window_size
                    }
        return trends

    def analyze_site_data(self, site_data):
        """Analyze site data for potential maintenance issues"""
        alerts = []
        
        # Calculate trends
        trends = self.calculate_trends(site_data)
        
        for param, trend_data in trends.items():
            thresholds = self.thresholds[param]
            current_value = trend_data['current_value']
            trend = trend_data['trend']
            
            # Check for out-of-range values
            if current_value < thresholds['low']:
                alerts.append({
                    'parameter': param,
                    'severity': 'high',
                    'message': f'Low {param}: {current_value:.1f}',
                    'recommendation': f'Check {param} sensors and control systems'
                })
            elif current_value > thresholds['high']:
                alerts.append({
                    'parameter': param,
                    'severity': 'high',
                    'message': f'High {param}: {current_value:.1f}',
                    'recommendation': f'Verify {param} control systems and membrane condition'
                })
            
            # Check for concerning trends
            if abs(trend) > thresholds['trend_threshold']:
                trend_direction = 'increasing' if trend > 0 else 'decreasing'
                alerts.append({
                    'parameter': param,
                    'severity': 'medium',
                    'message': f'{param.replace("_", " ").title()} is {trend_direction} rapidly',
                    'recommendation': f'Monitor {param} trend and schedule preventive maintenance'
                })
        
        return alerts

    def predict_maintenance_needs(self, site_data):
        """Predict maintenance needs based on historical data"""
        alerts = self.analyze_site_data(site_data)
        
        if not alerts:
            return {
                'status': 'normal',
                'alerts': [],
                'next_maintenance': datetime.now() + timedelta(days=30)
            }
        
        # Calculate maintenance urgency based on number and severity of alerts
        severity_scores = {'high': 3, 'medium': 2, 'low': 1}
        total_score = sum(severity_scores[alert['severity']] for alert in alerts)
        
        # Determine next maintenance date based on severity score
        if total_score >= 5:
            next_maintenance = datetime.now() + timedelta(days=7)
            status = 'critical'
        elif total_score >= 3:
            next_maintenance = datetime.now() + timedelta(days=14)
            status = 'warning'
        else:
            next_maintenance = datetime.now() + timedelta(days=21)
            status = 'attention'
            
        return {
            'status': status,
            'alerts': alerts,
            'next_maintenance': next_maintenance
        }
