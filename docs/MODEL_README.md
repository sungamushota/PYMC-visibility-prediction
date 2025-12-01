# Underwater Visibility Prediction Model

## Overview
This hierarchical Bayesian model predicts underwater visibility at Western Australian dive sites based on weather and oceanographic conditions.

## Model Performance
- **MAE**: 2.67 meters
- **RMSE**: 3.75 meters
- **R²**: 0.3961 (explains ~40% of variance)
- **Accuracy**: 69.79% of predictions within ±3m, 80.73% within ±4m

## Required Files

### Essential Files (Required for Predictions)
1. **`stormglass_pymc_hierarchical_extended_idata.nc`** (2.8 MB)
   - The trained PyMC Bayesian model with all posterior distributions
   
2. **`stormglass_pymc_hierarchical_extended_scaler.pkl`** (2 KB)
   - StandardScaler for feature normalization
   
3. **`stormglass_pymc_hierarchical_extended_predictors.pkl`** (1 KB)
   - List of 30 predictor features the model expects
   
4. **`predict_visibility.py`** 
   - Python script for making predictions

### Optional Files (For Reference)
5. **`stormglass_pymc_hierarchical_extended_coefficient_summary.csv`**
   - Feature importance and coefficient values
   
6. **`site_performance_metrics.csv`**
   - Performance metrics for each dive site
   
7. **`site_coordinates.json`**
   - GPS coordinates for all dive sites

## Required Python Packages

```bash
pip install pandas numpy scikit-learn pymc arviz matplotlib
```

Specific versions (recommended):
```
pandas>=2.0
numpy>=1.26,<2.0
scikit-learn>=1.3
pymc>=5.0
arviz>=0.17
```

## Usage

### Command Line
```bash
# Basic prediction
python predict_visibility.py --input weather_data.csv --output predictions.csv

# Prediction for specific site
python predict_visibility.py --input weather_data.csv --output predictions.csv --site AMJ
```

### Python Script
```python
from predict_visibility import VisibilityPredictor

# Initialize predictor
predictor = VisibilityPredictor(model_dir='models')

# Load your data
import pandas as pd
data = pd.read_csv('weather_data.csv')

# Make predictions
predictions = predictor.predict(data, site_code='AMJ')

# Get predictions with uncertainty
results = predictor.predict_with_uncertainty(data, site_code='AMJ')
print(f"Predicted: {results['mean']:.2f}m")
print(f"95% CI: [{results['lower_95']:.2f}, {results['upper_95']:.2f}]m")

# View feature importance
importance = predictor.get_feature_importance()
print(importance.head(10))
```

## Input Data Format

The model requires the following features (columns in your CSV):

### Required Rolling Average Features (2, 3, and 4-day):
- `airTemperature_2day_roll_avg`, `airTemperature_3day_roll_avg`, `airTemperature_4day_roll_avg`
- `waterTemperature_2day_roll_avg`, `waterTemperature_3day_roll_avg`, `waterTemperature_4day_roll_avg`
- `windSpeed_2day_roll_avg`, `windSpeed_3day_roll_avg`, `windSpeed_4day_roll_avg`
- `waveHeight_2day_roll_avg`, `waveHeight_3day_roll_avg`, `waveHeight_4day_roll_avg`
- `swellHeight_2day_roll_avg`, `swellHeight_3day_roll_avg`, `swellHeight_4day_roll_avg`
- `cloudCover_2day_roll_avg`, `cloudCover_3day_roll_avg`, `cloudCover_4day_roll_avg`
- `pressure_2day_roll_avg`, `pressure_3day_roll_avg`, `pressure_4day_roll_avg`
- `precipitation_2day_roll_avg`, `precipitation_3day_roll_avg`, `precipitation_4day_roll_avg`

### Additional Features:
- `precipitation_sum_last_24h` - Total precipitation in last 24 hours
- `precipitation_sum_last_48h` - Total precipitation in last 48 hours
- `DateTime_UTC` - Timestamp (for calculating temporal features)

