# DIAGNOSTIC REPORT: Wind-Visibility Prediction Issues
**Date:** December 17, 2024  
**Issue:** Model predicts high visibility during high wind periods, which seems counterintuitive

---

## EXECUTIVE SUMMARY

The user correctly identified that the model is predicting relatively good visibility (2.4-3.3m) during high wind periods (9-11.5 m/s). After comprehensive investigation, we found **multiple critical issues** that explain this behavior:

### 🚨 CRITICAL BUG FOUND
**ALL ROLLING AVERAGES ARE IDENTICAL** - The 2-day, 3-day, and 4-day rolling averages are exactly the same (100% of cases), which is mathematically impossible if calculated correctly. This is corrupting the training data.

### Key Findings Summary
1. ✅ **Data Processing Bug** - Rolling averages not calculated correctly (grouping by report_id instead of site)
2. ✅ **Wind has near-zero correlation with visibility** in training data (-0.000 correlation)
3. ✅ **Site-specific patterns contradict each other** - Some sites show negative correlation, others positive
4. ✅ **Precipitation is a better predictor** than wind (poor vis: 1.96mm vs good vis: 1.07mm)
5. ⚠️  **High wind can coincide with good visibility** - Divers report 2-20m vis at 11-13 m/s wind

---

## INVESTIGATION 1: ACTUAL DIVE REPORTS DURING HIGH WIND

### Finding: High Wind Does NOT Always Mean Poor Visibility

Analyzed 192 dive reports with wind > 8 m/s:

**Sample High Wind Cases:**
| Site | Visibility | Wind | Notes |
|------|-----------|------|-------|
| RTS | 20m | 12.6 m/s | "Hiding from swell & N wind" |
| SCR | 20m | 11.1 m/s | "VVgood! 18C, got windy, near shore viz crap" |
| LEN | 17m | 10.8 m/s | "Amazing visability, 21°. Sea like a mirror" |
| RNN | 15m | 10.7 m/s | "Opera House" |
| SGR | 2m | 11.6 m/s | "Sue's Groyne. Not much sea life, murky" |

**Key Observations:**
- Visibility ranges from 2m to 20m even at wind speeds of 11-13 m/s
- Only 7-8% of divers mention "wind", "surge", or "rough" conditions in notes
- Divers often choose sheltered spots during high wind ("Hiding from swell")
- Site selection and location matter more than overall wind speed

**Conclusion:** Wind speed alone is NOT a reliable predictor of visibility. Site-specific factors dominate.

---

## INVESTIGATION 2: TEMPORAL LAG EFFECTS

### Finding: No Clear Wind→Visibility Lag Effect

**Wind Conditions During Poor Visibility (≤3m):**
- Average wind: 6.20 m/s
- High wind (>8 m/s): 18.3% of cases
- Low wind (<5 m/s): 30.1% of cases

**Wind Conditions During Good Visibility (≥10m):**
- Average wind: 6.22 m/s (essentially identical!)
- High wind (>8 m/s): 18.4% of cases

**Precipitation Shows Stronger Signal:**
- Poor visibility: 1.96mm average precipitation (48h)
- Good visibility: 1.07mm average precipitation (48h)
- **Poor vis has ~2x the precipitation**

**Conclusion:** Wind shows NO predictive power. Precipitation is a much better predictor.

---

## INVESTIGATION 3: SITE-SPECIFIC PATTERNS

### Finding: Sites Show OPPOSITE Wind-Visibility Relationships

**Overall Correlations:**
- Exposed sites: -0.003 (essentially zero)
- Sheltered sites: +0.001 (essentially zero)

**Individual Site Correlations:**

| Site | Correlation | Type | Avg Vis | Notes |
|------|-------------|------|---------|-------|
| **CMT** | **-0.420** | Sheltered | 5.8m | Strong NEGATIVE (expected) |
| **BUL** | **-0.234** | Sheltered | 5.4m | Negative (expected) |
| CMB | -0.186 | Sheltered | 3.4m | Negative |
| PPR | -0.061 | Exposed | 7.8m | Weak negative |
| **AMJ** | **+0.153** | Sheltered | 4.1m | **POSITIVE (wrong!)** |
| SCR | +0.130 | Sheltered | 7.1m | Positive (wrong) |
| RNN | +0.097 | Exposed | 14.8m | Positive (wrong) |
| RTS | +0.091 | Exposed | 15.2m | Positive (wrong) |

