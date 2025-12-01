#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stormglass_data_collection.log')
    ]
)
logger = logging.getLogger(__name__)

class StormGlassClient:
    """Client for fetching weather and marine data from StormGlass API."""
    
    def __init__(self):
        """Initialize the StormGlass API client."""
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv('STORMGLASS_API_KEY')
        if not self.api_key:
            logger.error("STORMGLASS_API_KEY is not set in the environment variables")
            raise ValueError("STORMGLASS_API_KEY is required")
        
        # StormGlass API endpoints
        self.weather_url = "https://api.stormglass.io/v2/weather/point"
        self.tide_url = "https://api.stormglass.io/v2/tide/extremes/point"
        
        # Parameters to fetch from the API
        self.weather_params = [
            'airTemperature', 'waterTemperature', 'windSpeed', 'windDirection',
            'waveHeight', 'wavePeriod', 'waveDirection', 'swellHeight',
            'swellPeriod', 'swellDirection', 'cloudCover', 'humidity',
            'precipitation', 'visibility', 'pressure', 'gust', 'seaLevel'
        ]
    
    def get_weather_data(self, lat, lon, start_date, end_date=None):
        """
        Fetch weather and marine data for a specific location and time range.
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            start_date (str or datetime): Start date in 'YYYY-MM-DD' format or as datetime
            end_date (str or datetime, optional): End date. Defaults to start_date+1
        
        Returns:
            dict: Weather and marine data from StormGlass
        """
        try:
            # Convert dates to datetime objects if they're strings
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            
            if end_date is None:
                end_date = start_date + timedelta(days=1)
            elif isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Format as ISO strings for API request
            start_iso = start_date.isoformat()
            end_iso = end_date.isoformat()
            
            # Set up request parameters
            params = {
                'lat': lat,
                'lng': lon,
                'params': ','.join(self.weather_params),
                'start': start_iso,
                'end': end_iso,
                'source': 'sg'
            }
            
            headers = {
                'Authorization': self.api_key
            }
            
            logger.info(f"Fetching StormGlass data for {lat}, {lon} from {start_date} to {end_date}")
            
            # Make API request
            response = requests.get(
                self.weather_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            # Check for request limit errors
            if response.status_code == 429:
                logger.warning("StormGlass API rate limit exceeded. Waiting and trying again...")
                time.sleep(60)  # Wait for a minute before trying again
                response = requests.get(
                    self.weather_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Get tide data as well
            tide_data = self.get_tide_data(lat, lon, start_date, end_date)
            
            # Add tide data to the response
            if tide_data:
                data['tides'] = tide_data
            
            logger.info(f"Successfully retrieved data with {len(data.get('hours', []))} hourly records")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from StormGlass API: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting weather data: {str(e)}")
            return None
    
    def get_tide_data(self, lat, lon, start_date, end_date=None):
        """
        Fetch tide data for a specific location and time range.
        
        Args:
            lat (float): Latitude of the location
            lon (float): Longitude of the location
            start_date (datetime): Start date
            end_date (datetime, optional): End date. Defaults to start_date+1
        
        Returns:
            dict: Tide data from StormGlass
        """
        try:
            if end_date is None:
                end_date = start_date + timedelta(days=1)
            
            # Format as ISO strings for API request
            start_iso = start_date.isoformat()
            end_iso = end_date.isoformat()
            
            # Set up request parameters
            params = {
                'lat': lat,
                'lng': lon,
                'start': start_iso,
                'end': end_iso,
                'datum': 'MLLW'  # Mean Lower Low Water
            }
            
            headers = {
                'Authorization': self.api_key
            }
            
            logger.info(f"Fetching StormGlass tide data for {lat}, {lon} from {start_date} to {end_date}")
            
            # Make API request
            response = requests.get(
                self.tide_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            # Check for request limit errors
            if response.status_code == 429:
                logger.warning("StormGlass API rate limit exceeded. Waiting and trying again...")
                time.sleep(60)  # Wait for a minute before trying again
                response = requests.get(
                    self.tide_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tide data from StormGlass API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting tide data: {str(e)}")
            return None
    
    def get_historical_data(self, lat, lon, date, days_before=2):
        """
        Get weather data for a specific date and the days before it.
        Now computes daily averages for each required weather parameter from hourly data.
        """
        try:
            # Convert date to datetime if it's a string
            if isinstance(date, str):
                date = datetime.strptime(date, '%Y-%m-%d')
            # Calculate start date (days_before days before target date)
            start_date = date - timedelta(days=days_before)
            # Get weather data for the whole period
            data = self.get_weather_data(lat, lon, start_date, date + timedelta(days=1))
            if not data or 'hours' not in data:
                logger.error("Failed to get historical data")
                return None
            # Process the data into daily records
            daily_data = {}
            # Group hours by day
            for hour_data in data['hours']:
                time_str = hour_data['time']
                hour_date = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                day_str = hour_date.strftime('%Y-%m-%d')
                if day_str not in daily_data:
                    daily_data[day_str] = []
                daily_data[day_str].append(hour_data)
            # Calculate daily averages and build result
            result = {
                'target_date': date.strftime('%Y-%m-%d'),
                'days_data': {}
            }
            weather_params = [
                'airTemperature', 'waterTemperature', 'windSpeed', 'windDirection',
                'swellHeight', 'swellPeriod', 'swellDirection', 'cloudCover',
                'humidity', 'pressure', 'precipitation', 'visibility'
            ]
            for day_str, hours in daily_data.items():
                # Calculate how many days before the target date this is
                day_date = datetime.strptime(day_str, '%Y-%m-%d')
                days_diff = (date - day_date).days
                # Calculate daily averages for each required field
                day_weather = {}
                for param in weather_params:
                    values = []
                    for hour in hours:
                        val = None
                        if param in hour and isinstance(hour[param], dict):
                            val = hour[param].get('sg')
                        if val is not None:
                            values.append(val)
                    if values:
                        day_weather[param] = {'sg': sum(values) / len(values)}
                # Add tides if available
                if 'tides' in data and 'data' in data['tides']:
                    day_tides = [tide for tide in data['tides']['data'] if day_str in tide['time']]
                    if day_tides:
                        day_weather['tides'] = day_tides
                result['days_data'][int(days_diff)] = {
                    'date': day_str,
                    'weather': day_weather,
                    'hours': hours  # Include all hourly data as well
                }
            return result
        except Exception as e:
            logger.error(f"Error processing historical data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def extract_noaa_value(self, param):
        if isinstance(param, dict):
            val = param.get('sg')
            if val is None:
                val = param.get('noaa')
            return val
        elif isinstance(param, list) and param and isinstance(param[0], dict):
            val = param[0].get('sg')
            if val is None:
                val = param[0].get('noaa')
            return val
        return None

    def format_for_visibility_model(self, historical_data):
        """
        Format the historical data for use with the visibility prediction model.
        Extracts 'noaa' values from each parameter dict. Only uses records where all required fields are present.
        """
        if not historical_data or 'days_data' not in historical_data:
            return None
        try:
            # Get target date data (0 days ago)
            target_data = historical_data['days_data'].get(0, {}).get('weather', {})
            if not target_data:
                logger.error("Target date data not available")
                return None

            # List of required fields
            required_fields = [
                'waterTemperature', 'airTemperature', 'windSpeed', 'windDirection',
                'swellHeight', 'swellPeriod', 'swellDirection', 'cloudCover',
                'humidity', 'pressure', 'precipitation', 'visibility'
            ]
            extracted = {f: self.extract_noaa_value(target_data.get(f)) for f in required_fields}
            missing = [f for f, v in extracted.items() if v is None]
            if missing:
                logger.warning(f"Missing required Stormglass fields: {missing}. Skipping this record.")
                return None

            formatted_data = {
                'date': historical_data['target_date'],
                'water_temp_c': extracted['waterTemperature'],
                'air_temp_c': extracted['airTemperature'],
                'wind_speed_kmph': extracted['windSpeed'] * 3.6,
                'wind_degree': extracted['windDirection'],
                'swell_height_m': extracted['swellHeight'],
                'swell_period_s': extracted['swellPeriod'],
                'swell_direction_degree': extracted['swellDirection'],
                'cloud_cover_pct': extracted['cloudCover'],
                'humidity_pct': extracted['humidity'],
                'pressure_hPa': extracted['pressure'],
                'precipitation_mm': extracted['precipitation'],
                'visibility_km': extracted['visibility'],
            }

            # Add derived features
            formatted_data['diff_wind_swell_dir_deg'] = abs(formatted_data['wind_degree'] - formatted_data['swell_direction_degree'])
            if formatted_data['diff_wind_swell_dir_deg'] > 180:
                formatted_data['diff_wind_swell_dir_deg'] = 360 - formatted_data['diff_wind_swell_dir_deg']
            formatted_data['swell_steepness'] = formatted_data['swell_height_m'] / (formatted_data['swell_period_s'] ** 2) if formatted_data['swell_period_s'] > 0 else 0
            formatted_data['interaction_wind_swell'] = formatted_data['wind_speed_kmph'] * formatted_data['swell_height_m']

            # Add historical data (lagged features)
            for days_ago in range(1, 3):  # Add 1 and 2 days ago
                if days_ago in historical_data['days_data']:
                    past_data = historical_data['days_data'][days_ago]['weather']
                    # Only add lagged features if all required fields are present
                    lag_fields = ['waterTemperature', 'windSpeed', 'swellHeight', 'precipitation']
                    lag_extracted = {f: self.extract_noaa_value(past_data.get(f)) for f in lag_fields}
                    if all(v is not None for v in lag_extracted.values()):
                        formatted_data[f'water_temp_c_{days_ago}d_ago'] = lag_extracted['waterTemperature']
                        formatted_data[f'wind_speed_kmph_{days_ago}d_ago'] = lag_extracted['windSpeed'] * 3.6
                        formatted_data[f'swell_height_m_{days_ago}d_ago'] = lag_extracted['swellHeight']
                        formatted_data[f'precipitation_mm_{days_ago}d_ago'] = lag_extracted['precipitation']
            return formatted_data
        except Exception as e:
            logger.error(f"Error formatting data for visibility model: {str(e)}")
            return None

def main():
    """Test the StormGlass API client and print raw response for analysis."""
    try:
        client = StormGlassClient()
        
        # Test location
        lat = -32.02336
        lon = 115.445429
        
        # Test dates
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get historical data
        historical_data = client.get_historical_data(lat, lon, today, days_before=2)
        
        if historical_data:
            print(f"Successfully retrieved historical data for {today} and 2 days before\n")
            print("RAW historical_data response:")
            print(json.dumps(historical_data, indent=2))
            print("\n---\n")
            # Print the target_data for the target date (0 days ago)
            target_data = historical_data['days_data'].get(0, {}).get('weather', {})
            print("Target day 'weather' data:")
            print(json.dumps(target_data, indent=2))
            print("\n---\n")
            # Try to format for visibility model (will still fail if fields missing)
            formatted_data = client.format_for_visibility_model(historical_data)
            if formatted_data:
                print("Formatted data for visibility model:")
                print(json.dumps(formatted_data, indent=2))
                with open('stormglass_test_data.json', 'w') as f:
                    json.dump(formatted_data, f, indent=2)
                print("Saved formatted data to stormglass_test_data.json")
            else:
                print("Failed to format data for visibility model")
        else:
            print("Failed to retrieve historical data")
            
    except Exception as e:
        print(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main() 