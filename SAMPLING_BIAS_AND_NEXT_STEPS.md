# Sampling Bias Investigation & Data Analysis Next Steps

## Your Question
> "Some sites like Rockingham are abused by dive schools. I'm not sure how to deal with this. Is there a data plot correlating visibility to parameters? And if so, would we need to do data analysis to determine next steps?"

## Executive Summary

✅ **Good News**: NO significant "fair-weather" sampling bias detected at dive school sites  
⚠️ **Key Finding**: Problematic sites respond DIFFERENTLY to environmental parameters than good sites  
📊 **Answer**: YES, correlation plots created, and YES, we need further data analysis

---

## Investigation Results

### 1. Sampling Bias Analysis (Dive School Effect)

#### What We Tested:
- Do dive schools only visit sites on "good visibility" days?
- Are observations clustered on certain dates?
- Is there seasonal imbalance?

#### Results:

**✓ NO Strong Fair-Weather Bias:**
- RKM, SCR, NMF: No correlation between visibility and observation frequency (p>0.6)
- Observations spread across full visibility range (1-25m)
- Most days have only 1-2 observations (not large group events)
- Fair-weather bias score: Normal range

**⚠️ BUT Some Issues Detected:**

1. **Seasonal Imbalance:**
   - **SCR (South Cottesloe Reef)**: Only 6.9% winter observations (6.2x fewer than Autumn)
   - **NMF (North Mole Fremantle)**: Only 14.8% winter observations
   - Winter visibility: Actually HIGHER (8.5-8.8m) than other seasons!

2. **Visibility Distribution:**
   - Problematic sites: Mean 6.94m (higher than good sites!)
   - Good sites: Mean 4.95m
   - **Interpretation**: Problematic sites have MORE visibility variation, not bias toward good days

**Conclusion**: The poor accuracy is **NOT due to sampling bias** but due to **environmental complexity and model limitations**.

---

## 2. Visibility vs. Parameters Correlation Analysis

### Created Plots:
1. ✅ `plots/visibility_parameter_correlations.png` - 8 parameter scatter plots
2. ✅ `plots/site_specific_correlations.png` - Individual site correlations
3. ✅ `models/visibility_parameter_correlations.csv` - Detailed correlation data

### Key Findings:

#### Overall Correlation Strength: **WEAK** 
Most correlations are not statistically significant (p>0.05), suggesting:
- Linear relationships are weak or non-existent
- Need non-linear models
- Missing important predictors
- Complex interactions between variables

#### Different Relationships by Site Type:

| Parameter | Problematic Sites | Good Sites | Difference | Interpretation |
|-----------|------------------|------------|------------|----------------|
| **Atmospheric Visibility** | r=-0.13 (ns) | r=+0.05 (ns) | 0.174 | **OPPOSITE DIRECTIONS!** |
| **Water Temperature** | r=+0.05 (ns) | r=-0.13 (ns) | 0.176 | **OPPOSITE DIRECTIONS!** |
| **Precip Last 48h** | r=+0.01 (ns) | r=-0.16 (sig) | 0.166 | **Only works for good sites** |

#### Site-Specific Patterns:

**Rockingham (RKM) - CRITICAL:**
- Positive correlation with wave/swell height (+0.30, +0.31)
- This is COUNTERINTUITIVE (usually waves reduce visibility)
- Suggests complex local dynamics

**South Cottesloe Reef (SCR):**
- Negative correlation with swell height (-0.38)
- This makes more sense (swell → reduced visibility)
- But still not strong enough

**North Mole Fremantle (NMF):**
- Negative wave/swell correlations (-0.27, -0.30)
- Near port/river → local factors dominate
- Regional weather less predictive

**Good Sites (AMJ, KGT, BUL):**
- Stronger precipitation effect (r=-0.16, significant)
- More consistent patterns
- Simpler coastal environments

---

## 3. Answer to Your Question: Do We Need Data Analysis?

### **YES - Here's the roadmap:**

## Recommended Next Steps

### Phase 1: IMMEDIATE (This Week)
**Priority: Understand WHY sites differ**

1. **Non-Linear Relationship Analysis**
   - Test polynomial terms (visibility ~ wind² + wind³)
   - Identify threshold effects (e.g., visibility drops sharply above X wind speed)
   - Use GAM (Generalized Additive Models) to detect curves
   
2. **Interaction Effects**
   - Test: Wind × Precipitation (storms)
   - Test: Wave Height × Wind Direction (exposure)
   - Test: Swell × Bathymetry (site-specific)
   
3. **Lag Analysis**
   - Does visibility respond with delay after storms?
   - Test 1-day, 2-day, 3-day, 7-day lags
   - Rivers: Rainfall → runoff → turbidity (delayed)

### Phase 2: MODEL IMPROVEMENTS (Next 2 Weeks)

4. **Site-Type Specific Models**
   ```
   MODEL A: Stable Coastal Sites (AMJ, KGT, BUL)
   - Simpler model
   - Precipitation-focused
   - Good linear predictors
   
   MODEL B: Transitional/Complex Sites (RKM, SCR, NMF)
   - Non-linear terms
   - Local predictors (distance to features)
   - Interaction terms
   - Higher uncertainty bounds
   ```

