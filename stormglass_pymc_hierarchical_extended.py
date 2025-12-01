#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Extended Hierarchical Bayesian Model for Underwater Visibility using StormGlass Data
This version includes 2-day, 3-day, and 4-day rolling averages
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
import os
import pickle
import warnings
warnings.filterwarnings('ignore')

import pymc as pm
import arviz as az

print("Script: stormglass_pymc_hierarchical_extended.py started")
print("This version includes 2-day, 3-day, and 4-day rolling averages")

# Create directories for outputs
os.makedirs('plots', exist_ok=True)
os.makedirs('models', exist_ok=True)
print("Output directories ensured")

# --- Global Model Parameters ---
RANDOM_SEED = 42
N_SAMPLES = 2000
N_TUNE = 1000
N_CHAINS = 2
print(f"Global sampling parameters set: SEED={RANDOM_SEED}, SAMPLES={N_SAMPLES}, TUNE={N_TUNE}, CHAINS={N_CHAINS}")

# --- Step 1: Load and Prepare Data ---
print("\nStep 1: Loading and Preparing StormGlass Data")
data_path = 'stormglass_output/daily_rolling_averages.csv'
try:
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records from {data_path}")
except Exception as e:
    print(f"Error loading data from {data_path}: {e}")
    exit()

target_variable = 'visibility'
site_identifier = 'site'
log_target_variable = 'log_visibility'
site_codes_col = f"{site_identifier}_code"

print(f"Target: '{target_variable}', Site ID: '{site_identifier}'")

df[log_target_variable] = np.log(df[target_variable].clip(lower=0.1))
print(f"Log-transformed target '{log_target_variable}' created.")
df.dropna(subset=[log_target_variable], inplace=True)
print(f"Data after removing NaNs in '{log_target_variable}': {df.shape}")

min_samples_per_site = 10
site_counts = df[site_identifier].value_counts()
common_sites = site_counts[site_counts >= min_samples_per_site].index
df = df[df[site_identifier].isin(common_sites)].copy()
print(f"Filtered for {len(common_sites)} sites with >= {min_samples_per_site} samples. Data shape: {df.shape}")

if df.empty:
    print("No data left after filtering sites. Exiting.")
    exit()

df[site_codes_col] = pd.Categorical(df[site_identifier]).codes
print(f"Created integer site codes in '{site_codes_col}'. Unique codes: {df[site_codes_col].nunique()}")

# --- Step 2: Select Extended Predictors ---
print("\nStep 2: Selecting Extended Predictors (2, 3, and 4-day rolling averages)")

# Base weather parameters
base_params = [
    'windSpeed',
    'waveHeight',
    'precipitation',
    'airTemperature',
    'waterTemperature',
    'swellHeight',
    'cloudCover',
    'pressure'
]

# Create list of predictors with all rolling windows
selected_predictors_raw = []
for param in base_params:
    for window in [2, 3, 4]:
        col_name = f'{param}_{window}day_roll_avg'
        if col_name in df.columns:
            selected_predictors_raw.append(col_name)
        else:
            print(f"Warning: {col_name} not found in data")

# Add precipitation sums
selected_predictors_raw.extend([
    'precipitation_sum_last_24h',
    'precipitation_sum_last_48h'
])

# Add temporal features
if 'DateTime_UTC' in df.columns:
    df['DateTime_UTC'] = pd.to_datetime(df['DateTime_UTC'])
    df['year'] = df['DateTime_UTC'].dt.year
    df['month'] = df['DateTime_UTC'].dt.month
    df['day_of_year'] = df['DateTime_UTC'].dt.dayofyear
    df['day_of_year_sin'] = np.sin(2 * np.pi * df['day_of_year']/365)
    df['day_of_year_cos'] = np.cos(2 * np.pi * df['day_of_year']/365)
    df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
    df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
    print("Date features calculated.")
    time_features = ['day_of_year_sin', 'day_of_year_cos', 'month_sin', 'month_cos']
    selected_predictors_raw.extend(time_features)

