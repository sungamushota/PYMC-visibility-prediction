#!/usr/bin/env python3
"""
Analyze the relationship between sample size (number of repeats) and model accuracy.
Investigates why some high-repeat sites have poor accuracy.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Load site performance metrics
df = pd.read_csv('models/site_performance_metrics.csv')

# Sort by total samples descending
df_sorted = df.sort_values('Total_Samples', ascending=False)

print("=" * 80)
print("SAMPLE SIZE vs. ACCURACY ANALYSIS")
print("=" * 80)
print("\n1. TOP 10 SITES BY SAMPLE SIZE:")
print("-" * 80)
top_10 = df_sorted.head(10)[['Site_Code', 'Site_Name', 'Total_Samples', 'MAE_m', 'RMSE_m', 'R2_Score', 'Within_3m_%']]
print(top_10.to_string(index=False))

print("\n\n2. CONCERNING HIGH-SAMPLE SITES (>50 samples with poor accuracy):")
print("-" * 80)
high_sample_poor_accuracy = df[(df['Total_Samples'] >= 50) & 
                                ((df['MAE_m'] > 3.0) | (df['Within_3m_%'] < 60))]
high_sample_poor_accuracy = high_sample_poor_accuracy.sort_values('Total_Samples', ascending=False)
print(high_sample_poor_accuracy[['Site_Code', 'Site_Name', 'Total_Samples', 'MAE_m', 'RMSE_m', 'Within_3m_%']].to_string(index=False))

print("\n\n3. STATISTICAL CORRELATION ANALYSIS:")
print("-" * 80)
# Correlation between sample size and various metrics
correlation_mae = stats.pearsonr(df['Total_Samples'], df['MAE_m'])
correlation_rmse = stats.pearsonr(df['Total_Samples'], df['RMSE_m'])
correlation_within3m = stats.pearsonr(df['Total_Samples'], df['Within_3m_%'])

print(f"Correlation between Total Samples and MAE: r={correlation_mae[0]:.3f}, p-value={correlation_mae[1]:.4f}")
print(f"Correlation between Total Samples and RMSE: r={correlation_rmse[0]:.3f}, p-value={correlation_rmse[1]:.4f}")
print(f"Correlation between Total Samples and Within ±3m%: r={correlation_within3m[0]:.3f}, p-value={correlation_within3m[1]:.4f}")

# Interpret the results
if correlation_mae[1] < 0.05:
    if correlation_mae[0] > 0:
        print("\n⚠️  SIGNIFICANT POSITIVE CORRELATION: Sites with more samples tend to have HIGHER error (worse accuracy)!")
    else:
        print("\n✓ SIGNIFICANT NEGATIVE CORRELATION: Sites with more samples tend to have lower error (better accuracy).")
else:
    print("\nNo statistically significant correlation between sample size and error.")

print("\n\n4. SITE CATEGORIES BY SAMPLE SIZE AND PERFORMANCE:")
print("-" * 80)

# Categorize sites
low_sample = df[df['Total_Samples'] < 30]
med_sample = df[(df['Total_Samples'] >= 30) & (df['Total_Samples'] < 60)]
high_sample = df[df['Total_Samples'] >= 60]

print(f"\nLow Sample (<30, n={len(low_sample)}): Avg MAE={low_sample['MAE_m'].mean():.2f}m, Avg Within ±3m={low_sample['Within_3m_%'].mean():.1f}%")
print(f"Medium Sample (30-59, n={len(med_sample)}): Avg MAE={med_sample['MAE_m'].mean():.2f}m, Avg Within ±3m={med_sample['Within_3m_%'].mean():.1f}%")
print(f"High Sample (≥60, n={len(high_sample)}): Avg MAE={high_sample['MAE_m'].mean():.2f}m, Avg Within ±3m={high_sample['Within_3m_%'].mean():.1f}%")

print("\n\n5. POTENTIAL EXPLANATIONS:")
print("-" * 80)
print("""
Possible reasons why high-repeat sites have poor accuracy:

a) ENVIRONMENTAL COMPLEXITY:
   - Sites with more observations may be in more variable/complex environments
   - High traffic dive/snorkel sites often have turbulent conditions
   - Coastal vs offshore differences in water dynamics

b) SEASONAL VARIABILITY:
   - More samples = more seasonal coverage
   - Model may struggle to capture full seasonal patterns
   - Some sites have greater seasonal variation in visibility

c) DATA QUALITY ISSUES:
   - Popular sites might have observations from more diverse conditions
   - Different observers may have varying reporting standards
   - Edge cases and extreme conditions more likely captured

d) MODEL LIMITATIONS:
   - Current hierarchical model may not fully capture site-specific patterns
   - High-variance sites need more complex modeling
   - Potential missing predictors for specific site characteristics

e) SPATIAL FACTORS:
   - Some high-sample sites may be in transitional zones
   - Near river mouths, industrial areas, or complex bathymetry
   - Local factors not captured by regional weather data
