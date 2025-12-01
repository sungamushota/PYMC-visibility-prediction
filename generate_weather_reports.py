import pandas as pd
from datetime import datetime, timedelta, timezone
import numpy as np # For NaN and potentially other numeric ops
import time # For potential delays in API calls
from stormglass_api_client import StormGlassClient # Assuming it's in the same directory or path
import json # For loading site_coordinates
import argparse # Added for command-line arguments
import os # Added for directory creation and path joining

# CONFIGURATION
DAYS_BEFORE = 3 # Fetch data for report date and 3 days before (total 4 days)
API_CALL_DELAY_SECONDS = 1 # To be nice to the API
OUTPUT_DIRECTORY = "stormglass_output" # Define the output directory

# Define the exact parameters expected from StormGlass hourly data based on client's list
# This helps in creating consistent columns, especially for the wide CSV
EXPECTED_HOURLY_PARAMS = [
    'airTemperature', 'waterTemperature', 'windSpeed', 'windDirection',
    'waveHeight', 'wavePeriod', 'waveDirection', 'swellHeight',
    'swellPeriod', 'swellDirection', 'cloudCover', 'humidity',
    'precipitation', 'visibility', 'pressure', 'gust', 'seaLevel'
]

def main():
    # --- Add ArgumentParser for row limit ---
    parser = argparse.ArgumentParser(description='Generate weather reports by fetching data from StormGlass API.')
    parser.add_argument('--limit', type=int, help='Limit the number of rows to process from VIS_Reports_Augmented.csv for testing.')
    args = parser.parse_args()
    # --- End ArgumentParser setup ---

    # --- Create output directory ---
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    print(f"Output files will be saved to: {os.path.abspath(OUTPUT_DIRECTORY)}")
    # --- End create output directory ---

    # 1. Load Inputs
    try:
        df_reports_in = pd.read_csv('VIS_Reports_Augmented.csv')
    except FileNotFoundError:
        print("Error: VIS_Reports_Augmented.csv not found. Please ensure it exists.")
        return
    
    # Convert DateTime_UTC safely
    if 'DateTime_UTC' in df_reports_in.columns:
        df_reports_in['DateTime_UTC'] = pd.to_datetime(df_reports_in['DateTime_UTC'], errors='coerce')
        # Drop rows where DateTime_UTC could not be parsed, as it's crucial
        df_reports_in.dropna(subset=['DateTime_UTC'], inplace=True)
    else:
        print("Error: DateTime_UTC column not found in VIS_Reports_Augmented.csv.")
        return

    try:
        with open('site_coordinates.json', 'r') as f:
            site_coords = json.load(f)
    except FileNotFoundError:
        print("Error: site_coordinates.json not found.")
        return

    # 2. Add report_id
    df_reports_in.reset_index(drop=True, inplace=True) # Ensure clean index
    df_reports_in['report_id'] = df_reports_in.index

    # --- Apply row limit if provided ---
    if args.limit is not None and args.limit > 0:
        print(f"--- PROCESSING LIMITED TO FIRST {args.limit} REPORTS --- ")
        df_reports_in = df_reports_in.head(args.limit)
    # --- End apply row limit ---

    client = StormGlassClient()

    all_hourly_data_records = []
    all_tide_extreme_records = []
    all_data_wide_list = []

    for index, report_row in df_reports_in.iterrows():
        report_id = report_row['report_id']
        site_full_name = report_row.get('site') # Get the full name like "Ammo Jetty (AMJ)"
        
        site_abbreviation = None
        if site_full_name and '(' in site_full_name and ')' in site_full_name:
            try:
                # Extract abbreviation, e.g., "AMJ" from "Ammo Jetty (AMJ)"
                site_abbreviation = site_full_name.split('(')[-1].split(')')[0].strip()
            except IndexError:
                # This might happen if the format is not as expected, e.g. no closing parenthesis
                print(f"Warning: Could not parse site abbreviation from '{site_full_name}' for report_id {report_id}.")
                pass
        
        lat, lon = None, None
        if site_abbreviation and site_abbreviation in site_coords:
            lat = site_coords[site_abbreviation].get('lat')
            lon = site_coords[site_abbreviation].get('lon')
        
        report_datetime_utc = report_row['DateTime_UTC']

        if lat is None or lon is None:
            print(f"Warning: Missing coordinates for site '{site_full_name}' (parsed abbr: '{site_abbreviation}') (report_id {report_id}). Skipping API calls.")
            current_wide_row = report_row.to_dict()
            all_data_wide_list.append(current_wide_row)
            continue

        report_date_str = report_datetime_utc.strftime('%Y-%m-%d')
        # Use site_abbreviation for the print message now if available, else full name
        site_identifier_for_log = site_abbreviation if site_abbreviation else site_full_name
        print(f"Processing report_id {report_id} for date {report_date_str} at site {site_identifier_for_log} ({lat},{lon})...")

        try:
            historical_storm_data = client.get_historical_data(lat, lon, report_date_str, days_before=DAYS_BEFORE)
            time.sleep(API_CALL_DELAY_SECONDS)

            if not historical_storm_data or 'days_data' not in historical_storm_data:
                print(f"Warning: No historical Storm Glass data returned for report_id {report_id}.")
                current_wide_row = report_row.to_dict()
                all_data_wide_list.append(current_wide_row)
                continue
            
            current_wide_row = report_row.to_dict()

            for days_ago_val in range(DAYS_BEFORE + 1):
                day_data_dict = historical_storm_data.get('days_data', {}).get(days_ago_val)
                
                if day_data_dict and 'hours' in day_data_dict and day_data_dict['hours']:
                    day_date_obj_str = day_data_dict['date'] # YYYY-MM-DD string from historical_data output
                    
                    for hour_entry in day_data_dict['hours']:
                        hour_timestamp_utc = datetime.fromisoformat(hour_entry['time'].replace('Z', '+00:00'))
                        
                        # For wide CSV column naming
                        # days_ago_val is 0 for report day, 1 for D-1, etc.
                        prefix_wide = f"D{days_ago_val}_H{hour_timestamp_utc.strftime('%H')}_"
                        
                        hourly_record_for_df = {'report_id': report_id, 'weather_timestamp_utc': hour_timestamp_utc}
                        
                        for param_name in EXPECTED_HOURLY_PARAMS:
                            value = None
                            if param_name in hour_entry and isinstance(hour_entry[param_name], dict):
                                value = hour_entry[param_name].get('sg')
                            
                            current_wide_row[prefix_wide + param_name] = value
                            hourly_record_for_df[param_name] = value
                        
                        all_hourly_data_records.append(hourly_record_for_df)

                # Tides are at the root of historical_storm_data, not per day_data_dict in that structure
            if historical_storm_data.get('tides') and 'data' in historical_storm_data['tides']:
                for days_ago_val_tide in range(DAYS_BEFORE + 1): # Iterate D0, D-1, D-2, D-3
                    # Determine the actual date for this days_ago_val_tide
                    current_processing_date = (report_datetime_utc - timedelta(days=days_ago_val_tide)).date()
                    tide_counter_for_day = 1
                    for tide_event in historical_storm_data['tides']['data']:
                        tide_event_time = datetime.fromisoformat(tide_event['time'].replace('Z', '+00:00'))
                        if tide_event_time.date() == current_processing_date:
                            prefix_wide_tide = f"D{days_ago_val_tide}_Tide{tide_counter_for_day}_"
                            current_wide_row[prefix_wide_tide + 'time'] = tide_event_time.strftime('%H:%M:%S')
                            current_wide_row[prefix_wide_tide + 'height'] = tide_event['height']
                            current_wide_row[prefix_wide_tide + 'type'] = tide_event['type']
                            tide_counter_for_day += 1
                            
                            all_tide_extreme_records.append({
                                'report_id': report_id,
                                'tide_event_date_utc': current_processing_date,
                                'tide_event_time_utc': tide_event_time,
                                'tide_event_height': tide_event['height'],
                                'tide_event_type': tide_event['type']
                            })
            all_data_wide_list.append(current_wide_row)

        except Exception as e:
            print(f"ERROR processing report_id {report_id} for site {site_identifier_for_log}: {e}")
            import traceback
            traceback.print_exc()
            current_wide_row = report_row.to_dict() # Save original data at least
            all_data_wide_list.append(current_wide_row)
            continue

    # 4. Process and Save CSVs
    df_all_data_wide = pd.DataFrame(all_data_wide_list)
    # Rename visibility columns in df_all_data_wide
    rename_map_wide = {col: col.replace('_visibility', '_atmospheric_visibility_km') 
                       for col in df_all_data_wide.columns if '_visibility' in col}
    if rename_map_wide:
        df_all_data_wide.rename(columns=rename_map_wide, inplace=True)
    df_all_data_wide.to_csv(os.path.join(OUTPUT_DIRECTORY, 'all_data_wide.csv'), index=False)
    print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'all_data_wide.csv')}")

    if not all_hourly_data_records:
        print("No hourly data was collected. Skipping remaining CSVs.")
        return

    df_all_hourly = pd.DataFrame(all_hourly_data_records)
    df_all_hourly['weather_date_utc'] = df_all_hourly['weather_timestamp_utc'].dt.date

    # Generate report_day_hourly.csv
    df_report_day_hourly_list = []
    for index, report_row_filter in df_reports_in.iterrows():
        report_id_filter = report_row_filter['report_id']
        report_date_filter = report_row_filter['DateTime_UTC'].date()
        subset = df_all_hourly[(df_all_hourly['report_id'] == report_id_filter) & (df_all_hourly['weather_date_utc'] == report_date_filter)]
        df_report_day_hourly_list.append(subset)
    
    if df_report_day_hourly_list:
        df_report_day_hourly_final = pd.concat(df_report_day_hourly_list)
        if not df_report_day_hourly_final.empty:
            df_report_day_hourly_final_long = df_report_day_hourly_final.copy() # Keep a copy for long format saving
            df_report_day_hourly_final_long.drop(columns=['weather_date_utc'], inplace=True, errors='ignore')
            if 'visibility' in df_report_day_hourly_final_long.columns: # Name before long save
                 df_report_day_hourly_final_long.rename(columns={'visibility': 'atmospheric_visibility_km'}, inplace=True)
            df_report_day_hourly_final_long.to_csv(os.path.join(OUTPUT_DIRECTORY, 'report_day_hourly.csv'), index=False)
            print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'report_day_hourly.csv')} (long format)")

            # --- Create WIDE format for report_day_hourly --- 
            df_pivot = df_report_day_hourly_final.copy()
            if 'visibility' in df_pivot.columns: # Rename before pivot 
                 df_pivot.rename(columns={'visibility': 'atmospheric_visibility_km'}, inplace=True)
            
            df_pivot['hour_str'] = df_pivot['weather_timestamp_utc'].dt.strftime('H%H')
            # Columns to pivot, excluding identifiers already used or created for pivot
            value_vars = [col for col in df_pivot.columns if col not in ['report_id', 'weather_timestamp_utc', 'weather_date_utc', 'hour_str']]
            
            if value_vars: # Ensure there are columns to pivot
                report_day_hourly_wide_df = df_pivot.pivot_table(
                    index='report_id',
                    columns='hour_str',
                    values=value_vars
                )
                # Flatten the multi-level column index
                report_day_hourly_wide_df.columns = [f'{val_col}_{hour_col}' for val_col, hour_col in report_day_hourly_wide_df.columns]
                report_day_hourly_wide_df.reset_index(inplace=True)
                
                # Merge with original non-pivoted columns from df_reports_in to retain them
                original_report_cols = [col for col in df_reports_in.columns if col not in report_day_hourly_wide_df.columns or col == 'report_id']
                report_day_hourly_wide_df = pd.merge(df_reports_in[original_report_cols], report_day_hourly_wide_df, on='report_id', how='left')

                report_day_hourly_wide_df.to_csv(os.path.join(OUTPUT_DIRECTORY, 'report_day_hourly_wide.csv'), index=False)
                print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'report_day_hourly_wide.csv')}")
            else:
                print(f"Skipped {os.path.join(OUTPUT_DIRECTORY, 'report_day_hourly_wide.csv')} generation as no value columns found for pivoting.")
            # --- End WIDE format for report_day_hourly ---

    # Generate daily_averages.csv
    agg_funcs = {col: 'mean' for col in EXPECTED_HOURLY_PARAMS if col != 'precipitation'}
    if 'precipitation' in EXPECTED_HOURLY_PARAMS:
         agg_funcs['precipitation'] = 'sum'
    
    # Ensure all expected columns are present for aggregation, fill with NaN if not
    for param in EXPECTED_HOURLY_PARAMS:
        if param not in df_all_hourly.columns:
            df_all_hourly[param] = np.nan

    df_daily_averages = df_all_hourly.groupby(['report_id', 'weather_date_utc'])[EXPECTED_HOURLY_PARAMS].agg(agg_funcs).reset_index()
    
    # --- Filter daily_averages to keep only rows for the actual report date ---
    # Create a mapping of report_id to its actual report date
    df_reports_in['report_date_only_utc'] = df_reports_in['DateTime_UTC'].dt.date
    report_id_to_actual_date = df_reports_in.set_index('report_id')['report_date_only_utc'].to_dict()
    
    # Apply the filter
    # Keep rows where (report_id, weather_date_utc) matches (report_id, actual_report_date_for_that_id)
    df_daily_averages = df_daily_averages[
        df_daily_averages.apply(lambda row: row['weather_date_utc'] == report_id_to_actual_date.get(row['report_id']), axis=1)
    ]
    # --- End filter ---

    # Rename visibility column
    if 'visibility' in df_daily_averages.columns: # Check if original 'visibility' exists before renaming
        df_daily_averages.rename(columns={'visibility': 'atmospheric_visibility_km'}, inplace=True)
    
    # --- Merge original report data into daily_averages ---
    cols_to_merge_from_original = [col for col in df_reports_in.columns if col not in df_daily_averages.columns or col == 'report_id']
    # Ensure report_date_only_utc is not duplicated if it was used for filtering df_daily_averages join key
    if 'report_date_only_utc' in cols_to_merge_from_original and 'weather_date_utc' in df_daily_averages.columns:
        # df_daily_averages.weather_date_utc IS the report_date_only_utc after filtering
        pass # No special handling needed if keys align

    df_daily_averages = pd.merge(df_reports_in[cols_to_merge_from_original], df_daily_averages, on='report_id', how='right')
    # df_daily_averages might have report_date_only_utc from merge and weather_date_utc. Drop one if identical.
    if 'report_date_only_utc' in df_daily_averages.columns and 'weather_date_utc' in df_daily_averages.columns and df_daily_averages['report_date_only_utc'].equals(df_daily_averages['weather_date_utc']):
        df_daily_averages.drop(columns=['report_date_only_utc'], inplace=True)

    df_daily_averages.to_csv(os.path.join(OUTPUT_DIRECTORY, 'daily_averages.csv'), index=False)
    print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'daily_averages.csv')} (one row per report, for report date, with original data)")

    # Generate daily_rolling_averages.csv
    if not df_daily_averages.empty:
        # Ensure the column to be used for rolling average renaming is correct before groupby
        # If df_daily_averages has 'atmospheric_visibility_km', it will be used.
        # If it has 'visibility', it should have been renamed above. This is just a safeguard.
        if 'visibility' in df_daily_averages.columns and 'atmospheric_visibility_km' not in df_daily_averages.columns:
             df_daily_averages.rename(columns={'visibility': 'atmospheric_visibility_km'}, inplace=True)

        df_daily_averages_sorted = df_daily_averages.sort_values(by=['report_id', 'weather_date_utc'])
        
        rolling_windows = [2, 3, 4] # Define the window sizes you want
        all_reports_rolling_data_list = []

        for report_id_val, group in df_daily_averages_sorted.groupby('report_id'):
            # Select only numeric columns for rolling mean from EXPECTED_HOURLY_PARAMS
            # Handle renaming of 'visibility' to 'atmospheric_visibility_km' for selection if needed
            numeric_cols_for_rolling_selection = []
            for p in EXPECTED_HOURLY_PARAMS:
                col_to_check = 'atmospheric_visibility_km' if p == 'visibility' else p
                if col_to_check in group.columns and pd.api.types.is_numeric_dtype(group[col_to_check]):
                    numeric_cols_for_rolling_selection.append(col_to_check)
            
            # DataFrame to hold all rolling window calculations for this group
            # Start with the identifiers from the group
            group_rolling_combined = group[['report_id', 'weather_date_utc']].reset_index(drop=True)

            for window_size in rolling_windows:
                group_rolling_current_window = group[numeric_cols_for_rolling_selection].rolling(window=window_size, min_periods=1).mean()
                # Ensure column names for rolling avgs are consistent
                group_rolling_current_window.columns = [
                    f'{col.replace("visibility", "atmospheric_visibility_km")}_{window_size}day_roll_avg' 
                    if "visibility" in col else f'{col}_{window_size}day_roll_avg' 
                    for col in numeric_cols_for_rolling_selection
                ]
                
                # Merge with the group_rolling_combined
                group_rolling_combined = pd.concat([group_rolling_combined, group_rolling_current_window.reset_index(drop=True)], axis=1)
            
            all_reports_rolling_data_list.append(group_rolling_combined)

        if all_reports_rolling_data_list:
            df_rolling_averages_calc = pd.concat(all_reports_rolling_data_list)
            
            # Filter to keep only the rolling average for the actual report date
            df_reports_in_id_date = df_reports_in[['report_id', 'DateTime_UTC']].copy()
            df_reports_in_id_date['weather_date_utc'] = df_reports_in_id_date['DateTime_UTC'].dt.date
            
            df_rolling_for_report_date = pd.merge(df_rolling_averages_calc, df_reports_in_id_date[['report_id', 'weather_date_utc']],
                                                 on=['report_id', 'weather_date_utc'], how='inner')

            # Precipitation sums
            precip_sums_list = []
            for _, report_row_precip in df_reports_in.iterrows():
                report_id_precip = report_row_precip['report_id']
                report_dt_utc = report_row_precip['DateTime_UTC']
                
                report_hourly_subset = df_all_hourly[df_all_hourly['report_id'] == report_id_precip]
                precip_24h, precip_48h = np.nan, np.nan # Default to NaN
                if 'precipitation' in report_hourly_subset.columns and not report_hourly_subset['precipitation'].isnull().all():
                    mask_24h = (report_hourly_subset['weather_timestamp_utc'] > (report_dt_utc - timedelta(hours=24))) & \
                               (report_hourly_subset['weather_timestamp_utc'] <= report_dt_utc)
                    precip_24h = report_hourly_subset.loc[mask_24h, 'precipitation'].sum(min_count=1) # min_count=1 returns NaN if all are NaN
                    
                    mask_48h = (report_hourly_subset['weather_timestamp_utc'] > (report_dt_utc - timedelta(hours=48))) & \
                               (report_hourly_subset['weather_timestamp_utc'] <= report_dt_utc)
                    precip_48h = report_hourly_subset.loc[mask_48h, 'precipitation'].sum(min_count=1)

                precip_sums_list.append({
                    'report_id': report_id_precip,
                    'precipitation_sum_last_24h': precip_24h,
                    'precipitation_sum_last_48h': precip_48h
                })
            df_precip_sums = pd.DataFrame(precip_sums_list)
            
            df_daily_rolling_combined = pd.merge(df_rolling_for_report_date, df_precip_sums, on='report_id', how='left')
            # The renaming for rolling averages columns is now handled inside the loop building group_rolling_current_window.columns

            # --- Merge original report data into daily_rolling_combined ---
            df_daily_rolling_combined = pd.merge(df_reports_in[cols_to_merge_from_original], df_daily_rolling_combined, on='report_id', how='right')
            if 'report_date_only_utc' in df_daily_rolling_combined.columns and 'weather_date_utc' in df_daily_rolling_combined.columns and df_daily_rolling_combined['report_date_only_utc'].equals(df_daily_rolling_combined['weather_date_utc']):
                 df_daily_rolling_combined.drop(columns=['report_date_only_utc'], inplace=True)
            # --- End merge ---

            df_daily_rolling_combined.to_csv(os.path.join(OUTPUT_DIRECTORY, 'daily_rolling_averages.csv'), index=False)
            print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'daily_rolling_averages.csv')} (one row per report, with original data)")

    if all_tide_extreme_records:
        df_all_tides = pd.DataFrame(all_tide_extreme_records)
        df_all_tides.to_csv(os.path.join(OUTPUT_DIRECTORY, 'all_daily_tide_extremes.csv'), index=False)
        print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'all_daily_tide_extremes.csv')}")

    # --- Generate report_time_weather_snapshot.csv ---
    if not df_all_hourly.empty:
        snapshot_records = []
        for index, report_row in df_reports_in.iterrows():
            report_id = report_row['report_id']
            report_time_utc = report_row['DateTime_UTC']

            if pd.isna(report_time_utc):
                print(f"Skipping snapshot for report_id {report_id} due to missing DateTime_UTC.")
                snapshot_record = report_row.to_dict()
                for param in EXPECTED_HOURLY_PARAMS:
                    col_name_to_check = 'atmospheric_visibility_km' if param == 'visibility' else param
                    if col_name_to_check not in snapshot_record:
                         snapshot_record[col_name_to_check] = np.nan 
                snapshot_records.append(snapshot_record)
                continue

            hourly_data_for_report_day = df_all_hourly[
                (df_all_hourly['report_id'] == report_id) &
                (df_all_hourly['weather_timestamp_utc'].dt.date == report_time_utc.date())
            ].copy()

            if hourly_data_for_report_day.empty:
                print(f"No hourly data found for report_id {report_id} on its report date for snapshot. Appending original data only.")
                snapshot_record = report_row.to_dict()
                for param in EXPECTED_HOURLY_PARAMS:
                    col_name_to_check = 'atmospheric_visibility_km' if param == 'visibility' else param
                    if col_name_to_check not in snapshot_record:
                         snapshot_record[col_name_to_check] = np.nan 
                snapshot_records.append(snapshot_record)
                continue
            
            hourly_data_for_report_day['time_diff'] = (hourly_data_for_report_day['weather_timestamp_utc'] - report_time_utc).abs()
            closest_hour_record = hourly_data_for_report_day.loc[hourly_data_for_report_day['time_diff'].idxmin()]
            
            snapshot_record = report_row.to_dict()
            weather_cols_to_add = closest_hour_record.drop(['report_id', 'weather_date_utc', 'time_diff', 'weather_timestamp_utc'])
            
            if 'visibility' in weather_cols_to_add.index:
                weather_cols_to_add.rename(index={'visibility': 'atmospheric_visibility_km'}, inplace=True)
            
            snapshot_record.update(weather_cols_to_add)
            snapshot_record['closest_weather_hour_utc'] = closest_hour_record['weather_timestamp_utc']
            snapshot_records.append(snapshot_record)

        if snapshot_records:
            df_snapshot = pd.DataFrame(snapshot_records)
            df_snapshot.to_csv(os.path.join(OUTPUT_DIRECTORY, 'report_time_weather_snapshot.csv'), index=False)
            print(f"Saved {os.path.join(OUTPUT_DIRECTORY, 'report_time_weather_snapshot.csv')}")
    # --- End snapshot generation ---

    # --- Generate README.md ---
    readme_content = f"""# Storm Glass Data Output

This directory contains data generated by `generate_weather_reports.py`.
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Input Files Used:

- `VIS_Reports_Augmented.csv`: Contains the original augmented visibility reports, including observed visibility and `DateTime_UTC` for each report.
- `site_coordinates.json`: Contains latitude and longitude for dive sites, keyed by site abbreviation.

## Output Files Generated:

1.  **`all_data_wide.csv`**
    -   **Structure**: One row per original visibility report.
    -   **Content**: Includes all original report data, plus hourly Storm Glass weather data for the report day (D0) and {DAYS_BEFORE} prior days (D1, D2, D3) flattened into wide columns (e.g., `D0_H00_airTemperature`, `D1_H00_airTemperature`). Also includes flattened tide extreme data for these days.
    -   The `atmospheric_visibility_km` columns (e.g. `D0_H00_atmospheric_visibility_km`) come from the Storm Glass API.

2.  **`report_day_hourly.csv` (long format)**
    -   **Structure**: Multiple rows per original report (typically 24, one for each hour of the report day).
    -   **Content**: Contains `report_id`, `weather_timestamp_utc`, and hourly Storm Glass weather parameters for the actual day of the original visibility report.
    -   The `atmospheric_visibility_km` column comes from the Storm Glass API.

3.  **`report_day_hourly_wide.csv`**
    -   **Structure**: One row per original visibility report.
    -   **Content**: Includes all original report data, plus hourly Storm Glass weather data for the *report day only*, flattened into wide columns (e.g., `airTemperature_H00`, `atmospheric_visibility_km_H00`).

4.  **`daily_averages.csv`**
    -   **Structure**: One row per original visibility report.
    -   **Content**: Includes all original report data, plus daily averages (or sums for precipitation) of Storm Glass weather parameters for the *actual day of the original visibility report*.
    -   The `atmospheric_visibility_km` column represents the daily average of hourly atmospheric visibility from Storm Glass for the report day.

5.  **`daily_rolling_averages.csv`**
    -   **Structure**: One row per original visibility report.
    -   **Content**: Includes all original report data. For each weather parameter, it provides 2-day, 3-day, and 4-day rolling averages calculated from daily averages, culminating on the report date (e.g., `airTemperature_2day_roll_avg`, `atmospheric_visibility_km_4day_roll_avg`). Also includes precipitation sums for the 24 and 48 hours leading up to the original report's `DateTime_UTC`.

6.  **`all_daily_tide_extremes.csv`**
    -   **Structure**: Multiple rows, listing each tide extreme (high/low) event for each of the {DAYS_BEFORE + 1} days fetched for each report.
    -   **Content**: `report_id`, `tide_event_date_utc`, `tide_event_time_utc`, `tide_event_height`, `tide_event_type`.

7.  **`report_time_weather_snapshot.csv`**
    -   **Structure**: One row per original visibility report.
    -   **Content**: Includes all original report data, plus the Storm Glass weather parameters for the single hour closest to the original report's `DateTime_UTC`. A `closest_weather_hour_utc` column indicates the timestamp of the weather data used.
    -   The `atmospheric_visibility_km` column comes from the Storm Glass API for that specific hour.

## General Notes:

-   `report_id` in all generated files links back to the original `VIS_Reports_Augmented.csv` (specifically, its index after loading and resetting).
-   The `atmospheric_visibility_km` parameter in these files is derived from the Storm Glass API and represents atmospheric conditions (e.g., clarity in km), not the diver-observed underwater visibility from your original reports.

"""
    readme_path = os.path.join(OUTPUT_DIRECTORY, 'README.md')
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    print(f"Saved README.md to {readme_path}")
    # --- End README.md generation ---

    print("Processing complete.")

if __name__ == '__main__':
    main() 