final_predictors = [pred for pred in selected_predictors_raw if pred in df.columns]
print(f"Using {len(final_predictors)} predictors (including multiple rolling windows)")
print(f"Predictors by type:")
print(f"  - 2-day rolling: {sum('2day' in p for p in final_predictors)}")
print(f"  - 3-day rolling: {sum('3day' in p for p in final_predictors)}")
print(f"  - 4-day rolling: {sum('4day' in p for p in final_predictors)}")
print(f"  - Other features: {sum('day' not in p or 'sum' in p for p in final_predictors)}")

if not final_predictors:
    print("Error: No predictor columns found. Exiting.")
    exit()

X = df[final_predictors].copy()
y = df[log_target_variable].values
site_indices_for_split = df[site_codes_col].values

numeric_imputer = SimpleImputer(strategy='median')
X_imputed = numeric_imputer.fit_transform(X)
X = pd.DataFrame(X_imputed, columns=final_predictors, index=X.index)
print(f"Predictors imputed. Shape of X: {X.shape}")

# --- Site-aware train-test split ---
print("\nPerforming site-aware train-test split (80% train, 20% test per site)...")

train_indices = []
test_indices = []
np.random.seed(RANDOM_SEED)

for site_code in df[site_codes_col].unique():
    site_mask = df[site_codes_col] == site_code
    site_indices = df.index[site_mask].tolist()
    
    np.random.shuffle(site_indices)
    
    n_site_samples = len(site_indices)
    n_train = int(0.8 * n_site_samples)
    
    train_indices.extend(site_indices[:n_train])
    test_indices.extend(site_indices[n_train:])
    
    print(f"  Site {site_code}: {n_site_samples} total samples -> {n_train} train, {n_site_samples - n_train} test")

train_indices = np.array(sorted(train_indices))
test_indices = np.array(sorted(test_indices))

X_train = X.loc[train_indices]
X_test = X.loc[test_indices]
y_train = y[df.index.isin(train_indices)]
y_test = y[df.index.isin(test_indices)]
site_idx_train = site_indices_for_split[df.index.isin(train_indices)]
site_idx_test = site_indices_for_split[df.index.isin(test_indices)]