""")

# Now let's load the original data to investigate these sites more deeply
print("\n\n6. DETAILED INVESTIGATION OF WORST HIGH-SAMPLE SITES:")
print("-" * 80)

# Load the original data
vis_data = pd.read_csv('VIS_Reports_Augmented.csv')

# Extract site code from the full site name (e.g., "Ammo Jetty (AMJ)" -> "AMJ")
vis_data['site_code'] = vis_data['site'].str.extract(r'\(([A-Z0-9]+)\)$')[0]

# Focus on the worst performing high-sample sites
worst_sites = ['RKM', 'SCR', 'NMF', 'KGT']

for site in worst_sites:
    site_data = vis_data[vis_data['site_code'] == site]
    site_metrics = df[df['Site_Code'] == site].iloc[0]
    
    print(f"\n{site} - {site_metrics['Site_Name']}:")
    print(f"  Total Samples: {site_metrics['Total_Samples']}")
    print(f"  MAE: {site_metrics['MAE_m']:.2f}m, Within ±3m: {site_metrics['Within_3m_%']:.1f}%")
    print(f"  Visibility Range: {site_data['visibility'].min():.1f}m to {site_data['visibility'].max():.1f}m")
    print(f"  Visibility Std Dev: {site_data['visibility'].std():.2f}m")
    print(f"  Avg Visibility: {site_data['visibility'].mean():.2f}m")
    
    # Check if there's a seasonal pattern
    site_data['Month'] = pd.to_datetime(site_data['DateTime_Local_Naive']).dt.month
    monthly_variation = site_data.groupby('Month')['visibility'].agg(['mean', 'std', 'count'])
    if len(monthly_variation) > 3:
        print(f"  Monthly Variation: CV={monthly_variation['mean'].std() / monthly_variation['mean'].mean():.2f} (higher = more seasonal)")

# Create visualization
print("\n\nGenerating visualizations...")

# Create a comprehensive plot
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Sample Size vs. Accuracy Analysis', fontsize=16, fontweight='bold')

# Plot 1: Sample Size vs MAE
ax1 = axes[0, 0]
scatter1 = ax1.scatter(df['Total_Samples'], df['MAE_m'], 
                      c=df['Within_3m_%'], cmap='RdYlGn', 
                      s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax1.set_xlabel('Total Samples', fontsize=12)
ax1.set_ylabel('MAE (m)', fontsize=12)
ax1.set_title('Sample Size vs. Mean Absolute Error', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3)
# Add colorbar
cbar1 = plt.colorbar(scatter1, ax=ax1)
cbar1.set_label('Within ±3m (%)', fontsize=10)
# Annotate worst performers with high samples
for _, row in high_sample_poor_accuracy.iterrows():
    ax1.annotate(row['Site_Code'], 
                xy=(row['Total_Samples'], row['MAE_m']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=8, color='red', fontweight='bold')

# Plot 2: Sample Size vs Within 3m %
ax2 = axes[0, 1]
scatter2 = ax2.scatter(df['Total_Samples'], df['Within_3m_%'], 
                      c=df['MAE_m'], cmap='RdYlGn_r',
                      s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax2.set_xlabel('Total Samples', fontsize=12)
ax2.set_ylabel('Within ±3m (%)', fontsize=12)
ax2.set_title('Sample Size vs. Prediction Accuracy', fontsize=13, fontweight='bold')
ax2.axhline(y=60, color='orange', linestyle='--', label='60% threshold', alpha=0.5)
ax2.grid(True, alpha=0.3)
ax2.legend()
cbar2 = plt.colorbar(scatter2, ax=ax2)
cbar2.set_label('MAE (m)', fontsize=10)
# Annotate worst performers
for _, row in high_sample_poor_accuracy.iterrows():
    ax2.annotate(row['Site_Code'], 
                xy=(row['Total_Samples'], row['Within_3m_%']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=8, color='red', fontweight='bold')

# Plot 3: Average Visibility vs MAE
ax3 = axes[1, 0]
scatter3 = ax3.scatter(df['Avg_Visibility_m'], df['MAE_m'],
                      c=df['Total_Samples'], cmap='viridis',
                      s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax3.set_xlabel('Average Visibility (m)', fontsize=12)
ax3.set_ylabel('MAE (m)', fontsize=12)
ax3.set_title('Average Visibility vs. Model Error', fontsize=13, fontweight='bold')
ax3.grid(True, alpha=0.3)
cbar3 = plt.colorbar(scatter3, ax=ax3)
cbar3.set_label('Total Samples', fontsize=10)
# Add annotations for problematic sites
for _, row in high_sample_poor_accuracy.iterrows():
    ax3.annotate(row['Site_Code'], 
                xy=(row['Avg_Visibility_m'], row['MAE_m']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=8, color='red', fontweight='bold')

# Plot 4: Box plot by sample size category
ax4 = axes[1, 1]
sample_categories = []
mae_by_category = []
for _, row in df.iterrows():
    if row['Total_Samples'] < 30:
        sample_categories.append('Low\n(<30)')
    elif row['Total_Samples'] < 60:
        sample_categories.append('Medium\n(30-59)')
    else:
        sample_categories.append('High\n(≥60)')
    mae_by_category.append(row['MAE_m'])

df['Sample_Category'] = sample_categories
box_data = [df[df['Sample_Category'] == cat]['MAE_m'].values 
            for cat in ['Low\n(<30)', 'Medium\n(30-59)', 'High\n(≥60)']]
bp = ax4.boxplot(box_data, labels=['Low\n(<30)', 'Medium\n(30-59)', 'High\n(≥60)'],
                 patch_artist=True, showmeans=True)
# Color the boxes
colors = ['lightgreen', 'yellow', 'lightcoral']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
ax4.set_xlabel('Sample Size Category', fontsize=12)
ax4.set_ylabel('MAE (m)', fontsize=12)
ax4.set_title('Model Error Distribution by Sample Size', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('plots/sample_size_accuracy_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/sample_size_accuracy_analysis.png")

# Additional plot: Visibility variability analysis
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))
fig2.suptitle('Visibility Variability Analysis for High-Sample Sites', fontsize=16, fontweight='bold')

# Calculate visibility std for each site from original data
site_stats = []
for site_code in df['Site_Code']:
    site_data = vis_data[vis_data['site_code'] == site_code]
    if len(site_data) > 0:
        site_stats.append({
            'Site_Code': site_code,
            'Vis_StdDev': site_data['visibility'].std(),
            'Vis_Range': site_data['visibility'].max() - site_data['visibility'].min(),
            'Vis_CV': site_data['visibility'].std() / site_data['visibility'].mean()
        })

stats_df = pd.DataFrame(site_stats)
df_merged = df.merge(stats_df, on='Site_Code')

# Plot: Visibility variability vs MAE
ax_left = axes2[0]
scatter_var = ax_left.scatter(df_merged['Vis_StdDev'], df_merged['MAE_m'],
                              c=df_merged['Total_Samples'], cmap='viridis',
                              s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax_left.set_xlabel('Visibility Std Dev (m)', fontsize=12)
ax_left.set_ylabel('MAE (m)', fontsize=12)
ax_left.set_title('Visibility Variability vs. Model Error', fontsize=13, fontweight='bold')
ax_left.grid(True, alpha=0.3)
cbar_var = plt.colorbar(scatter_var, ax=ax_left)
cbar_var.set_label('Total Samples', fontsize=10)

# Annotate high-sample, high-variability sites
high_var_high_sample = df_merged[(df_merged['Total_Samples'] >= 50) & (df_merged['Vis_StdDev'] > 3)]
for _, row in high_var_high_sample.iterrows():
    ax_left.annotate(row['Site_Code'], 
                    xy=(row['Vis_StdDev'], row['MAE_m']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, color='red', fontweight='bold')

# Plot: Sample size vs visibility variability
ax_right = axes2[1]
scatter_samp = ax_right.scatter(df_merged['Total_Samples'], df_merged['Vis_StdDev'],
                               c=df_merged['MAE_m'], cmap='RdYlGn_r',
                               s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax_right.set_xlabel('Total Samples', fontsize=12)
ax_right.set_ylabel('Visibility Std Dev (m)', fontsize=12)
ax_right.set_title('Sample Size vs. Visibility Variability', fontsize=13, fontweight='bold')
ax_right.grid(True, alpha=0.3)
cbar_samp = plt.colorbar(scatter_samp, ax=ax_right)
cbar_samp.set_label('MAE (m)', fontsize=10)

# Annotate problematic sites
for _, row in high_sample_poor_accuracy.iterrows():
    row_merged = df_merged[df_merged['Site_Code'] == row['Site_Code']].iloc[0]
    ax_right.annotate(row['Site_Code'], 
                     xy=(row['Total_Samples'], row_merged['Vis_StdDev']),
                     xytext=(5, 5), textcoords='offset points',
                     fontsize=8, color='red', fontweight='bold')

plt.tight_layout()
plt.savefig('plots/visibility_variability_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/visibility_variability_analysis.png")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print("\nKey Findings:")
print("1. Several high-sample sites have poor model accuracy")
print("2. Check the correlations above to see if this is a systematic issue")
print("3. Visibility variability may be a key factor")
print("4. Consider site-specific modeling improvements for problematic locations")
print("\nRecommendations:")
print("- Investigate site-specific environmental factors")
print("- Consider adding local predictors (bathymetry, proximity to features)")
print("- Explore non-linear relationships for high-variability sites")
print("- Potentially exclude or separately model the most problematic sites")
