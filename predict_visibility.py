#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visibility Prediction Script
Uses the trained hierarchical Bayesian model to predict underwater visibility
based on weather and oceanographic conditions.

Usage:
    python predict_visibility.py --input data.csv --output predictions.csv
    
Or use in Python:
    from predict_visibility import VisibilityPredictor
    predictor = VisibilityPredictor()
    predictions = predictor.predict(data_df)
"""

import pandas as pd
import numpy as np
import pickle
import arviz as az
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class VisibilityPredictor:
    """
    Hierarchical Bayesian model for predicting underwater visibility.
    
    Model Performance (Test Set):
    - MAE: 2.67 meters
    - RMSE: 3.75 meters
    - R²: 0.3961
    - 69.79% of predictions within ±3m
    - 80.73% of predictions within ±4m
    """
    
    def __init__(self, model_dir='models'):
        """
        Initialize the predictor by loading the trained model.
        
        Args:
            model_dir: Directory containing model files
        """
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.predictors = None
        self.site_effects = None
        self.intercept = None
        self.beta_coefficients = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the trained model and associated files."""
        print("Loading model files...")
        
        # Load PyMC model
        model_path = f'{self.model_dir}/stormglass_pymc_hierarchical_extended_idata.nc'
        self.model = az.from_netcdf(model_path)
        
        # Load scaler
        scaler_path = f'{self.model_dir}/stormglass_pymc_hierarchical_extended_scaler.pkl'
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        # Load predictor list
        predictors_path = f'{self.model_dir}/stormglass_pymc_hierarchical_extended_predictors.pkl'
        with open(predictors_path, 'rb') as f:
            self.predictors = pickle.load(f)
        
        # Extract model parameters
        self.intercept = self.model.posterior["intercept"].mean().item()
        self.beta_coefficients = self.model.posterior["beta_predictors"].mean(dim=("chain", "draw")).values
        self.site_effects = self.model.posterior["a_site_actual_dev"].mean(dim=("chain", "draw")).values
        
        print(f"✓ Model loaded successfully")
        print(f"✓ Using {len(self.predictors)} predictors")
        print(f"✓ {len(self.site_effects)} site-specific effects available")
    
    def prepare_features(self, df):
        """
        Prepare features from raw data.
        
        Args:
            df: DataFrame with raw weather/oceanographic data
            
        Returns:
            DataFrame with processed features ready for prediction
        """
        df = df.copy()
        
        # Add temporal features if DateTime_UTC column exists
        if 'DateTime_UTC' in df.columns:
            df['DateTime_UTC'] = pd.to_datetime(df['DateTime_UTC'])
            df['year'] = df['DateTime_UTC'].dt.year
            df['month'] = df['DateTime_UTC'].dt.month
            df['day_of_year'] = df['DateTime_UTC'].dt.dayofyear
            df['day_of_year_sin'] = np.sin(2 * np.pi * df['day_of_year']/365)
            df['day_of_year_cos'] = np.cos(2 * np.pi * df['day_of_year']/365)
            df['month_sin'] = np.sin(2 * np.pi * df['month']/12)
            df['month_cos'] = np.cos(2 * np.pi * df['month']/12)
        
        # Select required predictors
        X = df[self.predictors].copy()
        
        # Impute missing values
        imputer = SimpleImputer(strategy='median')
        X_imputed = imputer.fit_transform(X)
        X = pd.DataFrame(X_imputed, columns=self.predictors, index=X.index)
        
        return X
    
    def predict(self, df, site_code=None, use_site_effect=True):
        """
        Predict visibility for given conditions.
        
        Args:
            df: DataFrame with weather/oceanographic features
            site_code: Dive site code (3-letter code like 'AMJ', 'BWR', etc.)
                      If None, uses global average (no site-specific adjustment)
            use_site_effect: Whether to apply site-specific effects
            
        Returns:
            numpy array of predicted visibility values (meters)
        """
        # Prepare features
        X = self.prepare_features(df)
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make predictions (in log space)
        y_pred_log = self.intercept + np.dot(X_scaled, self.beta_coefficients)
        
        # Add site-specific effect if requested
        if use_site_effect and site_code is not None:
            # Map site codes to indices (0-23 for 24 sites)
            # This is a simplified version - in production you'd want a proper mapping
            site_mapping = {
                'AMJ': 0, 'BIC': 1, 'BSJ': 2, 'BUL': 3, 'BWR': 4, 'CAM': 5,
                'CMB': 6, 'CMT': 7, 'FRE': 8, 'FWB': 9, 'HIL': 10, 'KGT': 11,
                'MET': 12, 'NMF': 13, 'PPR': 14, 'PRT': 15, 'RKM': 16, 'RNN': 17,
                'ROB': 18, 'RTS': 19, 'RNW': 20, 'SCR': 21, 'WAT': 22, 'WOO': 23
            }
            
            if site_code in site_mapping:
                site_idx = site_mapping[site_code]
                site_effect = self.site_effects[site_idx]
                y_pred_log += site_effect
                print(f"Applied site-specific effect for {site_code}: {site_effect:.3f}")
            else:
                print(f"Warning: Unknown site code '{site_code}', using global average")
        
        # Transform back to original scale
        y_pred = np.exp(y_pred_log)
        
        return y_pred
    
    def predict_with_uncertainty(self, df, site_code=None, n_samples=1000):
        """
        Predict visibility with uncertainty estimates (credible intervals).
        
        Args:
            df: DataFrame with weather/oceanographic features
            site_code: Dive site code
            n_samples: Number of posterior samples to use for uncertainty estimation
            
        Returns:
            Dictionary with 'mean', 'lower_95', 'upper_95' predictions
        """
        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        
        # Sample from posterior
        intercept_samples = self.model.posterior["intercept"].values.flatten()[:n_samples]
        beta_samples = self.model.posterior["beta_predictors"].values.reshape(-1, len(self.predictors))[:n_samples]
        
        predictions = []
        for i in range(n_samples):
            y_log = intercept_samples[i] + np.dot(X_scaled, beta_samples[i])
            predictions.append(np.exp(y_log))
        
        predictions = np.array(predictions)
        
        return {
            'mean': predictions.mean(axis=0),
            'lower_95': np.percentile(predictions, 2.5, axis=0),
            'upper_95': np.percentile(predictions, 97.5, axis=0),
            'std': predictions.std(axis=0)
        }
    
    def get_feature_importance(self):
        """
        Get feature importance based on coefficient magnitudes.
        
        Returns:
            DataFrame with predictors and their importance
        """
        importance_df = pd.DataFrame({
            'predictor': self.predictors,
            'coefficient': self.beta_coefficients,
            'abs_coefficient': np.abs(self.beta_coefficients)
        })
        
        return importance_df.sort_values('abs_coefficient', ascending=False)


