"""
Inventory Optimization Model
Extracts demand forecasting and safety stock calculation logic
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy import stats
import warnings

warnings.filterwarnings('ignore')


class InventoryOptimizer:
    """
    Inventory optimization model using Exponential Smoothing for demand forecasting
    and statistical methods for safety stock calculation.
    """
    
    def __init__(self, service_level=0.95):
        """
        Initialize the optimizer
        
        Args:
            service_level (float): Target service level (default: 0.95 for 95%)
        """
        self.service_level = service_level
        self.model = None
        self.forecast_data = None
        
    def prepare_data(self, df, store_id=1, dept_id=1):
        """
        Prepare time series data for a specific store and department
        
        Args:
            df (pd.DataFrame): Raw sales data with columns: Store, Dept, Date, Weekly_Sales
            store_id (int): Store ID to filter
            dept_id (int): Department ID to filter
            
        Returns:
            pd.Series: Time series of weekly sales
        """
        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sort by date
        df = df.sort_values(['Store', 'Dept', 'Date'])
        
        # Filter for specific store and department
        filtered_df = df[(df['Store'] == store_id) & (df['Dept'] == dept_id)].copy()
        
        # Set date as index
        filtered_df = filtered_df.set_index('Date')
        
        # Create time series with weekly frequency
        ts_data = filtered_df['Weekly_Sales'].asfreq('W-FRI')
        
        return ts_data
    
    def forecast_demand(self, ts_data, forecast_periods=12):
        """
        Forecast future demand using Exponential Smoothing
        
        Args:
            ts_data (pd.Series): Historical time series data
            forecast_periods (int): Number of periods to forecast
            
        Returns:
            dict: Forecast results including predictions and confidence intervals
        """
        try:
            # Fit Exponential Smoothing model
            self.model = ExponentialSmoothing(
                ts_data,
                seasonal_periods=52,  # Weekly data with yearly seasonality
                trend='add',
                seasonal='add',
                use_boxcox=False
            ).fit()
            
            # Generate forecast
            forecast = self.model.forecast(steps=forecast_periods)
            
            # Calculate prediction intervals (approximate)
            residuals = ts_data - self.model.fittedvalues
            std_error = np.std(residuals)
            
            # 95% confidence interval
            z_score = stats.norm.ppf((1 + self.service_level) / 2)
            margin_of_error = z_score * std_error
            
            self.forecast_data = {
                'forecast': forecast.tolist(),
                'lower_bound': (forecast - margin_of_error).tolist(),
                'upper_bound': (forecast + margin_of_error).tolist(),
                'historical_mean': float(ts_data.mean()),
                'historical_std': float(ts_data.std())
            }
            
            return self.forecast_data
            
        except Exception as e:
            raise ValueError(f"Error in forecasting: {str(e)}")
    
    def calculate_safety_stock(self, ts_data, lead_time_days=7):
        """
        Calculate optimal safety stock level
        
        Args:
            ts_data (pd.Series): Historical time series data
            lead_time_days (int): Lead time in days
            
        Returns:
            dict: Safety stock calculations
        """
        # Convert to daily demand (assuming weekly data)
        daily_demand = ts_data.mean() / 7
        demand_std = ts_data.std() / 7
        
        # Z-score for service level
        z_score = stats.norm.ppf(self.service_level)
        
        # Safety stock formula: Z * σ * √L
        safety_stock = z_score * demand_std * np.sqrt(lead_time_days)
        
        # Reorder point
        reorder_point = (daily_demand * lead_time_days) + safety_stock
        
        return {
            'safety_stock': float(safety_stock),
            'reorder_point': float(reorder_point),
            'average_daily_demand': float(daily_demand),
            'demand_std_dev': float(demand_std),
            'service_level': self.service_level,
            'lead_time_days': lead_time_days
        }
    
    def estimate_cost_savings(self, ts_data, current_buffer_multiplier=1.5):
        """
        Estimate cost savings from optimized inventory
        
        Args:
            ts_data (pd.Series): Historical time series data
            current_buffer_multiplier (float): Current safety stock as multiplier of mean demand
            
        Returns:
            dict: Cost savings analysis
        """
        # Current approach (simple buffer)
        current_safety_stock = ts_data.mean() * current_buffer_multiplier
        
        # Optimized approach
        optimized_safety_stock = self.calculate_safety_stock(ts_data)['safety_stock'] * 7  # Convert to weekly
        
        # Calculate reduction
        reduction = current_safety_stock - optimized_safety_stock
        reduction_percentage = (reduction / current_safety_stock) * 100
        
        return {
            'current_safety_stock': float(current_safety_stock),
            'optimized_safety_stock': float(optimized_safety_stock),
            'reduction': float(reduction),
            'reduction_percentage': float(reduction_percentage)
        }
    
    def get_recommendations(self, ts_data, forecast_periods=12, lead_time_days=7):
        """
        Get complete inventory recommendations
        
        Args:
            ts_data (pd.Series): Historical time series data
            forecast_periods (int): Number of periods to forecast
            lead_time_days (int): Lead time in days
            
        Returns:
            dict: Complete recommendations
        """
        forecast = self.forecast_demand(ts_data, forecast_periods)
        safety_stock = self.calculate_safety_stock(ts_data, lead_time_days)
        cost_savings = self.estimate_cost_savings(ts_data)
        
        return {
            'forecast': forecast,
            'safety_stock': safety_stock,
            'cost_savings': cost_savings,
            'summary': {
                'avg_weekly_sales': float(ts_data.mean()),
                'std_weekly_sales': float(ts_data.std()),
                'coefficient_of_variation': float((ts_data.std() / ts_data.mean()) * 100),
                'data_points': len(ts_data)
            }
        }
