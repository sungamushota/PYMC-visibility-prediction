# Site Accuracy and Feature Correlation Analysis

## Executive Summary

This analysis investigates two key questions:
1. **Why do some sites with many reports have poor prediction accuracy?**
2. **Which weather features are most correlated with visibility?**

## Key Findings

### 1. Sites with More Reports ≠ Better Accuracy

**Statistical Analysis:**
- Correlation between Sample Size and MAE: r = -0.289 (p = 0.172) - **NOT significant**
- Correlation between Sample Size and R²: r = 0.153 (p = 0.476) - **NOT significant**

**Conclusion:** There is NO statistically significant relationship between the number of reports and prediction accuracy. More data does not automatically lead to better predictions.

---

### 2. Problematic Sites (>50 reports with MAE > 3m)

Three sites stand out as having poor accuracy despite many observations:

#### **Rockingham Dive Trail (RKM)** - WORST PERFORMER
- **Total Reports:** 60
- **Average Visibility:** 6.5m
- **MAE:** 7.56m (very high!)
- **RMSE:** 8.88m
- **R² Score:** -4.59 (much worse than baseline!)
- **Within 3m Accuracy:** Only 8.3%
- **Coefficient of Variation:** 58.1% (moderate variability)

**Problem:** The model performs extremely poorly at this site. The R² of -4.59 means the model is nearly 5x worse than simply predicting the mean visibility every time.

#### **North Mole Fremantle (NMF)**
- **Total Reports:** 54
- **Average Visibility:** 8.3m
- **MAE:** 4.52m
- **R² Score:** -0.98
- **Within 3m Accuracy:** 36.4%
- **Coefficient of Variation:** 60.9% (moderate-high variability)

**Problem:** Moderate-high variability in visibility, with readings ranging from 1m to 25m.

#### **South Cottesloe Reef (SCR)**
- **Total Reports:** 72 (most reports!)
- **Average Visibility:** 7.2m
- **MAE:** 3.93m
- **R² Score:** -0.44
- **Within 3m Accuracy:** 46.7%
- **Coefficient of Variation:** 63.3% (moderate-high variability)

**Problem:** Despite having the most reports, visibility is highly variable (1m to 20m range).

---

### 3. Why Are These Sites Hard to Predict?

**Analysis of Visibility Variability:**

Sites with high variability (high Coefficient of Variation) tend to have worse prediction accuracy:

| Site | CV (%) | MAE (m) | Interpretation |
|------|--------|---------|----------------|
| AMJ  | 65.9%  | 1.87    | High variability, but good accuracy (low avg visibility helps) |
| SCR  | 63.3%  | 3.93    | High variability → poor accuracy |
| NMF  | 60.9%  | 4.52    | High variability → poor accuracy |
| RKM  | 58.1%  | 7.56    | Moderate variability, but VERY poor accuracy (other factors) |
| CMT  | 61.8%  | 2.10    | High variability, but good accuracy |

**Key Insight:** Variability alone doesn't fully explain poor accuracy. Other factors must be at play:
- **Site-specific conditions** not captured by weather features
- **Local water quality** variations
- **Proximity to river outflows** (e.g., NMF near Swan River)
- **Depth variations** at the site
- **Diver activity** stirring up sediment

---

### 4. Feature Correlations with Visibility

**Most Important Positive Correlations:**
(Higher values → Better visibility)

1. **Humidity** (r = 0.152) - Surprisingly positive
2. **Gust** (r = 0.114) - Wind gusts associated with better visibility
3. **Atmospheric Visibility** (r = 0.033) - Weak correlation

**Most Important Negative Correlations:**
(Higher values → Worse visibility)

1. **Swell Height** (r = -0.164) - STRONGEST predictor!
2. **Swell Period** (r = -0.117)
3. **Wave Height** (r = -0.103)
4. **Wave Period** (r = -0.098)
5. **Wind Direction** (r = -0.068)

**Key Insight:** **Wave and swell conditions are the most important predictors of underwater visibility!**
- Larger swells → More sediment stirred up → Lower visibility
- Longer swell periods → More energy → More disturbance
- Higher waves have similar negative effects

**Weaker than Expected:**
- Precipitation (r = -0.035) - Very weak
- Cloud cover (r = 0.004) - Essentially zero
- Wind speed (r = 0.002) - Essentially zero
- Air temperature (r = 0.030) - Very weak
- Water temperature (r = 0.015) - Very weak

---

### 5. Recommendations for Improvement

#### **For Model Performance:**

1. **Add Site-Specific Features:**
   - Distance from river mouths/outflows
   - Bottom depth at dive site
   - Bottom composition (sand/rock/seagrass)
   - Typical current patterns
   
2. **Add Temporal Features:**
   - Days since last storm
   - Recent rainfall (past 7 days)
   - Tidal range and timing
   - Season of year
   
3. **Consider Separate Models:**
   - Build site-specific models for problematic sites (RKM, NMF, SCR)
   - Or use a hierarchical/mixed-effects approach with more flexible site effects

4. **Feature Engineering:**
   - Wave energy index (combining height and period)
   - Swell direction relative to site orientation
   - Interaction terms (e.g., wind_speed × wind_direction)

#### **For Data Collection:**

1. **Improve Data Quality for Problematic Sites:**
   - Collect more detailed notes about local conditions
   - Record depth at which visibility was measured
   - Note any unusual events (dredging, algal blooms, etc.)
   
2. **Add New Measurements:**
   - Turbidity/sediment sensors
   - Current velocity measurements
   - Recent rainfall in nearby catchments

---

## Visualizations Generated

1. **`site_reports_vs_accuracy_analysis.png`**
   - 4-panel plot showing relationship between number of reports and accuracy metrics
   - Color-coded by average visibility
   - Annotated with worst performers

2. **`feature_correlation_heatmap_full.png`**
   - Comprehensive correlation matrix of all weather features
   - Shows inter-feature correlations
   - Lower triangle only for clarity

3. **`visibility_feature_correlations.png`**
   - Bar chart of all features correlated with visibility
   - Green bars = positive correlation (higher → better vis)
   - Red bars = negative correlation (higher → worse vis)
   - **Most useful for understanding which features matter!**

4. **`site_visibility_variability_analysis.png`**
   - Box plots showing visibility distribution at each high-sample site
   - Coefficient of variation chart color-coded by MAE
   - Shows which sites have high variability

5. **`key_feature_scatter_plots.png`**
   - Scatter plots of top 10 most correlated features vs visibility
   - Includes trend lines
   - Shows correlation coefficients

---

## Conclusion

**Main Takeaways:**

1. ✅ **More data does NOT automatically mean better predictions**
2. ✅ **Swell and wave conditions are the strongest predictors of visibility**
3. ⚠️ **Some sites (RKM, NMF, SCR) have unique challenges not captured by weather data alone**
4. ✅ **Visibility variability contributes to prediction difficulty, but isn't the whole story**
5. 💡 **Model could be significantly improved with site-specific and temporal features**

**Next Steps:**
- Consider collecting the additional features recommended above
- Investigate site-specific models for problematic locations
- Consider a mixed-effects model that allows different feature weights per site
- Explore non-linear relationships (e.g., random forests, gradient boosting)