def main():
    """Example usage of the predictor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Predict underwater visibility')
    parser.add_argument('--input', type=str, help='Input CSV file with weather data')
    parser.add_argument('--output', type=str, help='Output CSV file for predictions')
    parser.add_argument('--site', type=str, default=None, help='Site code (e.g., AMJ, BWR)')
    
    args = parser.parse_args()
    
    if args.input:
        # Load data
        data = pd.read_csv(args.input)
        print(f"Loaded {len(data)} records from {args.input}")
        
        # Initialize predictor
        predictor = VisibilityPredictor()
        
        # Make predictions
        predictions = predictor.predict(data, site_code=args.site)
        
        # Add predictions to dataframe
        data['predicted_visibility_m'] = predictions
        
        # Save results
        output_file = args.output or 'predictions.csv'
        data.to_csv(output_file, index=False)
        print(f"\n✓ Predictions saved to {output_file}")
        print(f"  Mean predicted visibility: {predictions.mean():.2f}m")
        print(f"  Range: {predictions.min():.2f}m to {predictions.max():.2f}m")
    else:
        print("No input file specified. Use --input to provide data file.")
        print("\nExample usage:")
        print("  python predict_visibility.py --input weather_data.csv --output predictions.csv --site AMJ")


if __name__ == "__main__":
    main()

