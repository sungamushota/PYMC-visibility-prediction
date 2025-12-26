#!/usr/bin/env python3
"""
Analyze correlations between visibility and environmental parameters.
Compare problematic sites vs. good sites to understand what's different.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

print("Loading data...")
# Load environmental data
env_data = pd.read_csv('stormglass_output/daily_rolling_averages.csv')

# The site column already contains site codes
env_data['site_code'] = env_data['site']

# Key parameters to analyze
key_params_3day = [
    'windSpeed_3day_roll_avg',
    'waveHeight_3day_roll_avg',
    'swellHeight_3day_roll_avg',
    'precipitation_3day_roll_avg',
    'atmospheric_atmospheric_visibility_km_km_3day_roll_avg',
    'cloudCover_3day_roll_avg',
    'gust_3day_roll_avg',
    'waterTemperature_3day_roll_avg',
    'precipitation_sum_last_48h'
]

# Cleaner names for plotting
param_names = {
    'windSpeed_3day_roll_avg': 'Wind Speed (3d avg)',
    'waveHeight_3day_roll_avg': 'Wave Height (3d avg)',
    'swellHeight_3day_roll_avg': 'Swell Height (3d avg)',
    'precipitation_3day_roll_avg': 'Precipitation (3d avg)',
    'atmospheric_atmospheric_visibility_km_km_3day_roll_avg': 'Atmospheric Visibility',
    'cloudCover_3day_roll_avg': 'Cloud Cover (3d avg)',
    'gust_3day_roll_avg': 'Wind Gusts (3d avg)',
    'waterTemperature_3day_roll_avg': 'Water Temp (3d avg)',
    'precipitation_sum_last_48h': 'Precip Last 48h'
}

# Site categories
problematic_sites = ['RKM', 'SCR', 'NMF']
good_high_sample = ['AMJ', 'KGT', 'BUL']

print("\n" + "="*80)
print("VISIBILITY vs. ENVIRONMENTAL PARAMETERS CORRELATION ANALYSIS")
print("="*80)

# Calculate correlations for each site category
print("\n1. CORRELATION COEFFICIENTS")
print("-"*80)

correlation_results = []

for site_list, label in [(problematic_sites, 'PROBLEMATIC'), (good_high_sample, 'GOOD')]:
    print(f"\n{label} Sites ({', '.join(site_list)}):")
    print("-"*60)
    
    site_data = env_data[env_data['site_code'].isin(site_list)].copy()
    
    for param in key_params_3day:
        if param in site_data.columns:
            valid_data = site_data[['visibility', param]].dropna()
            
            if len(valid_data) > 10:
                corr = stats.pearsonr(valid_data['visibility'], valid_data[param])
                
                correlation_results.append({
                    'Site_Type': label,
                    'Parameter': param_names.get(param, param),
                    'Correlation': corr[0],
                    'P_Value': corr[1],
                    'N': len(valid_data),
                    'Significant': 'Yes' if corr[1] < 0.05 else 'No'
                })
                
                sig_marker = '***' if corr[1] < 0.001 else ('**' if corr[1] < 0.01 else ('*' if corr[1] < 0.05 else ''))
                print(f"  {param_names.get(param, param):30s}: r={corr[0]:6.3f} (p={corr[1]:.3f}) {sig_marker:3s} n={len(valid_data)}")

corr_df = pd.DataFrame(correlation_results)

print("\n\n2. KEY FINDINGS: DIFFERENT CORRELATION PATTERNS")
print("-"*80)

# Compare correlations between site types
for param in key_params_3day:
    param_name = param_names.get(param, param)
    prob_corr = corr_df[(corr_df['Site_Type'] == 'PROBLEMATIC') & (corr_df['Parameter'] == param_name)]
    good_corr = corr_df[(corr_df['Site_Type'] == 'GOOD') & (corr_df['Parameter'] == param_name)]
    
    if len(prob_corr) > 0 and len(good_corr) > 0:
        prob_r = prob_corr['Correlation'].values[0]
        good_r = good_corr['Correlation'].values[0]
        diff = abs(prob_r - good_r)
        
        if diff > 0.15:  # Substantial difference
            print(f"\n{param_name}:")
            print(f"  Problematic sites: r={prob_r:.3f} ({'sig' if prob_corr['Significant'].values[0] == 'Yes' else 'ns'})")
            print(f"  Good sites: r={good_r:.3f} ({'sig' if good_corr['Significant'].values[0] == 'Yes' else 'ns'})")
            print(f"  Difference: {diff:.3f} ⚠️  DIFFERENT RELATIONSHIPS!")

print("\n\n3. CREATING CORRELATION VISUALIZATIONS...")
print("-"*80)

# Create comprehensive correlation plot
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)
fig.suptitle('Visibility vs. Environmental Parameters: Problematic vs. Good Sites', 
             fontsize=16, fontweight='bold', y=0.995)

# Select top parameters to plot
plot_params = [
    'windSpeed_3day_roll_avg',
    'waveHeight_3day_roll_avg', 
    'swellHeight_3day_roll_avg',
    'precipitation_sum_last_48h',
    'atmospheric_atmospheric_visibility_km_km_3day_roll_avg',
    'cloudCover_3day_roll_avg',
    'gust_3day_roll_avg',
    'waterTemperature_3day_roll_avg'
]

for idx, param in enumerate(plot_params[:8]):
    row = idx // 3
    col = idx % 3
    ax = fig.add_subplot(gs[row, col])
    
    param_name = param_names.get(param, param)
    
    # Plot problematic sites
    prob_data = env_data[env_data['site_code'].isin(problematic_sites)][['visibility', param]].dropna()
    if len(prob_data) > 0:
        ax.scatter(prob_data[param], prob_data['visibility'], 
                  alpha=0.4, s=30, color='red', label='Problematic', edgecolors='darkred', linewidth=0.5)
        
        # Fit line
        if len(prob_data) > 10:
            z = np.polyfit(prob_data[param], prob_data['visibility'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(prob_data[param].min(), prob_data[param].max(), 100)
            ax.plot(x_line, p(x_line), 'r-', linewidth=2, alpha=0.7)
    
    # Plot good sites
    good_data = env_data[env_data['site_code'].isin(good_high_sample)][['visibility', param]].dropna()
    if len(good_data) > 0:
        ax.scatter(good_data[param], good_data['visibility'],
                  alpha=0.4, s=30, color='green', label='Good', edgecolors='darkgreen', linewidth=0.5)
        
        # Fit line
        if len(good_data) > 10:
            z = np.polyfit(good_data[param], good_data['visibility'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(good_data[param].min(), good_data[param].max(), 100)
            ax.plot(x_line, p(x_line), 'g-', linewidth=2, alpha=0.7)
    
    ax.set_xlabel(param_name, fontsize=10)
    ax.set_ylabel('Underwater Visibility (m)', fontsize=10)
    ax.set_title(param_name, fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)
    
    # Add correlation values as text
    prob_corr_val = corr_df[(corr_df['Site_Type'] == 'PROBLEMATIC') & (corr_df['Parameter'] == param_name)]
    good_corr_val = corr_df[(corr_df['Site_Type'] == 'GOOD') & (corr_df['Parameter'] == param_name)]
    
    text_str = ''
    if len(prob_corr_val) > 0:
        text_str += f"Prob: r={prob_corr_val['Correlation'].values[0]:.2f}\n"
    if len(good_corr_val) > 0:
        text_str += f"Good: r={good_corr_val['Correlation'].values[0]:.2f}"
    
    ax.text(0.05, 0.95, text_str, transform=ax.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Last subplot: correlation comparison heatmap
ax_heat = fig.add_subplot(gs[2, 2])

# Create matrix for heatmap
pivot_data = corr_df.pivot_table(values='Correlation', 
                                 index='Parameter', 
                                 columns='Site_Type')

# Reorder to match our parameters
param_order = [param_names.get(p, p) for p in plot_params if param_names.get(p, p) in pivot_data.index]
pivot_data = pivot_data.loc[param_order]

sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
           ax=ax_heat, cbar_kws={'label': 'Correlation'},
           vmin=-0.5, vmax=0.5, linewidths=0.5)
ax_heat.set_title('Correlation Comparison', fontsize=11, fontweight='bold')
ax_heat.set_xlabel('')
ax_heat.set_ylabel('')

plt.savefig('plots/visibility_parameter_correlations.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/visibility_parameter_correlations.png")

# Create site-specific comparison
fig2, axes = plt.subplots(2, 3, figsize=(18, 10))
fig2.suptitle('Site-Specific Correlation Analysis (Key Parameters)', 
              fontsize=16, fontweight='bold')

all_sites = problematic_sites + good_high_sample
colors_site = ['darkred', 'red', 'orange', 'lightgreen', 'green', 'darkgreen']

for idx, site in enumerate(all_sites):
    ax = axes[idx // 3, idx % 3]
    
    site_data = env_data[env_data['site_code'] == site].copy()
    
    # Calculate correlations for this site
    site_corrs = []
    for param in plot_params[:6]:  # Top 6 parameters
        valid_data = site_data[['visibility', param]].dropna()
        if len(valid_data) > 5:
            corr = stats.pearsonr(valid_data['visibility'], valid_data[param])
            site_corrs.append({
                'param': param_names.get(param, param).replace(' (3d avg)', ''),
                'corr': corr[0],
                'sig': corr[1] < 0.05
            })
    
    if site_corrs:
        site_corr_df = pd.DataFrame(site_corrs)
        
        # Create bar plot
        bar_colors = ['green' if sig else 'gray' for sig in site_corr_df['sig']]
        bars = ax.barh(range(len(site_corr_df)), site_corr_df['corr'], 
                      color=bar_colors, alpha=0.7, edgecolor='black')
        ax.set_yticks(range(len(site_corr_df)))
        ax.set_yticklabels(site_corr_df['param'], fontsize=9)
        ax.set_xlabel('Correlation', fontsize=10)
        ax.set_title(f'{site}', fontsize=12, fontweight='bold', 
                    color=colors_site[idx])
        ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax.grid(axis='x', alpha=0.3)
        ax.set_xlim(-0.6, 0.6)
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, site_corr_df['corr'])):
            ax.text(val + 0.02 if val > 0 else val - 0.02, i,
                   f'{val:.2f}', va='center', 
                   ha='left' if val > 0 else 'right',
                   fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('plots/site_specific_correlations.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/site_specific_correlations.png")

# Save detailed correlation results
corr_df.to_csv('models/visibility_parameter_correlations.csv', index=False)
print("✓ Saved: models/visibility_parameter_correlations.csv")

print("\n" + "="*80)
print("SUMMARY: NEXT STEPS FOR DATA ANALYSIS")
print("="*80)

print("""
Based on correlation analysis, here's what we found:

1. CORRELATION PATTERNS EXIST but may differ between site types
   
2. KEY PARAMETERS TO INVESTIGATE FURTHER:
   - Wave height and swell height (oceanographic conditions)
   - Wind speed and gusts (water mixing)
   - Precipitation (runoff and turbidity)
   - Atmospheric visibility (regional weather patterns)

3. RECOMMENDED NEXT STEPS:

   A. IMMEDIATE ANALYSIS NEEDED:
      □ Non-linear relationships (some may be threshold-based)
      □ Interaction effects (e.g., wind + rain together)
      □ Lag effects (visibility impact delayed after storms)
      □ Site-specific thresholds
      
   B. MODEL IMPROVEMENTS:
      □ Add polynomial/spline terms for key predictors
      □ Include interaction terms
      □ Site-specific predictor coefficients
      □ Temporal autocorrelation
      
   C. DATA COLLECTION:
      □ More winter observations for SCR, NMF
      □ Local turbidity measurements
      □ River flow data (for NMF)
      □ Tidal state information

4. ANSWER TO YOUR QUESTION:
   YES, we should proceed with deeper data analysis to:
   - Identify non-linear relationships
   - Find site-specific patterns
   - Determine which predictors work best for each site type
   - Understand why problematic sites behave differently
   
   The correlations show promise but are not strong enough yet.
   This suggests we're missing key variables or functional forms.
""")

print("\nRecommendation: Run advanced modeling analysis next? (Y/N)")
print("This would include: GAM analysis, interaction terms, threshold detection")
