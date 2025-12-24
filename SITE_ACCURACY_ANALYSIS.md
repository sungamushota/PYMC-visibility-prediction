# Site Accuracy and Feature Correlation Analysis

## Summary

This analysis investigates why some sites with many visibility reports (repeats) have poor prediction accuracy, and visualizes feature correlations with visibility.

## Key Findings

### Sites with Many Repeats but Poor Accuracy

Three sites stand out as having many samples but poor accuracy:

1. **RKM (Rockingham Dive Trail)**: 60 samples, MAE = 7.56m
2. **NMF (North Mole Fremantle)**: 54 samples, MAE = 4.52m  
3. **SCR (South Cottesloe Reef)**: 72 samples, MAE = 3.93m

### Why These Sites Have Poor Accuracy?

#### 1. High Visibility Variability
All three problem sites show **high coefficient of variation (CV)**:
- **RKM**: CV = 0.58 (visibility ranges from 1-15m)
- **NMF**: CV = 0.61 (visibility ranges from 1-25m)
- **SCR**: CV = 0.63 (visibility ranges from 1-20m)

In contrast, high-accuracy sites like **AMJ** (MAE=1.87m) and **BUL** (MAE=1.68m) have:
- Lower average visibility (3.6m and 4.2m respectively)
- More consistent visibility patterns

#### 2. Site-Specific Feature Relationships
The problem sites show **different feature correlations** compared to the global model:

**RKM (Rockingham Dive Trail)**:
- Swell height has **positive** correlation (+0.31) at this site, but **negative** globally (-0.16)
- Swell direction is highly correlated (+0.37) locally but weakly correlated globally
- This suggests the model's global relationships don't apply well here

**NMF (North Mole Fremantle)**:
- Air temperature is highly correlated (+0.35) locally but weakly correlated globally (+0.02)
- Precipitation shows **positive** correlation (+0.28) locally but **negative** globally (-0.07)
- This site may have unique local conditions affecting visibility

**SCR (South Cottesloe Reef)**:
- Swell height shows stronger negative correlation (-0.38) than global (-0.16)
- Wave direction correlations differ significantly from global patterns

### Comparison with High-Accuracy Sites

Sites with many samples and **good** accuracy (MAE < 2.5m):
- **AMJ** (Ammo Jetty): 86 samples, MAE = 1.87m, Avg visibility = 3.6m
- **KGT** (Kwinana Grain Terminal): 73 samples, MAE = 2.02m, Avg visibility = 6.0m
- **BUL** (Bulk Jetty): 56 samples, MAE = 1.68m, Avg visibility = 4.2m

These sites have:
- Lower visibility variability
- Feature relationships that align better with global patterns
- More consistent environmental conditions

## Feature Correlations with Visibility

### Top Correlated Features (Global)

1. **Humidity** (2-4 day rolling): +0.17 correlation
   - Higher humidity associated with better visibility

2. **Swell Height** (2-4 day rolling): -0.16 correlation
   - Higher swell height associated with lower visibility

3. **Swell Period** (2-4 day rolling): -0.12 correlation
   - Longer swell periods associated with lower visibility

4. **Gust** (2-4 day rolling): +0.10 correlation
   - Higher wind gusts associated with better visibility

5. **Wave Height** (2-4 day rolling): -0.10 correlation
   - Higher waves associated with lower visibility

6. **Precipitation** (24-48h sums): -0.07 to -0.09 correlation
   - Recent rain reduces visibility

### Key Insights

- **Swell characteristics** (height, period) are the strongest predictors
- **Temporal features** (rolling averages) capture delayed effects better than instantaneous values
- **Precipitation** has immediate negative impact (24-48h window)
- Most correlations are relatively weak (<0.2), suggesting visibility is influenced by complex interactions

## Recommendations

### For Improving Model Accuracy

1. **Site-Specific Models**: Consider building separate models for high-variability sites (RKM, NMF, SCR) that account for their unique feature relationships

2. **Feature Engineering**: 
   - Add interaction terms for sites where feature relationships differ
   - Consider site-specific feature transformations

3. **Data Collection**: 
   - Focus on collecting more data for sites with high variability
   - Investigate local conditions that might explain site-specific patterns

4. **Model Architecture**:
   - The hierarchical Bayesian model already includes site effects, but may need stronger site-specific coefficients for problem sites
   - Consider allowing site-specific feature coefficients, not just intercepts

### For Understanding Visibility Patterns

1. **Environmental Factors**: Investigate why certain sites (like RKM) show opposite relationships (e.g., swell height positively correlated)

2. **Geographic Patterns**: Analyze if sites with similar poor accuracy share geographic or oceanographic characteristics

3. **Temporal Patterns**: Check if poor accuracy correlates with specific seasons or weather patterns

## Files Generated

- `plots/site_accuracy_analysis.png`: Visualizations showing:
  - MAE vs number of samples
  - Visibility range vs prediction error
  - Coefficient of variation vs prediction error
  - Average visibility vs prediction error

- `plots/feature_correlations_visibility.png`: Visualizations showing:
  - Top 30 features correlated with visibility
  - Correlation heatmap by feature type and rolling window

- `models/feature_correlations_visibility.csv`: Detailed correlation data for all features

## Next Steps

1. Investigate site-specific environmental conditions (bathymetry, currents, local weather patterns)
2. Build site-specific sub-models for problem sites
3. Collect additional data for high-variability sites during different seasons
4. Explore non-linear relationships and feature interactions
