#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Prediction Script for PyMC Hierarchical Visibility Model
Supports both single predictions and predictions over a time period
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import json
import pickle
import pymc as pm
import arviz as az
from stormglass_api_client import StormGlassClient
import argparse
import sys
import os
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Expected parameters from the model
EXPECTED_PREDICTORS = [
    'windSpeed_2day_roll_avg',
    'waveHeight_2day_roll_avg',
    'precipitation_2day_roll_avg',
    'airTemperature_2day_roll_avg',
    'waterTemperature_2day_roll_avg',
    'swellHeight_2day_roll_avg',
    'cloudCover_2day_roll_avg',
    'pressure_2day_roll_avg',
    'precipitation_sum_last_24h',
    'precipitation_sum_last_48h',
    'day_of_year_sin',
    'day_of_year_cos',
    'month_sin',
    'month_cos'
]

# StormGlass parameters to fetch
STORMGLASS_PARAMS = [
    'airTemperature', 'waterTemperature', 'windSpeed', 'windDirection',
    'waveHeight', 'wavePeriod', 'waveDirection', 'swellHeight',
    'swellPeriod', 'swellDirection', 'cloudCover', 'humidity',
    'precipitation', 'visibility', 'pressure', 'gust', 'seaLevel'
]

class PeriodVisibilityPredictor:
    def __init__(self, model_path='models/stormglass_pymc_hierarchical_daily_rolling_idata.nc',
                 scaler_path='models/stormglass_pymc_hierarchical_daily_rolling_scaler.pkl',
                 site_coords_path='site_coordinates.json'):
        """Initialize the predictor with model and data paths"""
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.site_coords_path = site_coords_path
        self.client = StormGlassClient()
        
        # Load site coordinates
        self.load_site_coordinates()
        
        # Load model and scaler
        self.load_model_and_scaler()
        
    def load_site_coordinates(self):
        """Load site coordinates from JSON file"""
        try:
            with open(self.site_coords_path, 'r') as f:
                self.site_coords = json.load(f)
            print(f"Loaded coordinates for {len(self.site_coords)} sites")
        except Exception as e:
            print(f"Error loading site coordinates: {e}")
            self.site_coords = {}
            
    def load_model_and_scaler(self):
        """Load the trained model and scaler"""
        try:
            # Load InferenceData
            self.idata = az.from_netcdf(self.model_path)
            print(f"Loaded model from {self.model_path}")
            
            # Load scaler
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            print(f"Loaded scaler from {self.scaler_path}")
            
            # Extract model parameters
            self.intercept_mean = self.idata.posterior["intercept"].mean().item()
            self.beta_predictors_mean = self.idata.posterior["beta_predictors"].mean(dim=("chain", "draw")).values
            self.site_effects_mean = self.idata.posterior["a_site_actual_dev"].mean(dim=("chain", "draw")).values
            
            # Get site mapping from the model
            self.model_sites = self.idata.posterior.coords["site_train"].values
            
        except Exception as e:
            print(f"Error loading model or scaler: {e}")
            raise
            
    def get_site_effect(self, site_code):
        """Get site-specific effect for a given site code"""
        site_effect = 0.0
        
        try:
            df_training = pd.read_csv('stormglass_output/daily_rolling_averages.csv')
            site_mapping = {}
            for idx, site in enumerate(df_training['site'].unique()):
                if '(' in site and ')' in site:
                    code = site.split('(')[-1].split(')')[0].strip()
                    site_mapping[code] = idx
            
            if site_code in site_mapping:
                site_idx = site_mapping[site_code]
                if site_idx < len(self.site_effects_mean):
                    site_effect = self.site_effects_mean[site_idx]
                    
        except Exception as e:
            print(f"Warning: Could not load site mappings: {e}")
            
        return site_effect
        
    def fetch_weather_data_period(self, site_code, start_date, end_date):
        """Fetch weather data for a period, handling API limitations"""
        if site_code not in self.site_coords:
            raise ValueError(f"Site code '{site_code}' not found in coordinates database")
            
        lat = self.site_coords[site_code]['lat']
        lon = self.site_coords[site_code]['lon']
        
        # StormGlass API typically allows up to 10 days of forecast data
        # For historical data, we need to fetch in chunks
        all_data = {'days_data': {}}
        
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        print(f"Fetching weather data for {site_code} from {start_date} to {end_date}")
        
        # We need data from 3 days before the start date for rolling averages
        fetch_start = current_date - timedelta(days=3)
        fetch_end = end_datetime + timedelta(days=1)  # Include end date
        
        try:
            # Use get_weather_data which accepts start and end dates
            weather_data = self.client.get_weather_data(
                lat, lon, 
                fetch_start.strftime('%Y-%m-%d'), 
                fetch_end.strftime('%Y-%m-%d')
            )
            
            if not weather_data or 'hours' not in weather_data:
                raise ValueError("Failed to get weather data")
                
            # Convert to the format expected by process_weather_data_for_date
            # We'll return the raw weather data with hours
            return {'days_data': {}, 'hours': weather_data.get('hours', [])}
                
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            raise
            
    def process_weather_data_for_date(self, all_hourly_data, target_date):
        """Process weather data for a specific date"""
        df_hourly = pd.DataFrame(all_hourly_data)
        
        # Filter data up to target date
        df_hourly['timestamp'] = pd.to_datetime(df_hourly['timestamp'])
        df_hourly['date'] = df_hourly['timestamp'].dt.date
        
        # Get data up to and including target date
        target_date_obj = target_date.date() if hasattr(target_date, 'date') else target_date
        df_relevant = df_hourly[df_hourly['date'] <= target_date_obj].copy()
        
        if df_relevant.empty:
            return None
            
        # Calculate daily averages
        agg_funcs = {col: 'mean' for col in STORMGLASS_PARAMS if col != 'precipitation'}
        agg_funcs['precipitation'] = 'sum'
        
        # Only aggregate columns that exist
        agg_funcs_filtered = {k: v for k, v in agg_funcs.items() if k in df_relevant.columns}
        
        df_daily = df_relevant.groupby('date')[list(agg_funcs_filtered.keys())].agg(agg_funcs_filtered).reset_index()
        df_daily = df_daily.sort_values('date')
        
        # Calculate rolling averages (2-day)
        features = {}
        
        params_for_rolling = ['windSpeed', 'waveHeight', 'precipitation', 'airTemperature',
                             'waterTemperature', 'swellHeight', 'cloudCover', 'pressure']
        
        for param in params_for_rolling:
            if param in df_daily.columns:
                # Get last 2 days including target date
                last_2_days = df_daily.tail(2)
                if len(last_2_days) >= 1:
                    features[f'{param}_2day_roll_avg'] = last_2_days[param].mean()
                else:
                    features[f'{param}_2day_roll_avg'] = np.nan
            else:
                features[f'{param}_2day_roll_avg'] = np.nan
                
        # Calculate precipitation sums
        target_datetime_tz = target_date.replace(tzinfo=pytz.UTC) if target_date.tzinfo is None else target_date
        
        # Last 24 hours
        mask_24h = (df_hourly['timestamp'] > (target_datetime_tz - timedelta(hours=24))) & \
                   (df_hourly['timestamp'] <= target_datetime_tz)
        features['precipitation_sum_last_24h'] = df_hourly.loc[mask_24h, 'precipitation'].sum() if 'precipitation' in df_hourly.columns else 0
        
        # Last 48 hours
        mask_48h = (df_hourly['timestamp'] > (target_datetime_tz - timedelta(hours=48))) & \
                   (df_hourly['timestamp'] <= target_datetime_tz)
        features['precipitation_sum_last_48h'] = df_hourly.loc[mask_48h, 'precipitation'].sum() if 'precipitation' in df_hourly.columns else 0
        
        # Add temporal features
        features['day_of_year_sin'] = np.sin(2 * np.pi * target_date.timetuple().tm_yday / 365)
        features['day_of_year_cos'] = np.cos(2 * np.pi * target_date.timetuple().tm_yday / 365)
        features['month_sin'] = np.sin(2 * np.pi * target_date.month / 12)
        features['month_cos'] = np.cos(2 * np.pi * target_date.month / 12)
        
        return features
        
    def predict_period(self, site_code, start_date, end_date, time_str='12:00', 
                      include_uncertainty=True, save_plot=True):
        """Make visibility predictions for a time period"""
        # Parse dates
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Fetch weather data for the period
        weather_data = self.fetch_weather_data_period(site_code, start_date, end_date)
        
        # Extract all hourly data
        all_hourly_data = []
        
        # Process hours directly from the weather data
        for hour_entry in weather_data.get('hours', []):
            hour_timestamp = datetime.fromisoformat(hour_entry['time'].replace('Z', '+00:00'))
            
            hourly_record = {
                'timestamp': hour_timestamp,
                'date': hour_timestamp.date()
            }
            
            for param in STORMGLASS_PARAMS:
                if param in hour_entry and isinstance(hour_entry[param], dict):
                    hourly_record[param] = hour_entry[param].get('sg')
                else:
                    hourly_record[param] = np.nan
                    
            all_hourly_data.append(hourly_record)
        
        # Get site effect
        site_effect = self.get_site_effect(site_code)
        if site_effect != 0:
            print(f"Using site-specific effect for {site_code}: {site_effect:.3f}")
        else:
            print(f"No site-specific effect found for {site_code}, using average")
        
        # Make predictions for each day
        results = []
        current_date = start_datetime
        
        while current_date <= end_datetime:
            # Combine date and time
            target_time = datetime.strptime(time_str, '%H:%M').time()
            target_datetime = datetime.combine(current_date, target_time)
            
            # Process weather data for this date
            features = self.process_weather_data_for_date(all_hourly_data, target_datetime)
            
            if features is None:
                print(f"Warning: No data available for {current_date.strftime('%Y-%m-%d')}")
                current_date += timedelta(days=1)
                continue
            
            # Prepare for prediction
            X = pd.DataFrame([features])[EXPECTED_PREDICTORS]
            X = X.fillna(X.median())
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            fixed_effects = self.intercept_mean + np.dot(X_scaled, self.beta_predictors_mean)
            log_prediction = fixed_effects[0] + site_effect
            prediction = np.exp(log_prediction)
            
            result = {
                'date': current_date.strftime('%Y-%m-%d'),
                'datetime': target_datetime,
                'predicted_visibility_m': round(prediction, 2),
                'features': features
            }
            
            # Calculate uncertainty if requested
            if include_uncertainty:
                posterior_samples = []
                n_samples = min(100, len(self.idata.posterior["intercept"].values.flatten()))
                
                for i in range(n_samples):
                    intercept_sample = self.idata.posterior["intercept"].values.flatten()[i]
                    beta_sample = self.idata.posterior["beta_predictors"].values.reshape(-1, len(EXPECTED_PREDICTORS))[i]
                    
                    fixed_sample = intercept_sample + np.dot(X_scaled, beta_sample)
                    log_pred_sample = fixed_sample[0] + site_effect
                    posterior_samples.append(np.exp(log_pred_sample))
                    
                result['prediction_interval_lower'] = round(np.percentile(posterior_samples, 2.5), 2)
                result['prediction_interval_upper'] = round(np.percentile(posterior_samples, 97.5), 2)
                
            results.append(result)
            current_date += timedelta(days=1)
        
        # Create visualization if requested
        if save_plot and results:
            self.plot_period_predictions(results, site_code, time_str)
            
        return results
        
    def plot_period_predictions(self, results, site_code, time_str):
        """Create a plot of predictions over time"""
        dates = [r['datetime'] for r in results]
        predictions = [r['predicted_visibility_m'] for r in results]
        
        plt.figure(figsize=(12, 6))
        
        # Plot predictions
        plt.plot(dates, predictions, 'b-', linewidth=2, label='Predicted Visibility')
        
        # Add confidence intervals if available
        if 'prediction_interval_lower' in results[0]:
            lower = [r['prediction_interval_lower'] for r in results]
            upper = [r['prediction_interval_upper'] for r in results]
            plt.fill_between(dates, lower, upper, alpha=0.3, color='blue', label='95% Confidence Interval')
        
        # Add horizontal lines for reference
        plt.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='Good visibility (10m)')
        plt.axhline(y=5, color='orange', linestyle='--', alpha=0.5, label='Moderate visibility (5m)')
        plt.axhline(y=3, color='red', linestyle='--', alpha=0.5, label='Poor visibility (3m)')
        
        # Format plot
        plt.xlabel('Date')
        plt.ylabel('Visibility (meters)')
        plt.title(f'Visibility Forecast for {site_code} at {time_str}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format x-axis
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        filename = f'visibility_forecast_{site_code}_{dates[0].strftime("%Y%m%d")}_{dates[-1].strftime("%Y%m%d")}.png'
        plt.savefig(filename)
        plt.close()
        print(f"Saved forecast plot to {filename}")
        
    def save_results_to_csv(self, results, site_code, filename=None):
        """Save prediction results to CSV file"""
        if not results:
            print("No results to save")
            return
            
        # Convert to DataFrame
        df_results = pd.DataFrame(results)
        
        # Flatten features into separate columns
        if 'features' in df_results.columns:
            features_df = pd.json_normalize(df_results['features'])
            df_results = pd.concat([df_results.drop('features', axis=1), features_df], axis=1)
        
        # Generate filename if not provided
        if filename is None:
            start_date = results[0]['date']
            end_date = results[-1]['date']
            filename = f'visibility_predictions_{site_code}_{start_date}_{end_date}.csv'
            
        df_results.to_csv(filename, index=False)
        print(f"Saved results to {filename}")
        
        return df_results

def main():
    parser = argparse.ArgumentParser(
        description='Predict underwater visibility for a time period using StormGlass weather data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single day prediction
  python %(prog)s AMJ 2024-12-15 --time 10:00
  
  # Period prediction (7 days)
  python %(prog)s AMJ 2024-12-15 --end-date 2024-12-21 --time 09:00
  
  # Save results to CSV
  python %(prog)s HIL 2024-12-20 --end-date 2024-12-25 --save-csv
        """
    )
    
    parser.add_argument('site_code', help='Site code (e.g., AMJ, HIL, RNN)')
    parser.add_argument('start_date', help='Start date for prediction (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for period prediction (YYYY-MM-DD)')
    parser.add_argument('--time', default='12:00', help='Time for prediction (HH:MM, default: 12:00)')
    parser.add_argument('--save-csv', action='store_true', help='Save results to CSV file')
    parser.add_argument('--no-plot', action='store_true', help='Skip creating visualization plot')
    parser.add_argument('--no-uncertainty', action='store_true', help='Skip uncertainty calculations')
    parser.add_argument('--model', default='models/stormglass_pymc_hierarchical_daily_rolling_idata.nc',
                       help='Path to model file')
    parser.add_argument('--scaler', default='models/stormglass_pymc_hierarchical_daily_rolling_scaler.pkl',
                       help='Path to scaler file')
    parser.add_argument('--sites', default='site_coordinates.json',
                       help='Path to site coordinates file')
    
    args = parser.parse_args()
    
    try:
        # Initialize predictor
        predictor = PeriodVisibilityPredictor(
            model_path=args.model,
            scaler_path=args.scaler,
            site_coords_path=args.sites
        )
        
        # Determine if this is a period prediction
        if args.end_date:
            # Period prediction
            results = predictor.predict_period(
                site_code=args.site_code,
                start_date=args.start_date,
                end_date=args.end_date,
                time_str=args.time,
                include_uncertainty=not args.no_uncertainty,
                save_plot=not args.no_plot
            )
            
            if results:
                print(f"\n{'='*60}")
                print(f"VISIBILITY FORECAST RESULTS FOR {args.site_code}")
                print(f"Period: {args.start_date} to {args.end_date} at {args.time}")
                print(f"{'='*60}")
                
                # Display summary statistics
                predictions = [r['predicted_visibility_m'] for r in results]
                print(f"\nSummary Statistics:")
                print(f"  Average visibility: {np.mean(predictions):.1f} m")
                print(f"  Best visibility: {np.max(predictions):.1f} m on {results[np.argmax(predictions)]['date']}")
                print(f"  Worst visibility: {np.min(predictions):.1f} m on {results[np.argmin(predictions)]['date']}")
                
                # Display daily predictions
                print(f"\nDaily Predictions:")
                print(f"{'Date':<12} {'Visibility (m)':<15} {'Conditions':<30}")
                print("-" * 57)
                
                for result in results:
                    vis = result['predicted_visibility_m']
                    conditions = "Good" if vis >= 10 else ("Moderate" if vis >= 5 else "Poor")
                    
                    if 'prediction_interval_lower' in result:
                        ci_str = f"[{result['prediction_interval_lower']:.1f}, {result['prediction_interval_upper']:.1f}]"
                        print(f"{result['date']:<12} {vis:<15.1f} {conditions:<15} CI: {ci_str}")
                    else:
                        print(f"{result['date']:<12} {vis:<15.1f} {conditions}")
                
                # Save to CSV if requested
                if args.save_csv:
                    predictor.save_results_to_csv(results, args.site_code)
                    
        else:
            # Single prediction (use original predict method)
            # This would need to be implemented similar to the original script
            print("Single day prediction - use predict_with_stormglass.py for now")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 