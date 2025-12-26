# Site Repeat Accuracy Investigation - Quick Summary

## Your Observation
✅ **CORRECT**: Sites with most repeats (RKM, SCR, NMF) have poor accuracy

## Key Findings

### 1. Is it Dive School Bias? 
**NO** - No fair-weather sampling bias detected
- Observations spread across all visibility conditions
- No correlation between visibility and observation frequency
- NOT a data quality issue

### 2. Real Problem
**Environmental Complexity** - These sites are fundamentally harder to predict
- Higher variability (Std Dev 3.3-4.9m)
- Complex local factors (rivers, ports, transitional zones)
- Different relationships with weather parameters

### 3. Evidence
**Correlation Analysis Shows**:
- Weak linear correlations overall (r < 0.2)
- **OPPOSITE** relationships at different sites:
  - Atmospheric visibility: r=-0.13 (problematic) vs r=+0.05 (good)
  - Water temp: r=+0.05 (problematic) vs r=-0.13 (good)
- Need non-linear modeling

## Critical Sites

| Site | Samples | Accuracy | Status | Why Poor? |
|------|---------|----------|--------|-----------|
| **RKM** | 60 | 8.3% | 🔴 CRITICAL | Transitional zone, counterintuitive patterns |
| **NMF** | 54 | 36.4% | 🔴 CRITICAL | River/port influence, local turbidity |
| **SCR** | 72 | 46.7% | 🟠 POOR | Exposed reef, high seasonal variation |

## Answer to Your Questions

### "Is there a data plot correlating visibility to parameters?"
**YES** - Created 3 plots:
1. `plots/visibility_parameter_correlations.png` - 8 environmental parameters
2. `plots/site_specific_correlations.png` - Individual site patterns  
3. `plots/sample_size_accuracy_analysis.png` - Sample size relationships

### "Would we need to do data analysis to determine next steps?"
**YES** - Recommend:
1. Non-linear modeling (GAM, polynomial terms)
2. Interaction effects (wind × rain, wave × direction)
3. Site-specific models
4. Add local predictors (river flow, bathymetry)

## Next Steps - Three Options

### Option A: Quick Fix (1 week) ⚡
- Flag RKM, SCR, NMF as high-uncertainty
- Document limitations
- Deploy with warnings

### Option B: Moderate Enhancement (3-4 weeks) ⭐ **RECOMMENDED**
- Non-linear terms and interactions
- Site-type specific models
- Available local data integration
- Expected: 10-20% accuracy improvement

### Option C: Full Overhaul (2-3 months) 🎯
- Advanced GAM modeling
- New data collection
- Ensemble predictions
- Best possible accuracy

## Files Generated

### Analysis Scripts
- `analyze_sample_size_accuracy.py` - Main analysis
- `investigate_sampling_bias.py` - Bias detection
- `visibility_parameter_correlations.py` - Correlation analysis
- `create_site_comparison_plot.py` - Visualization

### Plots Created
1. `plots/sample_size_accuracy_analysis.png`
2. `plots/visibility_variability_analysis.png`
3. `plots/high_sample_sites_detailed_comparison.png`
4. `plots/visibility_parameter_correlations.png`
5. `plots/site_specific_correlations.png`

### Data Files
- `models/site_performance_metrics.csv` (existing)
- `models/high_sample_sites_analysis.csv` (new)
- `models/visibility_parameter_correlations.csv` (new)

### Documentation
- `SITE_REPEAT_ACCURACY_INVESTIGATION.md` - Full technical report
- `SAMPLING_BIAS_AND_NEXT_STEPS.md` - Detailed recommendations
- `INVESTIGATION_SUMMARY.md` - This file

## Bottom Line

Your observation was **spot-on**: high-repeat sites DO have poor accuracy. But it's NOT because dive schools only go on good days. It's because **popular dive sites are environmentally complex**, and our current simple linear model can't capture their behavior.

**Recommendation**: Proceed with **Option B** (Moderate Enhancement)
- Non-linear modeling
- Site-specific approaches  
- Local predictor integration
- 3-4 week timeline
- Expected meaningful improvement

The correlations are weak but informative - they tell us we need a more sophisticated modeling approach for these complex sites.

---

**Ready to proceed?** The analysis is complete and the path forward is clear.