**Critical Problem: AMJ (Ammo Jetty)**
- Most dive reports (86 dives)
- Consistently poor visibility (avg 4.1m, median 4m)
- **POSITIVE wind correlation** (+0.153)
- 15 reports of 1m visibility, 11 reports of 2m visibility
- Visibility is consistently poor regardless of wind

**Why This Matters:**
The model is trying to average across contradictory patterns:
- Some sites: wind ↑ → visibility ↓ (correct)
- Other sites: wind ↑ → visibility ↑ (wrong, or selection bias)
- Many sites: wind has no effect

Result: Overall coefficient near zero.

**Conclusion:** The hierarchical model helps somewhat, but site-specific factors (currents, river runoff, substrate, protection) dominate over wind.

---

## INVESTIGATION 4: DATA QUALITY ISSUES

### Finding: Weather Data Matches Dive Dates

✅ No significant date mismatches between weather data and dive reports  
✅ No impossible weather values (no hurricane-force winds, etc.)  
✅ Visibility outliers are legitimate (11 cases >20m, 48 cases of 1m)

**Potential Issues:**
- StormGlass provides weather for a single lat/lon point
- Actual dive conditions depend on local geography, currents, protection
- Divers may choose sheltered spots during high wind (selection bias)

**Conclusion:** Weather data quality appears good, but point-source weather data may not represent actual dive site conditions.

---

## INVESTIGATION 5: DATA PROCESSING BUG

### 🚨 CRITICAL: Rolling Averages Not Calculated Correctly

**Evidence:**
```
Cases where 2-day and 3-day wind are IDENTICAL: 999 (100.0%)
Cases where 2-day and 4-day wind are IDENTICAL: 999 (100.0%)
```

**Root Cause (Line 296 in generate_weather_reports.py):**
```python
for report_id_val, group in df_daily_averages_sorted.groupby('report_id'):
    ...
    group_rolling_current_window = group[numeric_cols_for_rolling_selection].rolling(window=window_size, min_periods=1).mean()
```

**Problem:**
- Code groups by `report_id` (individual dive report)
- Each group typically has only ONE row
- Rolling average over 1 row = same value for all windows
- 2-day avg = 3-day avg = 4-day avg (all identical!)

**Impact on Model:**
- Model sees the same predictor 3 times with different names
- Coefficients get split across identical features
- Model cannot learn true relationships
- Wastes model capacity on redundant features

**Required Fix:**
Should group by `site` and sort by `date`, not by `report_id`:
```python
for site_val, group in df_daily_averages_sorted.groupby('site'):
    group = group.sort_values('weather_date_utc')
    ...
```

---

## MODEL BEHAVIOR ANALYSIS

### Why the Model Predicts High Visibility on High Wind Days

Given the current (corrupted) training data, let's look at Dec 24 prediction:

**December 24, 2024 (HIL):**
- Wind: 10.6 m/s (HIGH)
- Wave: 2.38m
- **Swell: 1.35m (LOW)** ← Key driver
- Predicted visibility: **3.33m (BEST of period)**

**Model Coefficients:**
- `month_cos`: -0.171 (strongest predictor, seasonal effect)
- `swellHeight_2day_roll_avg`: -0.106 (swell reduces visibility)
- `windSpeed_2day_roll_avg`: -0.013 (tiny effect!)

**What's Happening:**
1. **Low swell (1.35m)** → model predicts better visibility (coefficient -0.106)
2. **Seasonal effect (Dec)** → model thinks December is good (month_cos)
3. **High wind (10.6 m/s)** → tiny negative effect (coefficient -0.013) gets overwhelmed

**Why Wind Coefficient is So Small:**
- Training data shows zero correlation between wind and visibility
- Site-specific effects contradict each other
- Rolling averages are all identical (corrupting the data)

---

## CONCLUSIONS & RECOMMENDATIONS

### Root Causes Identified

