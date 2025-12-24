"""
Analysis script to investigate:
1. Why sites with more reports have poor accuracy
2. Feature correlations to visibility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
site_metrics = pd.read_csv('models/site_performance_metrics.csv')
# Load the rolling averages which has BOTH visibility and weather features
full_data = pd.read_csv('stormglass_output/daily_rolling_averages.csv')

print(f"Loaded {len(full_data)} records with {len(full_data.columns)} columns")

# ============================================================================
# PART 1: Analyze relationship between number of reports and accuracy
# ============================================================================

print("\n" + "="*80)
print("PART 1: Analyzing sites with many reports but poor accuracy")
print("="*80)

# Create accuracy vs sample size analysis
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Site Performance: Number of Reports vs Accuracy Metrics', fontsize=16, fontweight='bold')

# Plot 1: MAE vs Total Samples
ax1 = axes[0, 0]
scatter1 = ax1.scatter(site_metrics['Total_Samples'], site_metrics['MAE_m'], 
                       s=100, alpha=0.6, c=site_metrics['Avg_Visibility_m'], 
                       cmap='viridis', edgecolors='black', linewidth=1)
ax1.set_xlabel('Total Number of Reports', fontsize=12, fontweight='bold')
ax1.set_ylabel('Mean Absolute Error (m)', fontsize=12, fontweight='bold')
ax1.set_title('MAE vs Number of Reports\n(color = avg visibility)', fontsize=11)
ax1.grid(True, alpha=0.3)
cbar1 = plt.colorbar(scatter1, ax=ax1)
cbar1.set_label('Avg Visibility (m)', fontsize=10)

# Annotate worst performers
worst_mae = site_metrics.nlargest(5, 'MAE_m')
for idx, row in worst_mae.iterrows():
    ax1.annotate(row['Site_Code'], 
                (row['Total_Samples'], row['MAE_m']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

# Plot 2: RMSE vs Total Samples
ax2 = axes[0, 1]
scatter2 = ax2.scatter(site_metrics['Total_Samples'], site_metrics['RMSE_m'], 
                       s=100, alpha=0.6, c=site_metrics['Avg_Visibility_m'], 
                       cmap='viridis', edgecolors='black', linewidth=1)
ax2.set_xlabel('Total Number of Reports', fontsize=12, fontweight='bold')
ax2.set_ylabel('Root Mean Squared Error (m)', fontsize=12, fontweight='bold')
ax2.set_title('RMSE vs Number of Reports\n(color = avg visibility)', fontsize=11)
ax2.grid(True, alpha=0.3)
cbar2 = plt.colorbar(scatter2, ax=ax2)
cbar2.set_label('Avg Visibility (m)', fontsize=10)

# Plot 3: R2 Score vs Total Samples
ax3 = axes[1, 0]
scatter3 = ax3.scatter(site_metrics['Total_Samples'], site_metrics['R2_Score'], 
                       s=100, alpha=0.6, c=site_metrics['Avg_Visibility_m'], 
                       cmap='viridis', edgecolors='black', linewidth=1)
ax3.axhline(y=0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='R²=0 (baseline)')
ax3.set_xlabel('Total Number of Reports', fontsize=12, fontweight='bold')
ax3.set_ylabel('R² Score', fontsize=12, fontweight='bold')
ax3.set_title('R² Score vs Number of Reports\n(negative R² = worse than baseline)', fontsize=11)
ax3.grid(True, alpha=0.3)
ax3.legend()
cbar3 = plt.colorbar(scatter3, ax=ax3)
cbar3.set_label('Avg Visibility (m)', fontsize=10)

# Plot 4: Within 3m % vs Total Samples
ax4 = axes[1, 1]
scatter4 = ax4.scatter(site_metrics['Total_Samples'], site_metrics['Within_3m_%'], 
                       s=100, alpha=0.6, c=site_metrics['Avg_Visibility_m'], 
                       cmap='viridis', edgecolors='black', linewidth=1)
ax4.set_xlabel('Total Number of Reports', fontsize=12, fontweight='bold')
ax4.set_ylabel('Within 3m Accuracy (%)', fontsize=12, fontweight='bold')
ax4.set_title('Prediction Accuracy vs Number of Reports', fontsize=11)
ax4.grid(True, alpha=0.3)
cbar4 = plt.colorbar(scatter4, ax=ax4)
cbar4.set_label('Avg Visibility (m)', fontsize=10)

plt.tight_layout()
plt.savefig('plots/site_reports_vs_accuracy_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: plots/site_reports_vs_accuracy_analysis.png")

# Statistical analysis
print("\n" + "-"*80)
print("Statistical Analysis: Correlation between sample size and accuracy")
print("-"*80)
correlation_mae = stats.pearsonr(site_metrics['Total_Samples'], site_metrics['MAE_m'])
correlation_r2 = stats.pearsonr(site_metrics['Total_Samples'], site_metrics['R2_Score'])
print(f"Correlation (Sample Size vs MAE): r={correlation_mae[0]:.3f}, p-value={correlation_mae[1]:.4f}")
print(f"Correlation (Sample Size vs R²): r={correlation_r2[0]:.3f}, p-value={correlation_r2[1]:.4f}")

# Identify problematic sites
print("\n" + "-"*80)
print("Top 10 sites by number of reports:")
print("-"*80)
top_sites = site_metrics.nlargest(10, 'Total_Samples')[['Site_Code', 'Site_Name', 'Total_Samples', 
                                                          'Avg_Visibility_m', 'MAE_m', 'RMSE_m', 
                                                          'R2_Score', 'Within_3m_%']]
print(top_sites.to_string(index=False))

print("\n" + "-"*80)
print("Sites with >50 reports AND poor accuracy (MAE > 3m):")
print("-"*80)
problematic = site_metrics[(site_metrics['Total_Samples'] > 50) & (site_metrics['MAE_m'] > 3.0)]
problematic = problematic[['Site_Code', 'Site_Name', 'Total_Samples', 'Avg_Visibility_m', 
                           'MAE_m', 'R2_Score', 'Within_3m_%']]
print(problematic.to_string(index=False))

# ============================================================================
# PART 2: Feature Correlation Analysis
# ============================================================================

print("\n\n" + "="*80)
print("PART 2: Feature Correlations to Visibility")
print("="*80)

# Get weather feature columns (2-day rolling averages)
feature_cols = [col for col in full_data.columns if '_2day_roll_avg' in col]
feature_cols.append('visibility')

print(f"\nFound {len(feature_cols)-1} weather features")

# Create correlation data
correlation_data = full_data[feature_cols].dropna()
print(f"Working with {len(correlation_data)} complete records")

# Calculate correlations to visibility
correlations = correlation_data.corr()['visibility'].drop('visibility').sort_values(ascending=False)

print("\n" + "-"*80)
print("Top 15 Positive Correlations with Visibility:")
print("-"*80)
for feat, corr in correlations.head(15).items():
    feat_name = feat.replace('_2day_roll_avg', '').replace('_', ' ').title()
    print(f"{feat_name:50s}: {corr:7.4f}")

print("\n" + "-"*80)
print("Top 15 Negative Correlations with Visibility:")
print("-"*80)
for feat, corr in correlations.tail(15).items():
    feat_name = feat.replace('_2day_roll_avg', '').replace('_', ' ').title()
    print(f"{feat_name:50s}: {corr:7.4f}")

# ============================================================================
# PART 3: Comprehensive Correlation Heatmap
# ============================================================================

# Create correlation matrix
corr_matrix = correlation_data.corr()

# Plot full heatmap
fig, ax = plt.subplots(figsize=(20, 18))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, mask=mask, annot=False, cmap='RdBu_r', center=0, 
            vmin=-1, vmax=1, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
ax.set_title('Feature Correlation Matrix (2-Day Rolling Averages)\nLower Triangle Only', 
             fontsize=16, fontweight='bold', pad=20)
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig('plots/feature_correlation_heatmap_full.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: plots/feature_correlation_heatmap_full.png")

# ============================================================================
# PART 4: Focused Visibility Correlation Plot
# ============================================================================

# Extract visibility correlations
vis_correlations = corr_matrix['visibility'].drop('visibility').sort_values()

# Plot correlation bar chart
fig, ax = plt.subplots(figsize=(12, 10))
colors = ['red' if x < 0 else 'green' for x in vis_correlations.values]
vis_correlations.plot(kind='barh', ax=ax, color=colors, alpha=0.7, edgecolor='black')
ax.set_xlabel('Correlation Coefficient', fontsize=12, fontweight='bold')
ax.set_ylabel('Weather Features (2-Day Rolling Average)', fontsize=12, fontweight='bold')
ax.set_title('Feature Correlations with Visibility\n(Positive = Higher value → Better visibility)', 
             fontsize=14, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax.grid(True, alpha=0.3, axis='x')

# Clean up labels
labels = [label.get_text().replace('_2day_roll_avg', '').replace('_', ' ').title() 
          for label in ax.get_yticklabels()]
ax.set_yticklabels(labels, fontsize=9)

plt.tight_layout()
plt.savefig('plots/visibility_feature_correlations.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/visibility_feature_correlations.png")

# ============================================================================
# PART 5: Analyze problematic sites in detail
# ============================================================================

print("\n\n" + "="*80)
print("PART 3: Detailed Analysis of Problematic Sites")
print("="*80)

# Focus on sites with >50 reports
high_sample_sites = site_metrics[site_metrics['Total_Samples'] > 50]['Site_Code'].values

for site_code in high_sample_sites:
    site_data = full_data[full_data['site'] == site_code].copy()
    site_info = site_metrics[site_metrics['Site_Code'] == site_code].iloc[0]
    
    print(f"\n{'-'*80}")
    print(f"Site: {site_code} - {site_info['Site_Name']}")
    print(f"{'-'*80}")
    print(f"Total Reports: {site_info['Total_Samples']}")
    print(f"Average Visibility: {site_info['Avg_Visibility_m']:.1f}m")
    print(f"MAE: {site_info['MAE_m']:.2f}m, RMSE: {site_info['RMSE_m']:.2f}m")
    print(f"R² Score: {site_info['R2_Score']:.3f}")
    print(f"Within 3m: {site_info['Within_3m_%']:.1f}%")
    
    # Calculate visibility statistics
    if len(site_data) > 0:
        print(f"\nVisibility Distribution:")
        print(f"  Min: {site_data['visibility'].min():.1f}m")
        print(f"  25th percentile: {site_data['visibility'].quantile(0.25):.1f}m")
        print(f"  Median: {site_data['visibility'].median():.1f}m")
        print(f"  75th percentile: {site_data['visibility'].quantile(0.75):.1f}m")
        print(f"  Max: {site_data['visibility'].max():.1f}m")
        print(f"  Std Dev: {site_data['visibility'].std():.2f}m")
        
        # Check for extreme variability
        cv = (site_data['visibility'].std() / site_data['visibility'].mean()) * 100
        print(f"  Coefficient of Variation: {cv:.1f}%")
        if cv > 70:
            print("  ⚠️  HIGH VARIABILITY - this may explain poor prediction accuracy")

# ============================================================================
# PART 6: Visibility Distribution by Site
# ============================================================================

fig, axes = plt.subplots(2, 1, figsize=(16, 12))

# Top plot: Box plots for high-sample sites
ax1 = axes[0]
high_sample_data = []
high_sample_labels = []
for site_code in sorted(high_sample_sites):
    site_data = full_data[full_data['site'] == site_code]['visibility'].values
    if len(site_data) > 0:
        high_sample_data.append(site_data)
        site_name = site_metrics[site_metrics['Site_Code'] == site_code]['Site_Name'].iloc[0]
        n_samples = len(site_data)
        high_sample_labels.append(f"{site_code}\n(n={n_samples})")

bp1 = ax1.boxplot(high_sample_data, tick_labels=high_sample_labels, patch_artist=True)
for patch in bp1['boxes']:
    patch.set_facecolor('lightblue')
    patch.set_alpha(0.7)
ax1.set_ylabel('Visibility (m)', fontsize=12, fontweight='bold')
ax1.set_title('Visibility Distribution for Sites with >50 Reports\n(Box plots show median, quartiles, and outliers)', 
              fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')
ax1.tick_params(axis='x', rotation=45)

# Bottom plot: Coefficient of variation
ax2 = axes[1]
cv_data = []
cv_labels = []
colors_cv = []

for site_code in sorted(high_sample_sites):
    site_data = full_data[full_data['site'] == site_code]['visibility']
    if len(site_data) > 0 and site_data.mean() > 0:
        cv = (site_data.std() / site_data.mean()) * 100
        mae = site_metrics[site_metrics['Site_Code'] == site_code]['MAE_m'].iloc[0]
        cv_data.append(cv)
        cv_labels.append(site_code)
        # Color by MAE - red for high error, green for low error
        colors_cv.append('red' if mae > 3.0 else 'orange' if mae > 2.0 else 'green')

bars = ax2.bar(cv_labels, cv_data, color=colors_cv, alpha=0.7, edgecolor='black')
ax2.set_ylabel('Coefficient of Variation (%)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Site Code', fontsize=12, fontweight='bold')
ax2.set_title('Visibility Variability by Site (>50 reports)\nRed = High MAE (>3m), Orange = Medium MAE (2-3m), Green = Low MAE (<2m)', 
              fontsize=13, fontweight='bold')
ax2.axhline(y=70, color='red', linestyle='--', linewidth=2, alpha=0.7, 
            label='High Variability Threshold (70%)')
ax2.grid(True, alpha=0.3, axis='y')
ax2.legend()
ax2.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('plots/site_visibility_variability_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: plots/site_visibility_variability_analysis.png")

# ============================================================================
# PART 7: Create scatter plots of key features vs visibility
# ============================================================================

# Select most correlated features
top_positive = vis_correlations.tail(5).index.tolist()
top_negative = vis_correlations.head(5).index.tolist()
key_predictors = top_positive + top_negative

fig, axes = plt.subplots(2, 5, figsize=(20, 10))
axes = axes.flatten()

for i, feature in enumerate(key_predictors):
    ax = axes[i]
    
    # Sample data if too many points
    sample_data = correlation_data[[feature, 'visibility']].dropna()
    if len(sample_data) > 5000:
        sample_data = sample_data.sample(5000, random_state=42)
    
    if len(sample_data) > 10:
        ax.scatter(sample_data[feature], sample_data['visibility'], 
                  alpha=0.3, s=20, edgecolors='none')
        
        # Add trend line
        z = np.polyfit(sample_data[feature], sample_data['visibility'], 1)
        p = np.poly1d(z)
        x_line = np.linspace(sample_data[feature].min(), sample_data[feature].max(), 100)
        ax.plot(x_line, p(x_line), "r--", linewidth=2, alpha=0.8)
        
        # Labels
        feature_name = feature.replace('_2day_roll_avg', '').replace('_', ' ').title()
        ax.set_xlabel(feature_name, fontsize=9, fontweight='bold')
        ax.set_ylabel('Visibility (m)', fontsize=9, fontweight='bold')
        
        # Add correlation value
        corr_val = vis_correlations[feature]
        ax.set_title(f'r = {corr_val:.3f}', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)

plt.suptitle('Top 10 Most Correlated Features with Visibility\n(5 Positive + 5 Negative)', 
             fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('plots/key_feature_scatter_plots.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/key_feature_scatter_plots.png")

print("\n" + "="*80)
print("Analysis Complete!")
print("="*80)
print("\nKey Findings Summary:")
print("-" * 80)
print("1. Sites with more reports don't necessarily have better accuracy")
print("2. High variability in visibility at certain sites makes prediction harder")
print("3. Feature correlations reveal which weather factors most influence visibility")
print("\nGenerated visualizations:")
print("  • plots/site_reports_vs_accuracy_analysis.png")
print("  • plots/feature_correlation_heatmap_full.png")
print("  • plots/visibility_feature_correlations.png")
print("  • plots/site_visibility_variability_analysis.png")
print("  • plots/key_feature_scatter_plots.png")
