# Visibility Prediction Project Workflow

This document outlines the 3-step process for collecting data, training the visibility model, and running predictions.

## 1. Data Collection and Feature Engineering

This step fetches the necessary weather data and processes it to create the features required by the model, such as daily and rolling averages.

-   **Script:** `generate_weather_reports.py`
-   **Input:** Raw data from APIs (like Stormglass) and existing CSV files (e.g., `VIS_Reports_Augmented.csv`).
-   **Output:** `stormglass_output/daily_rolling_averages.csv`
-   **Command:**
    ```bash
    python generate_weather_reports.py
    ```

## 2. Model Training

This step uses the processed data to train the hierarchical Bayesian model. The most recent version of the model is the "extended" version, which includes 2, 3, and 4-day rolling averages as features.

-   **Script:** `stormglass_pymc_hierarchical_extended.py`
-   **Input:** `stormglass_output/daily_rolling_averages.csv`
-   **Outputs:**
    -   `models/stormglass_pymc_hierarchical_extended_idata.nc` (The trained model)
    -   `models/stormglass_pymc_hierarchical_extended_scaler.pkl` (The feature scaler)
    -   `models/stormglass_pymc_hierarchical_extended_predictors.pkl` (The list of model predictors)
-   **Command:**
    ```bash
    python stormglass_pymc_hierarchical_extended.py
    ```

## 3. Making Predictions

This final step uses the trained model and a live data fetch to predict visibility for a given site and time period. It can output a plot, a CSV file, and a summary to the console.

-   **Script:** `predict_with_stormglass_period.py`
-   **Inputs:**
    -   A site code (e.g., `AMJ`)
    -   A start and end date
    -   The trained model files from Step 2.
-   **Outputs:**
    -   A forecast plotted to a `.png` file.
    -   A `.csv` file with detailed prediction results (if requested).
    -   A summary printed to the console.

### Example Command

To get a 7-day forecast for site `AMJ` using the latest "extended" model, run the following command. Note the use of the `--model` and `--scaler` flags to point to the correct files.

```bash
python predict_with_stormglass_period.py AMJ 2024-12-15 --end-date 2024-12-21 \
--model models/stormglass_pymc_hierarchical_extended_idata.nc \
--scaler models/stormglass_pymc_hierarchical_extended_scaler.pkl \
--save-csv
``` 