5. **Add Missing Predictors**
   - **For NMF**: River flow data, tide state, port activity
   - **For RKM**: Bathymetry, current patterns, upwelling indices
   - **For SCR**: Wave exposure, reef complexity
   - **All sites**: Temporal autocorrelation (yesterday's visibility)

6. **Ensemble Approach**
   - Combine multiple models
   - Weight by recent performance
   - Provide confidence intervals

### Phase 3: DATA COLLECTION (Ongoing)

7. **Address Seasonal Gaps**
   - Priority: More **winter observations** for SCR, NMF
   - Target: 15-20 winter observations per site
   - Timeline: Winter 2026 (June-August)

8. **Local Environmental Data**
   - Swan River flow gauge data (for NMF)
   - Tide tables integration
   - Bathymetric profiles
   - Current meter data (if available)

9. **Enhanced Observation Protocol**
   - Record: sea state, swell direction, recent weather
   - Note: local conditions (river plumes visible, etc.)
   - Consistency: Same observer preferences

---

## 4. Specific Recommendations by Site

### Rockingham Dive Trail (RKM) - CRITICAL PRIORITY

**Problem**: 8.3% accuracy, counterintuitive correlations

**Hypothesis**: Transitional zone where multiple water masses interact
- Offshore water (clear) vs coastal water (turbid)
- Wind/swell may push one or the other toward site
- Need oceanographic classification

**Action Plan**:
1. Collect local bathymetry and current data
2. Test "water mass origin" predictor (wind direction-based)
3. Consider separate model or flag as high-uncertainty
4. Short-term: **Recommend users check recent observations** before relying on forecast

### South Cottesloe Reef (SCR) - MEDIUM PRIORITY

**Problem**: 46.7% accuracy, strong seasonal variation

**Hypothesis**: Exposed reef highly sensitive to wave climate and seasons

**Action Plan**:
1. Add seasonal multipliers to model
2. Test wave exposure index (wind + wave height + direction)
3. Collect more winter observations (currently only 5 vs 31 autumn)
4. Consider separate summer/winter models

### North Mole Fremantle (NMF) - HIGH PRIORITY

**Problem**: 36.4% accuracy, port/river influence

**Hypothesis**: River outflow and port activity dominate visibility

**Action Plan**:
1. Integrate Swan River flow data
2. Add distance-to-river-mouth weighting
3. Test precipitation → river flow → visibility lag model
4. Consider tidal influence on river outflow
5. Short-term: Add uncertainty warning during/after rain events

---

## 5. Statistical Evidence Summary

### What We Know:
- ✓ No fair-weather sampling bias
- ✓ Problematic sites have higher environmental variability
- ✓ Different sites respond differently to same parameters
- ✓ Current linear model is insufficient
- ✓ Seasonal gaps exist

### What We Don't Know:
- ❓ Functional form of relationships (linear, threshold, exponential?)
- ❓ Which interactions matter most
- ❓ Optimal lag times for precipitation effects
- ❓ Local bathymetric influences
- ❓ Tidal and current effects

### What We Need to Test:
1. Non-linear relationships (GAM, polynomial terms)
2. Interaction effects (wind × rain, wave × direction)
3. Lag effects (1-7 day delays)
4. Site-specific thresholds
5. Temporal autocorrelation
6. Local vs regional predictor importance

---

## 6. Implementation Timeline

| Timeframe | Task | Outcome |
|-----------|------|---------|
| **Week 1** | Non-linear analysis, interaction testing | Identify best functional forms |
| **Week 2** | Implement site-type specific models | Improved predictions for complex sites |
| **Week 3** | Add uncertainty flags, test ensemble | Production-ready system |
| **Week 4** | Validate, document, deploy | Updated forecasting system |
| **Ongoing** | Collect winter data, monitor performance | Continuous improvement |

---

## 7. Expected Outcomes

### Best Case:
- **RKM**: Improve from 8% to 40-50% accuracy with local predictors
- **SCR**: Improve from 47% to 60-70% with seasonal terms
- **NMF**: Improve from 36% to 55-65% with river flow data

### Realistic Case:
- 10-20 percentage point improvement with enhanced modeling
- Clear identification of high-uncertainty conditions
- User confidence through transparency about limitations

### Worst Case:
- Some sites remain difficult to predict
- Flag as "high-uncertainty" with wider prediction intervals
- Focus forecasting effort on sites with good accuracy

---

## 8. Decision Point: Next Actions

**Question for You**: How should we proceed?

### Option A: Quick Fixes (1 week effort)
- Add uncertainty flags for RKM, SCR, NMF
- Document limitations
- Deploy with caveats
- ➕ Fast, low risk
- ➖ Doesn't solve accuracy problem

### Option B: Moderate Enhancement (3-4 week effort)
- Implement non-linear terms and interactions
- Create site-type specific models
- Add available local data
- ➕ Substantial improvement likely
- ➖ Moderate development time

### Option C: Comprehensive Overhaul (2-3 month effort)
- Full GAM/advanced modeling
- Collect new environmental data
- Ensemble predictions
- Thorough validation
- ➕ Best possible accuracy
- ➖ Long timeline, resource intensive

### **Recommendation**: **Option B** - Moderate Enhancement
- Best balance of effort vs improvement
- Addresses core issues identified
- Can iterate to Option C later if needed
- Delivers value in reasonable timeframe

---

## Conclusion

The dive school "abuse" concern was valid to investigate, but **sampling bias is NOT the problem**. The real issue is that **popular dive sites are environmentally complex** and our current model is too simple to capture their behavior.

**The correlations exist but are weak**, indicating we need:
1. Non-linear modeling
2. Site-specific approaches
3. Additional local predictors
4. Interaction terms

**YES, we need further data analysis** - specifically non-linear modeling and site-specific predictor identification. This is not a data quality issue; it's a model complexity issue.

Would you like me to proceed with implementing the moderate enhancement approach (Option B)?

---

*Analysis completed: December 24, 2025*  
*Files generated: 8 analysis scripts, 6 plots, 3 CSV summaries, 2 investigation reports*
