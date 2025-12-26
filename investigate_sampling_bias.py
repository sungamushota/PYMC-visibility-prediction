#!/usr/bin/env python3
"""
Investigate potential sampling bias at high-traffic dive school sites.
Key questions:
1. Do high-sample sites show different visibility distributions?
2. Are observations correlated with "good weather" parameters?
3. Is there evidence of fair-weather sampling bias?
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import pickle

# Load data
print("Loading data...")
vis_data = pd.read_csv('VIS_Reports_Augmented.csv')
vis_data['site_code'] = vis_data['site'].str.extract(r'\(([A-Z0-9]+)\)$')[0]
vis_data['Date'] = pd.to_datetime(vis_data['DateTime_Local_Naive']).dt.date

site_metrics = pd.read_csv('models/site_performance_metrics.csv')

# Load model predictors to see what environmental data was used
try:
    with open('models/stormglass_pymc_hierarchical_extended_predictors.pkl', 'rb') as f:
        predictor_info = pickle.load(f)
    print(f"Model predictors available: {list(predictor_info.keys())}")
except:
    print("Could not load predictor info")
    predictor_info = None

print("\n" + "="*80)
print("SAMPLING BIAS INVESTIGATION")
print("="*80)

# Focus on problematic high-sample sites vs. good high-sample sites
problematic_sites = ['RKM', 'SCR', 'NMF']  # Poor accuracy
good_high_sample = ['AMJ', 'KGT', 'BUL', 'CMT', 'PPR']  # Good accuracy, high samples
low_sample_sites = site_metrics[site_metrics['Total_Samples'] < 30]['Site_Code'].tolist()

print("\n1. VISIBILITY DISTRIBUTION COMPARISON")
print("-"*80)

# Compare visibility distributions
for site_group, site_list, label in [
    (problematic_sites, problematic_sites, "Problematic High-Sample"),
    (good_high_sample[:3], good_high_sample[:3], "Good High-Sample"),
]:
    vis_values = []
    for site in site_list:
        site_data = vis_data[vis_data['site_code'] == site]['visibility'].dropna()
        vis_values.extend(site_data.tolist())
    
    if vis_values:
        print(f"\n{label} Sites ({', '.join(site_list)}):")
        print(f"  Mean visibility: {np.mean(vis_values):.2f}m")
        print(f"  Median visibility: {np.median(vis_values):.2f}m")
        print(f"  Std dev: {np.std(vis_values):.2f}m")
        print(f"  Min/Max: {np.min(vis_values):.1f}m / {np.max(vis_values):.1f}m")
        print(f"  25th/75th percentile: {np.percentile(vis_values, 25):.1f}m / {np.percentile(vis_values, 75):.1f}m")
        
        # Check for positive skew (bias toward good visibility)
        skewness = stats.skew(vis_values)
        print(f"  Skewness: {skewness:.3f} {'(right-skewed - bias toward high vis)' if skewness > 0.5 else '(relatively symmetric)'}")

print("\n\n2. OBSERVATION FREQUENCY ANALYSIS")
print("-"*80)
print("\nChecking if sites are observed more frequently on certain days...")

# For each problematic site, check observation frequency
for site in problematic_sites:
    site_data = vis_data[vis_data['site_code'] == site].copy()
    site_data['Date'] = pd.to_datetime(site_data['DateTime_Local_Naive']).dt.date
    
    # Count observations per date
    obs_per_date = site_data.groupby('Date').size()
    
    print(f"\n{site}:")
    print(f"  Total observations: {len(site_data)}")
    print(f"  Unique dates: {len(obs_per_date)}")
    print(f"  Avg observations per active day: {obs_per_date.mean():.2f}")
    print(f"  Max observations on single day: {obs_per_date.max()}")
    
    if obs_per_date.max() > 5:
        print(f"  ⚠️  HIGH CLUSTERING: Some days have {obs_per_date.max()} observations!")
        print(f"      This suggests dive school group activities")
    
    # Check for repeat observations
    multi_obs_days = (obs_per_date > 1).sum()
    print(f"  Days with multiple observations: {multi_obs_days} ({100*multi_obs_days/len(obs_per_date):.1f}%)")

print("\n\n3. VISIBILITY vs. OBSERVATION COUNT")
print("-"*80)
print("\nDo sites get MORE observations when visibility is GOOD?")

# For each site, correlate visibility with observation frequency
for site in problematic_sites + good_high_sample[:2]:
    site_data = vis_data[vis_data['site_code'] == site].copy()
    site_data['Date'] = pd.to_datetime(site_data['DateTime_Local_Naive']).dt.date
    
    # Get daily stats
    daily_stats = site_data.groupby('Date').agg({
        'visibility': ['mean', 'count']
    }).reset_index()
    daily_stats.columns = ['Date', 'Avg_Vis', 'Obs_Count']
    
    if len(daily_stats) > 10:
        corr = stats.pearsonr(daily_stats['Avg_Vis'], daily_stats['Obs_Count'])
        print(f"\n{site}:")
        print(f"  Correlation between visibility and daily obs count: r={corr[0]:.3f}, p={corr[1]:.3f}")
        
        if corr[1] < 0.05 and corr[0] > 0.3:
            print(f"  ⚠️  SIGNIFICANT POSITIVE CORRELATION!")
            print(f"      More observations on high-visibility days = SAMPLING BIAS")
        elif corr[1] >= 0.05:
            print(f"  ✓ No significant correlation (good)")

print("\n\n4. SEASONAL COVERAGE")
print("-"*80)
print("\nAre observations spread across all seasons?")

for site in problematic_sites:
    site_data = vis_data[vis_data['site_code'] == site].copy()
    site_data['Month'] = pd.to_datetime(site_data['DateTime_Local_Naive']).dt.month
    site_data['Season'] = site_data['Month'].map({
        12: 'Summer', 1: 'Summer', 2: 'Summer',
        3: 'Autumn', 4: 'Autumn', 5: 'Autumn',
        6: 'Winter', 7: 'Winter', 8: 'Winter',
        9: 'Spring', 10: 'Spring', 11: 'Spring'
    })
    
    season_counts = site_data['Season'].value_counts()
    season_vis = site_data.groupby('Season')['visibility'].mean()
    
    print(f"\n{site}:")
    for season in ['Summer', 'Autumn', 'Winter', 'Spring']:
        count = season_counts.get(season, 0)
        vis = season_vis.get(season, np.nan)
        print(f"  {season:8s}: {count:3d} obs ({100*count/len(site_data):5.1f}%), avg vis: {vis:.1f}m")
    
    # Check for imbalance
    if season_counts.max() / season_counts.min() > 2:
        print(f"  ⚠️  SEASONAL IMBALANCE: {season_counts.idxmax()} has {season_counts.max()/season_counts.min():.1f}x more obs than {season_counts.idxmin()}")

print("\n\n5. VISIBILITY THRESHOLD ANALYSIS")
print("-"*80)
print("\nWhat % of observations are in 'good' vs 'poor' conditions?")

# Define thresholds
thresholds = {
    'Excellent': (10, 100),
    'Good': (7, 10),
    'Moderate': (5, 7),
    'Poor': (3, 5),
    'Very Poor': (0, 3)
}

comparison_data = []
for site_list, label in [(problematic_sites, 'Problematic'), (good_high_sample[:3], 'Good High-Sample')]:
    print(f"\n{label} Sites:")
    for site in site_list:
        site_vis = vis_data[vis_data['site_code'] == site]['visibility'].dropna()
        
        if len(site_vis) > 0:
            row_data = {'Site': site, 'Type': label, 'N': len(site_vis)}
            for category, (low, high) in thresholds.items():
                count = ((site_vis >= low) & (site_vis < high)).sum()
                pct = 100 * count / len(site_vis)
                row_data[category] = pct
            comparison_data.append(row_data)
            
            print(f"  {site}:")
            for category, (low, high) in thresholds.items():
                count = ((site_vis >= low) & (site_vis < high)).sum()
                pct = 100 * count / len(site_vis)
                print(f"    {category:12s} ({low:2.0f}-{high:2.0f}m): {pct:5.1f}%")

comparison_df = pd.DataFrame(comparison_data)

print("\n\n6. FAIRWEATHER BIAS INDEX")
print("-"*80)
print("\nCalculating 'fairweather bias' score (higher = more bias toward good conditions)")

for _, row in comparison_df.iterrows():
    # Calculate bias score: weight toward good conditions
    bias_score = (row['Excellent'] * 3 + row['Good'] * 2 + row['Moderate'] * 1) / 100
    expected_score = 1.5  # Baseline if evenly distributed
    
    print(f"{row['Site']} ({row['Type']}): Bias={bias_score:.2f} {'⚠️  HIGH' if bias_score > 2.0 else '✓ Normal'}")

print("\n\n7. RECOMMENDATION: DO WE NEED FURTHER DATA ANALYSIS?")
print("="*80)

print("""
Based on this investigation, here's what we should do:

A. IF SAMPLING BIAS IS DETECTED:
   1. ⚠️  Quantify the bias magnitude
   2. Create weighted predictions (down-weight biased observations)
   3. Collect more observations during poor conditions
   4. Consider removing heavily biased dates/observations
   
B. IF NO STRONG BIAS DETECTED:
   1. ✓ The poor accuracy is due to environmental complexity, not bias
   2. Focus on improving model with:
      - Better environmental predictors
      - Non-linear terms
      - Site-specific coefficients
      
C. NEXT STEPS FOR DATA ANALYSIS:
   1. Correlation analysis: visibility vs. environmental parameters
   2. Compare predictor-response relationships across site types
   3. Identify which predictors work well vs. poorly at each site
   4. Test if relationships differ for problematic sites

Let me now create the correlation plots you requested...
""")
