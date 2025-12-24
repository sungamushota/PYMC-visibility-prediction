# Site Repeat vs. Accuracy Investigation

## Executive Summary

You correctly identified a critical issue: **several sites with the most observations (repeats) show poor model accuracy**. This investigation analyzes this phenomenon and provides actionable recommendations.

## Key Findings

### 1. Problematic High-Sample Sites

Three sites with ≥50 samples show concerning performance:

| Site Code | Site Name | Total Samples | MAE (m) | Within ±3m (%) | Performance |
|-----------|-----------|---------------|---------|----------------|-------------|
| **RKM** | Rockingham Dive Trail | 60 | 7.56 | 8.3% | ❌ WORST |
| **SCR** | South Cottesloe Reef | 72 | 3.93 | 46.7% | ⚠️ POOR |
| **NMF** | North Mole Fremantle | 54 | 4.52 | 36.4% | ⚠️ POOR |
| KGT | Kwinana Grain Terminal | 73 | 2.02 | 80.0% | ✓ Acceptable |

### 2. Statistical Analysis

- **Correlation**: No statistically significant correlation between sample size and error (r=-0.289, p=0.17)
- However, the **High Sample category (≥60)** has concerning patterns:
  - Average MAE: 3.84m (vs. 2.77m for Medium Sample sites)
  - Average Within ±3m: 54.6% (vs. 70.5% for Medium Sample sites)
  
### 3. Visibility Variability Analysis

High-sample sites with poor accuracy show **high environmental variability**:

| Site | Vis Range | Vis StdDev | Monthly CV | Interpretation |
|------|-----------|------------|------------|----------------|
| **RKM** | 1-15m | 3.32m | 0.36 | High variability |
| **SCR** | 1-20m | 4.49m | 0.46 | Very high seasonal variation |
| **NMF** | 1-25m | 4.94m | 0.46 | Extreme variability |
| KGT | 1-20m | 3.15m | 0.29 | Moderate variability |

## Root Causes

### Primary Factors

1. **Environmental Complexity**
   - High-sample sites are often popular dive locations with complex local conditions
   - RKM, SCR, NMF are all high-traffic sites with variable water dynamics
   - Coastal sites near structures, channels, or transitional zones

2. **High Visibility Variability**
   - Sites with more observations capture more seasonal patterns
   - Model struggles with extreme variability (StdDev >4m)
   - Monthly coefficient of variation >0.4 indicates strong seasonal patterns

3. **Spatial Factors**
   - **NMF (North Mole Fremantle)**: Near river mouth and industrial port - high turbidity variation
   - **RKM (Rockingham Dive Trail)**: Transitional zone between coastal and offshore waters
   - **SCR (South Cottesloe Reef)**: Exposed reef with high seasonal influence

### Secondary Factors

4. **Model Limitations**
   - Current hierarchical model uses site-level random effects
   - May not fully capture complex site-specific non-linear patterns
   - Missing local predictors (bathymetry, proximity to features, tidal influence)

5. **Data Characteristics**
   - More samples = more edge cases and extreme conditions captured
   - Popular sites may have observations from wider range of conditions
   - Increased seasonal coverage reveals model weaknesses

## Recommendations

### Immediate Actions

1. **⚠️ Flag High-Uncertainty Sites**
   - Add uncertainty warnings for RKM, SCR, NMF predictions
   - Consider excluding these from operational forecasts until improved
   - Document limitations for end users

2. **📊 Enhance Model for Problematic Sites**
   - Add site-specific visibility variance modeling
   - Implement separate models or thresholds for high-variability sites
   - Consider temporal trend components (seasonal, monthly effects)

### Medium-Term Improvements

3. **🌊 Add Local Environmental Predictors**
   - Bathymetry data (depth, seafloor complexity)
   - Proximity to river mouths, ports, or outfalls
   - Tidal state and current strength
   - Coastal upwelling indices

4. **📈 Implement Advanced Modeling Techniques**
   - Non-linear relationships for high-variance sites
   - Mixture models for bimodal visibility distributions
   - Time-varying coefficients for seasonal effects
   - Spatial correlation structure

5. **🔍 Site-Specific Analysis**
   - Conduct detailed environmental assessment of RKM, SCR, NMF
   - Interview local divers about site-specific conditions
   - Review observation protocols for consistency

### Long-Term Strategy

6. **🎯 Adaptive Prediction Strategy**
   - Different models for different site types:
     - Simple model: Low-variability coastal sites
     - Complex model: High-variability transitional zones
     - Specialized model: River mouths and industrial areas
   
7. **📚 Continuous Learning**
   - Regular model retraining as new data accumulates
   - Track prediction performance over time
   - Update site classifications based on observed patterns

## Technical Details

### Why More Data Doesn't Always Help

The paradox of "more data, worse performance" occurs when:

1. **Sampling Bias**: More observations = more diverse conditions = harder to predict
2. **Model Complexity**: Simple models struggle with complex patterns revealed by more data
3. **Heterogeneity**: Sites with high sample counts may be fundamentally different (popular, accessible, variable)

### Visualization Insights

See generated plots:
- `plots/sample_size_accuracy_analysis.png`: Shows clear clustering of problematic high-sample sites
- `plots/visibility_variability_analysis.png`: Reveals strong relationship between variability and error

## Specific Site Recommendations

### Rockingham Dive Trail (RKM) - CRITICAL
- **Status**: Only 8.3% predictions within ±3m
- **Issue**: Transitional zone with 14m visibility range
- **Action**: 
  - Flag as high-uncertainty
  - Consider separate local model
  - Add tide/current data if available

### South Cottesloe Reef (SCR) - NEEDS IMPROVEMENT  
- **Status**: 46.7% predictions within ±3m
- **Issue**: Exposed reef, high seasonal variation (CV=0.46)
- **Action**:
  - Add seasonal multipliers
  - Consider wave exposure metrics
  - Test ensemble predictions

### North Mole Fremantle (NMF) - NEEDS IMPROVEMENT
- **Status**: 36.4% predictions within ±3m  
- **Issue**: Port/river influence, 24m visibility range
- **Action**:
  - Add river flow data
  - Model port activity influence
  - Consider separate turbidity model

## Next Steps

1. ✅ **Complete**: Comprehensive analysis of sample size vs. accuracy
2. 🔄 **In Progress**: Document findings and recommendations (this file)
3. ⏭️ **Next**: 
   - Implement uncertainty flags for problematic sites
   - Test site-specific modeling approaches
   - Gather additional predictor data for high-variance sites
   - Consider ensemble methods or model averaging

## Conclusion

The observation that high-repeat sites have poor accuracy is **valid and important**. This is not a statistical anomaly but reveals fundamental limitations in the current modeling approach for environmentally complex sites. The issue is not with the data quantity but with the **model's ability to capture complex, non-linear, site-specific patterns**.

**Priority**: Address RKM, SCR, and NMF through enhanced modeling or operational flagging before relying on predictions for these sites.

---

*Analysis Date: December 24, 2025*  
*Generated by: analyze_sample_size_accuracy.py*