1. **🚨 CRITICAL BUG:** Rolling averages are not calculated correctly, corrupting all training data
2. **Physical Reality:** Wind speed has weak direct effect on underwater visibility at Perth dive sites
3. **Site-Specific Factors:** Local geography, currents, river runoff dominate over wind
4. **Selection Bias:** Divers choose sheltered spots during high wind (hiding from conditions)
5. **Confounding Variables:** Precipitation, seasonal effects, and swell matter more than wind

### Why the Model May Still Be "Correct"

The model learned from real dive reports that:
- High wind doesn't always mean poor visibility
- Divers find good spots even in windy conditions
- Swell and precipitation are better predictors than wind speed

However, the corrupted rolling averages mean we cannot trust the current model.

### Recommended Actions (DO NOT IMPLEMENT YET)

**Priority 1: Fix Data Processing Bug**
1. Fix `generate_weather_reports.py` line 296 to group by `site` not `report_id`
2. Regenerate `daily_rolling_averages.csv` with correct rolling windows
3. Retrain model with corrected data

**Priority 2: Model Architecture Improvements**
1. Add site-type interactions (exposed vs sheltered × wind)
2. Add wind direction (not just speed) - offshore wind vs onshore wind
3. Add lagged wind effects (wind from 1-3 days before affects visibility later)
4. Add proximity to river mouths (Swan River affects coastal sites)
5. Consider tidal state (river outflow during ebb tides)

**Priority 3: Feature Engineering**
1. Create "effective wind" feature accounting for site protection
2. Add seasonal plankton bloom indicators
3. Add cumulative wave energy over 3-5 days (not just current day)
4. Add river discharge data if available

**Priority 4: Data Collection**
1. Validate StormGlass weather matches actual conditions at dive sites
2. Add dive location within site (some spots sheltered, others exposed)
3. Collect more data from exposed sites during high wind

### Expected Impact of Fixes

After fixing the rolling average bug and retraining:
- Wind coefficients may become more meaningful (currently split across identical features)
- Model may learn that 3-4 day wind history matters more than current wind
- Site-specific effects will be more accurately captured
- Predictions may change significantly

However, wind may STILL have small coefficients if the physical reality is that:
- Perth dive sites are partially sheltered
- Divers choose protected spots during high wind
- Other factors (swell, precipitation, season) dominate

---

## VALIDATION QUESTIONS FOR USER

Before proceeding with fixes, please confirm:

1. **Is the current prediction wrong?** Have you observed that high wind (10+ m/s) typically produces poor visibility at HIL?

2. **What's your experience?** At Hillarys during 10+ m/s winds, do you typically see:
   - Always poor visibility (<3m)?
   - Variable visibility (depends on exact location/conditions)?
   - Good visibility possible if choosing sheltered spots?

3. **Wind direction matters?** Does offshore wind (from land) affect visibility differently than onshore wind (from ocean)?

4. **Other factors?** Are there other conditions you check besides wind that affect visibility (e.g., recent rain, swell direction, tide state)?

Your practical diving experience will help determine whether the model needs to learn "wind always = poor visibility" or if the relationship is more nuanced as the current data suggests.

---

## TECHNICAL DETAILS

### Test Case: Manual Calculation

To verify the bug, here's what SHOULD happen with correct rolling averages:

**Example: AMJ site, 3 consecutive days**
- Day 1: Wind = 5 m/s
- Day 2: Wind = 7 m/s  
- Day 3: Wind = 9 m/s (dive day)

**Correct calculations:**
- 2-day avg = (7 + 9) / 2 = 8.0 m/s
- 3-day avg = (5 + 7 + 9) / 3 = 7.0 m/s
- 4-day avg = would need 4 days of data

**Current (buggy) result:**
- 2-day avg = 9 m/s (only sees dive day)
- 3-day avg = 9 m/s (only sees dive day)
- 4-day avg = 9 m/s (only sees dive day)

All three are identical because each dive report is processed in isolation.

### Files Affected

- `/workspace/generate_weather_reports.py` - Line 296 (bug location)
- `/workspace/stormglass_output/daily_rolling_averages.csv` - Contains corrupted data
- `/workspace/models/stormglass_pymc_hierarchical_extended_idata.nc` - Trained on corrupted data

---

## END OF REPORT