print(f"\nSite-aware split complete:")
print(f"  Total training samples: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
print(f"  Total test samples: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")

pred_scaler = StandardScaler()
X_train_scaled = pred_scaler.fit_transform(X_train)
X_test_scaled = pred_scaler.transform(X_test)
print("Predictors scaled.")

site_idx_train_int = site_idx_train.astype(int)
n_sites_train = len(np.unique(site_idx_train_int))
print(f"Number of unique sites in training data: {n_sites_train}")

# --- Step 3: Build Extended PyMC Model ---
print("\nStep 3: Building Extended PyMC Hierarchical Model")

idata_full = None
model_with_predictors = None

coords_full = {
    "site_train": np.unique(site_idx_train_int),
    "predictors": final_predictors,
    "obs_id_train": np.arange(len(y_train))
}

with pm.Model(coords=coords_full) as model_with_predictors:
    # Priors
    intercept = pm.Normal('intercept', mu=np.mean(y_train), sigma=2)
    
    # Use slightly tighter priors for coefficients since we have more predictors
    beta_predictors = pm.Normal('beta_predictors', mu=0, sigma=0.5, dims='predictors')
    
    # Site-level parameters
    sigma_site = pm.HalfCauchy('sigma_site', beta=1)
    a_site_offset = pm.Normal('a_site_offset', mu=0, sigma=1, dims='site_train')
    a_site_actual_dev = pm.Deterministic('a_site_actual_dev', a_site_offset * sigma_site, dims='site_train')
    
    # Linear predictor
    fixed_effects_mu = intercept + pm.math.dot(X_train_scaled, beta_predictors)
    mu = fixed_effects_mu + a_site_actual_dev[site_idx_train_int]
    
    # Observation model
    sigma_obs = pm.HalfCauchy('sigma_obs', beta=1)
    likelihood = pm.Normal('likelihood', mu=mu, sigma=sigma_obs, observed=y_train, dims='obs_id_train')
    
    print("Model definition complete. Starting sampling...")
    try:
        idata_full = pm.sample(
            draws=N_SAMPLES, 
            tune=N_TUNE, 
            chains=N_CHAINS, 
            random_seed=RANDOM_SEED, 
            progressbar=True, 
            cores=1
        )
        print("Sampling complete for extended model.")
        print("\nSummary of extended model (key parameters):")
        print(az.summary(idata_full, var_names=['intercept', 'sigma_site', 'sigma_obs']))
        
        # Show summary of beta coefficients grouped by rolling window
        print("\nCoefficient summary by rolling window:")
        beta_summary = az.summary(idata_full, var_names=['beta_predictors'])
        
        for window in [2, 3, 4]:
            window_cols = [i for i, col in enumerate(final_predictors) if f'{window}day' in col]
            if window_cols:
                print(f"\n{window}-day rolling averages:")
                print(beta_summary.iloc[window_cols][['mean', 'sd', 'hdi_3%', 'hdi_97%']])
        
        divergences_full = idata_full.sample_stats.diverging.sum().item()
        print(f"\nNumber of divergences: {divergences_full}")
        
    except Exception as e:
        print(f"Error during PyMC sampling: {e}")
        import traceback
        traceback.print_exc()
        exit()

print("\nModel fitting complete.")

# --- Step 4: Model Saving and Evaluation ---
print("\nStep 4: Model Saving, Prediction, and Evaluation")
model_name_prefix = "stormglass_pymc_hierarchical_extended"

if model_with_predictors is not None and idata_full is not None and X_test_scaled is not None:
    # Save model and scaler
    idata_filename = f'models/{model_name_prefix}_idata.nc'
    try:
        az.to_netcdf(idata_full, idata_filename)
        print(f"InferenceData saved to {idata_filename}")
    except Exception as e:
        print(f"Error saving InferenceData: {e}")
    
    scaler_filename = f'models/{model_name_prefix}_scaler.pkl'
    try:
        with open(scaler_filename, 'wb') as f:
            pickle.dump(pred_scaler, f)
        print(f"Predictor scaler saved to {scaler_filename}")
    except Exception as e:
        print(f"Error saving scaler: {e}")
    
    # Save predictor list
    predictors_filename = f'models/{model_name_prefix}_predictors.pkl'
    try:
        with open(predictors_filename, 'wb') as f:
            pickle.dump(final_predictors, f)
        print(f"Predictor list saved to {predictors_filename}")
    except Exception as e:
        print(f"Error saving predictors: {e}")
    
    # Make predictions
    try:
        unique_training_site_codes = np.unique(site_idx_train_int)
        a_site_dev_posterior_mean = idata_full.posterior["a_site_actual_dev"].mean(dim=("chain", "draw")).values
        test_site_effects = np.zeros(len(site_idx_test))
        
        for i, test_site_code in enumerate(site_idx_test):
            if test_site_code in unique_training_site_codes:
                training_idx_pos = np.where(unique_training_site_codes == test_site_code)[0][0]
                test_site_effects[i] = a_site_dev_posterior_mean[training_idx_pos]
        
        intercept_mean = idata_full.posterior["intercept"].mean().item()
        beta_predictors_mean = idata_full.posterior["beta_predictors"].mean(dim=("chain", "draw")).values
        
        y_pred_fixed_effects = intercept_mean + np.dot(X_test_scaled, beta_predictors_mean)
        y_pred_log_mean = y_pred_fixed_effects + test_site_effects
        
        y_pred_orig = np.exp(y_pred_log_mean)
        y_test_orig = np.exp(y_test)
        
        mae = mean_absolute_error(y_test_orig, y_pred_orig)
        rmse = np.sqrt(mean_squared_error(y_test_orig, y_pred_orig))
        r2 = r2_score(y_test_orig, y_pred_orig)
        
        print("\nExtended Model Performance (on original visibility scale - Test Set):")
        print(f"Mean Absolute Error: {mae:.2f} m")
        print(f"Root Mean Squared Error: {rmse:.2f} m")
        print(f"R² Score: {r2:.4f}")
        
        abs_diff = np.abs(y_pred_orig - y_test_orig)
        within_3m = np.mean(abs_diff <= 3) * 100
        within_4m = np.mean(abs_diff <= 4) * 100
        print(f"Percentage of predictions within +/- 3m of actual: {within_3m:.2f}%")
        print(f"Percentage of predictions within +/- 4m of actual: {within_4m:.2f}%")
        
        # Compare with original model (2-day only)
        print("\nComparison with original model (2-day rolling only):")
        print("Original model: MAE=2.67m, RMSE=3.75m, R²=0.3952")
        print(f"Extended model: MAE={mae:.2f}m, RMSE={rmse:.2f}m, R²={r2:.4f}")
        print(f"Improvement: MAE {2.67-mae:.2f}m, RMSE {3.75-rmse:.2f}m, R² {r2-0.3952:.4f}")
        
        # Plot actual vs predicted
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test_orig, y_pred_orig, alpha=0.6, label=f'R² = {r2:.3f}', c='blue')
        min_val = min(y_test_orig.min(), y_pred_orig.min()) * 0.95
        max_val = max(y_test_orig.max(), y_pred_orig.max()) * 1.05
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Ideal Fit')
        plt.xlabel('Actual Visibility (m)')
        plt.ylabel('Predicted Visibility (m)')
        plt.title('Extended Model: Actual vs Predicted Visibility (Test Set)')
        plt.legend()
        plt.grid(True)
        plot_filename = f'plots/{model_name_prefix}_actual_vs_predicted.png'
        plt.savefig(plot_filename)
        plt.close()
        print(f"Saved actual vs predicted plot to '{plot_filename}'")
        
    except Exception as e:
        print(f"Error during prediction/evaluation: {e}")
        import traceback
        traceback.print_exc()

