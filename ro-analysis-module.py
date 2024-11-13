import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from prophet import Prophet
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

class AdvancedAnalytics:
    """Advanced statistical analysis features"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def detect_anomalies(self, data, columns, contamination=0.1):
        """Detect anomalies using Isolation Forest"""
        scaled_data = self.scaler.fit_transform(data[columns])
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        anomalies = iso_forest.fit_predict(scaled_data)
        return pd.Series(anomalies == -1, index=data.index)
    
    def analyze_trends(self, data, column):
        """Analyze trends using exponential smoothing"""
        model = ExponentialSmoothing(
            data[column],
            seasonal_periods=24,
            trend='add',
            seasonal='add'
        )
        fitted_model = model.fit()
        trend = fitted_model.trend
        seasonality = fitted_model.seasonal
        return trend, seasonality
    
    def correlation_analysis(self, data, columns):
        """Perform correlation analysis with statistical significance"""
        corr_matrix = data[columns].corr()
        p_values = pd.DataFrame(
            [[pearsonr(data[c1], data[c2])[1] for c2 in columns] for c1 in columns],
            index=columns,
            columns=columns
        )
        return corr_matrix, p_values
    
    def performance_metrics(self, data, column, baseline):
        """Calculate comprehensive performance metrics"""
        return {
            'mean': data[column].mean(),
            'std': data[column].std(),
            'cv': data[column].std() / data[column].mean(),
            'efficiency': (data[column] / baseline).mean(),
            'stability': 1 - data[column].rolling(24).std().mean() / data[column].mean()
        }

class PredictiveModeling:
    """Advanced prediction models"""
    
    def __init__(self):
        self.models = {
            'prophet': self._train_prophet,
            'lstm': self._train_lstm,
            'ensemble': self._train_ensemble
        }
        
    def _train_prophet(self, data, column, forecast_days):
        """Train Facebook Prophet model"""
        df = pd.DataFrame({
            'ds': data.index,
            'y': data[column]
        })
        model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10,
            seasonality_mode='multiplicative'
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    def _train_lstm(self, data, column, forecast_days):
        """Train LSTM model"""
        sequence_length = 24
        X, y = self._prepare_sequences(data[column], sequence_length)
        
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(sequence_length, 1)),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X, y, epochs=50, batch_size=32, verbose=0)
        
        # Generate predictions
        last_sequence = X[-1]
        predictions = []
        for _ in range(forecast_days):
            pred = model.predict(last_sequence.reshape(1, sequence_length, 1))
            predictions.append(pred[0, 0])
            last_sequence = np.roll(last_sequence, -1)
            last_sequence[-1] = pred
            
        return predictions
    
    def _train_ensemble(self, data, column, forecast_days):
        """Combine multiple models for ensemble predictions"""
        prophet_pred = self._train_prophet(data, column, forecast_days)
        lstm_pred = self._train_lstm(data, column, forecast_days)
        
        # Combine predictions with weights
        weights = {'prophet': 0.6, 'lstm': 0.4}
        ensemble_pred = weights['prophet'] * prophet_pred['yhat'].values + \
                       weights['lstm'] * np.array(lstm_pred)
        
        return ensemble_pred

class ReportGenerator:
    """Generate comprehensive reports"""
    
    def generate_pdf_report(self, data, analysis_results, predictions, config):
        """Generate PDF report with charts and analysis"""
        doc = SimpleDocTemplate("ro_system_report.pdf")
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        elements.append(Paragraph("RO System Analysis Report", styles['Title']))
        
        # System Overview
        elements.append(Paragraph("System Overview", styles['Heading1']))
        self._add_system_summary(elements, data, styles)
        
        # Performance Analysis
        elements.append(Paragraph("Performance Analysis", styles['Heading1']))
        self._add_performance_analysis(elements, analysis_results, styles)
        
        # Predictions and Recommendations
        elements.append(Paragraph("Predictions and Recommendations", styles['Heading1']))
        self._add_predictions(elements, predictions, styles)
        
        # Generate PDF
        doc.build(elements)
        
    def generate_excel_report(self, data, analysis_results, predictions):
        """Generate Excel report with multiple sheets"""
        with pd.ExcelWriter('ro_system_report.xlsx') as writer:
            