### Optional (auto-calculated from DateTime_UTC):
- `day_of_year_sin`, `day_of_year_cos` - Seasonal patterns
- `month_sin`, `month_cos` - Monthly patterns

## Dive Sites

The model has site-specific adjustments for 24 Western Australian dive sites:

| Code | Site Name | Avg Visibility | Best Performance |
|------|-----------|----------------|------------------|
| AMJ | Ammo Jetty | 3.6m | MAE: 1.87m |
| BIC | Bicton Baths | 5.3m | MAE: 1.81m |
| BSJ | Busselton Jetty | 15.7m | MAE: 12.79m |
| BUL | Bulk Jetty | 4.2m | MAE: 1.68m |
| BWR | Blackwall Reach | 2.6m | MAE: 10.06m |
| CAM | Camilla Wreck | 8.7m | MAE: 3.91m |
| CMB | The Coombe & Mosman Bay | 2.9m | MAE: 2.37m |
| CMT | Coogee Maritime Trail | 4.2m | MAE: 2.10m |
| FRE | South Fremantle | 5.3m | MAE: 2.94m |
| FWB | Freshwater Bay | 4.0m | MAE: 1.13m ⭐ |
| HIL | Hillarys | 8.8m | MAE: 4.96m |
| KGT | Kwinana Grain Terminal | 6.0m | MAE: 2.02m |
| MET | Mettam's Pool | 5.8m | MAE: 2.60m |
| NMF | North Mole Fremantle | 8.3m | MAE: 4.52m |
| PPR | Point Peron | 7.2m | MAE: 2.17m |
| PRT | Port Beach | 7.0m | MAE: 3.37m |
| RKM | Rockingham Dive Trail | 6.5m | MAE: 7.56m |
| RNN | Rottnest North | 14.3m | MAE: 4.06m |
| RNW | Rottnest West | 20.0m | MAE: 7.55m |
| RTS | Rottnest South | 13.3m | MAE: 7.68m |
| ROB | Robbs Jetty | 7.0m | MAE: 2.17m |
| SCR | South Cottesloe Reef | 7.2m | MAE: 3.93m |
| WAT | Watermans/North Beach | 3.6m | MAE: 1.57m |
| WOO | Woodman Point | 5.3m | MAE: 3.28m |

⭐ Best performing site

## Model Architecture

- **Type**: Hierarchical Bayesian Model (PyMC)
- **Sampling**: NUTS (No-U-Turn Sampler)
- **Chains**: 2
- **Draws**: 2,000 per chain (4,000 total)
- **Tuning**: 1,000 steps
- **Divergences**: 0 (excellent convergence)
- **Features**: 30 predictors (weather, oceanographic, temporal)
- **Hierarchy**: Global effects + site-specific random effects

## Top Predictive Features

1. **month_cos** (-0.17) - Seasonal patterns (winter/summer)
2. **swellHeight** (rolling averages) (-0.11) - Larger swells reduce visibility
3. **waveHeight** (rolling averages) (+0.07 to +0.08) - Wave patterns
4. **day_of_year_cos** (+0.09) - Annual patterns
5. **precipitation** (24h/48h sums) (-0.04 to -0.03) - Rain reduces visibility

## Limitations

1. **Site-specific**: Best performance for sites with more training data
2. **Weather-based**: Cannot account for local factors (construction, storms, etc.)
3. **Temporal**: Most accurate for 1-5 day forecasts
4. **Range**: Better accuracy for visibility < 10m

## Training Data

- **Records**: 912 visibility reports (after filtering)
- **Date Range**: Multiple years of historical data
- **Sites**: 24 dive sites across Western Australia
- **Sources**: Diver reports + StormGlass weather API

## Contact & Citation

Model developed: December 2025
Training duration: ~3 minutes (MCMC sampling)
Framework: PyMC + ArviZ

For questions or issues, please contact the model maintainer.