# --- Step 5: Feature Importance Analysis ---
print("\nStep 5: Analyzing Feature Importance")

if 'idata_full' in locals() and idata_full is not None:
    try:
        # Extract coefficient means and standard deviations
        beta_means = idata_full.posterior["beta_predictors"].mean(dim=("chain", "draw")).values
        beta_stds = idata_full.posterior["beta_predictors"].std(dim=("chain", "draw")).values
        
        # Create DataFrame for analysis
        coef_df = pd.DataFrame({
            'predictor': final_predictors,
            'coefficient': beta_means,
            'std': beta_stds,
            'abs_coefficient': np.abs(beta_means)
        })
        
        # Add rolling window info
        coef_df['window'] = coef_df['predictor'].apply(
            lambda x: '2-day' if '2day' in x else ('3-day' if '3day' in x else ('4-day' if '4day' in x else 'other'))
        )
        
        # Sort by absolute coefficient
        coef_df = coef_df.sort_values('abs_coefficient', ascending=False)
        
        print("\nTop 15 Most Important Features:")
        print(coef_df.head(15)[['predictor', 'coefficient', 'window']])
        
        # Plot feature importance by window
        plt.figure(figsize=(12, 8))
        
        # Group by base parameter and window
        for i, param in enumerate(base_params):
            param_data = coef_df[coef_df['predictor'].str.contains(param)]
            if not param_data.empty:
                windows = ['2-day', '3-day', '4-day']
                coeffs = []
                for window in windows:
                    window_data = param_data[param_data['window'] == window]
                    if not window_data.empty:
                        coeffs.append(window_data['coefficient'].values[0])
                    else:
                        coeffs.append(0)
                
                plt.subplot(2, 4, i+1)
                plt.bar(windows, coeffs)
                plt.title(param)
                plt.ylabel('Coefficient')
                plt.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        plt.suptitle('Coefficient Values by Parameter and Rolling Window', y=1.02)
        importance_plot = f'plots/{model_name_prefix}_feature_importance_by_window.png'
        plt.savefig(importance_plot)
        plt.close()
        print(f"Saved feature importance plot to '{importance_plot}'")
        
        # Save coefficient summary
        coef_summary_file = f'models/{model_name_prefix}_coefficient_summary.csv'
        coef_df.to_csv(coef_summary_file, index=False)
        print(f"Saved coefficient summary to '{coef_summary_file}'")
        
    except Exception as e:
        print(f"Error during feature importance analysis: {e}")
        import traceback
        traceback.print_exc()

print("\nExtended model training complete!")
print("="*60)
print("SUMMARY:")
print(f"- Used {len(final_predictors)} predictors (2, 3, and 4-day rolling averages)")
print(f"- Model performance: MAE={mae:.2f}m, RMSE={rmse:.2f}m, R²={r2:.4f}")
print(f"- Model saved to: models/{model_name_prefix}_idata.nc")
print("="*60) 