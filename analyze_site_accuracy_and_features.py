#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analysis script to investigate:
1. Why sites with many repeats have poor accuracy
2. Feature correlations to visibility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("Site Accuracy and Feature Correlation Analysis")
print("="*80)

# Load data
print("\n1. Loading data...")
data_path = 'stormglass_output/daily_rolling_averages.csv'
df = pd.read_csv(data_path)
print(f"   Loaded {len(df)} records")

# Load site performance metrics
perf_df = pd.read_csv('models/site_performance_metrics.csv')
print(f"   Loaded performance metrics for {len(perf_df)} sites")

# Merge performance metrics with site counts
site_counts = df['site'].value_counts().reset_index()
site_counts.columns = ['Site_Code', 'Actual_Samples']
perf_df = perf_df.merge(site_counts, on='Site_Code', how='left')

# Identify sites with many repeats but poor accuracy
perf_df['Poor_Accuracy'] = perf_df['MAE_m'] > 3.0
perf_df['Many_Repeats'] = perf_df['Total_Samples'] >= 50
perf_df['High_Samples_Poor_Accuracy'] = perf_df['Many_Repeats'] & perf_df['Poor_Accuracy']

print("\n2. Sites with many repeats but poor accuracy:")
problem_sites = perf_df[perf_df['High_Samples_Poor_Accuracy']].sort_values('MAE_m', ascending=False)
print(problem_sites[['Site_Code', 'Site_Name', 'Total_Samples', 'MAE_m', 'RMSE_m', 'R2_Score', 'Avg_Visibility_m']].to_string(index=False))

# --- Analysis 1: Why do high-sample sites have poor accuracy? ---
print("\n" + "="*80)
print("ANALYSIS 1: Investigating Poor Accuracy in High-Sample Sites")
print("="*80)

# Get feature columns
feature_cols = [col for col in df.columns if any(x in col for x in ['roll_avg', 'sum_last', 'sin', 'cos'])]
target_col = 'visibility'

# Prepare data for analysis
analysis_df = df[['site', target_col] + feature_cols].copy()
analysis_df = analysis_df.dropna(subset=[target_col])

# Calculate statistics per site
site_stats = []
for site_code in problem_sites['Site_Code'].values:
    site_data = analysis_df[analysis_df['site'] == site_code].copy()
    if len(site_data) == 0:
        continue
    
    stats = {
        'Site_Code': site_code,
        'N_Samples': len(site_data),
        'Visibility_Mean': site_data[target_col].mean(),
        'Visibility_Std': site_data[target_col].std(),
        'Visibility_Min': site_data[target_col].min(),
        'Visibility_Max': site_data[target_col].max(),
        'Visibility_Range': site_data[target_col].max() - site_data[target_col].min(),
        'Visibility_CV': site_data[target_col].std() / site_data[target_col].mean() if site_data[target_col].mean() > 0 else 0,
    }
    
    # Check for missing values in features
    missing_pct = site_data[feature_cols].isna().sum().sum() / (len(site_data) * len(feature_cols)) * 100
    stats['Missing_Features_Pct'] = missing_pct
    
    site_stats.append(stats)

site_stats_df = pd.DataFrame(site_stats)
site_stats_df = site_stats_df.merge(problem_sites[['Site_Code', 'MAE_m', 'RMSE_m', 'R2_Score']], on='Site_Code')

print("\nCharacteristics of high-sample, poor-accuracy sites:")
print(site_stats_df.to_string(index=False))

# Compare with good-accuracy sites
good_sites = perf_df[(perf_df['Total_Samples'] >= 50) & (perf_df['MAE_m'] <= 2.5)].sort_values('MAE_m')
print("\n\nFor comparison - High-sample sites with GOOD accuracy:")
print(good_sites[['Site_Code', 'Site_Name', 'Total_Samples', 'MAE_m', 'Avg_Visibility_m']].to_string(index=False))

# --- Visualization 1: Site Accuracy vs Number of Samples ---
print("\n3. Creating visualizations...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: MAE vs Total Samples
ax1 = axes[0, 0]
scatter = ax1.scatter(perf_df['Total_Samples'], perf_df['MAE_m'], 
                     c=perf_df['R2_Score'], cmap='RdYlGn', 
                     s=100, alpha=0.7, edgecolors='black', linewidth=1)
ax1.set_xlabel('Total Samples (Number of Reports)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Mean Absolute Error (MAE) in meters', fontsize=12, fontweight='bold')
ax1.set_title('Site Accuracy vs Number of Samples', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Highlight problem sites
problem_mask = perf_df['High_Samples_Poor_Accuracy']
ax1.scatter(perf_df.loc[problem_mask, 'Total_Samples'], 
           perf_df.loc[problem_mask, 'MAE_m'],
           s=200, marker='X', color='red', edgecolors='darkred', 
           linewidth=2, label='High Samples, Poor Accuracy', zorder=5)

# Add site labels for problem sites
for idx, row in perf_df[problem_mask].iterrows():
    ax1.annotate(row['Site_Code'], 
                (row['Total_Samples'], row['MAE_m']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=9, fontweight='bold', color='darkred')

plt.colorbar(scatter, ax=ax1, label='R² Score')
ax1.legend()

# Plot 2: Visibility Range vs MAE
ax2 = axes[0, 1]
if len(site_stats_df) > 0:
    ax2.scatter(site_stats_df['Visibility_Range'], site_stats_df['MAE_m'], 
               s=100, alpha=0.7, color='coral', edgecolors='black')
    for idx, row in site_stats_df.iterrows():
        ax2.annotate(row['Site_Code'], 
                    (row['Visibility_Range'], row['MAE_m']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)
ax2.set_xlabel('Visibility Range (Max - Min)', fontsize=12, fontweight='bold')
ax2.set_ylabel('MAE (meters)', fontsize=12, fontweight='bold')
ax2.set_title('Visibility Variability vs Prediction Error', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Plot 3: Coefficient of Variation vs MAE
ax3 = axes[1, 0]
if len(site_stats_df) > 0:
    ax3.scatter(site_stats_df['Visibility_CV'], site_stats_df['MAE_m'], 
               s=100, alpha=0.7, color='steelblue', edgecolors='black')
    for idx, row in site_stats_df.iterrows():
        ax3.annotate(row['Site_Code'], 
                    (row['Visibility_CV'], row['MAE_m']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)
ax3.set_xlabel('Coefficient of Variation (Std/Mean)', fontsize=12, fontweight='bold')
ax3.set_ylabel('MAE (meters)', fontsize=12, fontweight='bold')
ax3.set_title('Visibility Variability (CV) vs Prediction Error', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3)

# Plot 4: Average Visibility vs MAE
ax4 = axes[1, 1]
scatter2 = ax4.scatter(perf_df['Avg_Visibility_m'], perf_df['MAE_m'],
                      c=perf_df['Total_Samples'], cmap='viridis',
                      s=100, alpha=0.7, edgecolors='black', linewidth=1)
ax4.set_xlabel('Average Visibility (meters)', fontsize=12, fontweight='bold')
ax4.set_ylabel('MAE (meters)', fontsize=12, fontweight='bold')
ax4.set_title('Average Visibility vs Prediction Error', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3)

# Highlight problem sites
ax4.scatter(perf_df.loc[problem_mask, 'Avg_Visibility_m'], 
           perf_df.loc[problem_mask, 'MAE_m'],
           s=200, marker='X', color='red', edgecolors='darkred', 
           linewidth=2, zorder=5)

plt.colorbar(scatter2, ax=ax4, label='Total Samples')
plt.tight_layout()
plt.savefig('plots/site_accuracy_analysis.png', dpi=300, bbox_inches='tight')
print("   Saved: plots/site_accuracy_analysis.png")
plt.close()

# --- Analysis 2: Feature Correlations to Visibility ---
print("\n" + "="*80)
print("ANALYSIS 2: Feature Correlations to Visibility")
print("="*80)

# Prepare features
print("\n4. Calculating feature correlations...")
feature_cols = [col for col in df.columns if any(x in col for x in ['roll_avg', 'sum_last', 'sin', 'cos'])]
X = df[feature_cols].copy()
y = df[target_col].copy()

# Remove rows with missing target
valid_mask = ~y.isna()
X = X[valid_mask]
y = y[valid_mask]

# Impute missing values
imputer = SimpleImputer(strategy='median')
X_imputed = imputer.fit_transform(X)
X_imputed = pd.DataFrame(X_imputed, columns=feature_cols, index=X.index)

# Calculate correlations
correlations = []
for col in feature_cols:
    corr = X_imputed[col].corr(y)
    if not np.isnan(corr):
        correlations.append({
            'Feature': col,
            'Correlation': corr,
            'Abs_Correlation': abs(corr)
        })

corr_df = pd.DataFrame(correlations)
corr_df = corr_df.sort_values('Abs_Correlation', ascending=False)

print(f"\nTop 20 features most correlated with visibility:")
print(corr_df.head(20).to_string(index=False))

# Group correlations by feature type
corr_df['Feature_Type'] = corr_df['Feature'].apply(lambda x: 
    'Swell' if 'swell' in x.lower() else
    'Wave' if 'wave' in x.lower() else
    'Wind' if 'wind' in x.lower() else
    'Precipitation' if 'precipitation' in x.lower() else
    'Temperature' if 'temperature' in x.lower() else
    'Pressure' if 'pressure' in x.lower() else
    'Cloud' if 'cloud' in x.lower() else
    'Temporal' if any(t in x.lower() for t in ['sin', 'cos', 'month', 'day']) else
    'Other'
)

# --- Visualization 2: Feature Correlations ---
fig, axes = plt.subplots(2, 1, figsize=(16, 14))

# Plot 1: Top correlations bar plot
ax1 = axes[0]
top_n = 30
top_corr = corr_df.head(top_n)
colors = ['red' if x < 0 else 'green' for x in top_corr['Correlation']]
bars = ax1.barh(range(len(top_corr)), top_corr['Correlation'], color=colors, alpha=0.7)
ax1.set_yticks(range(len(top_corr)))
ax1.set_yticklabels(top_corr['Feature'], fontsize=9)
ax1.set_xlabel('Correlation with Visibility', fontsize=12, fontweight='bold')
ax1.set_title(f'Top {top_n} Features Correlated with Visibility', fontsize=14, fontweight='bold')
ax1.axvline(x=0, color='black', linestyle='--', linewidth=1)
ax1.grid(True, alpha=0.3, axis='x')
ax1.invert_yaxis()

# Add correlation values on bars
for i, (idx, row) in enumerate(top_corr.iterrows()):
    ax1.text(row['Correlation'], i, f" {row['Correlation']:.3f}", 
            va='center', fontsize=8, fontweight='bold')

# Plot 2: Correlation heatmap by feature type
ax2 = axes[1]
feature_types = corr_df['Feature_Type'].unique()
type_corr_summary = corr_df.groupby('Feature_Type').agg({
    'Correlation': ['mean', 'std', 'count']
}).reset_index()
type_corr_summary.columns = ['Feature_Type', 'Mean_Corr', 'Std_Corr', 'Count']
type_corr_summary = type_corr_summary.sort_values('Mean_Corr', key=abs, ascending=False)

# Create a pivot table for heatmap
pivot_data = []
for feature_type in type_corr_summary['Feature_Type']:
    type_features = corr_df[corr_df['Feature_Type'] == feature_type]
    for window in ['2day', '3day', '4day', 'other']:
        window_features = type_features[type_features['Feature'].str.contains(window, na=False)]
        if len(window_features) > 0:
            pivot_data.append({
                'Feature_Type': feature_type,
                'Window': window.replace('day', '-day').replace('other', 'Other'),
                'Mean_Correlation': window_features['Correlation'].mean(),
                'Count': len(window_features)
            })

if pivot_data:
    pivot_df = pd.DataFrame(pivot_data)
    pivot_table = pivot_df.pivot(index='Feature_Type', columns='Window', values='Mean_Correlation')
    
    sns.heatmap(pivot_table, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
                ax=ax2, cbar_kws={'label': 'Mean Correlation'}, linewidths=0.5)
    ax2.set_title('Feature Correlations by Type and Rolling Window', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Rolling Window', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Feature Type', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('plots/feature_correlations_visibility.png', dpi=300, bbox_inches='tight')
print("   Saved: plots/feature_correlations_visibility.png")
plt.close()

# --- Detailed analysis for problem sites ---
print("\n" + "="*80)
print("ANALYSIS 3: Detailed Feature Analysis for Problem Sites")
print("="*80)

for site_code in problem_sites['Site_Code'].head(3).values:
    print(f"\n--- {site_code} ({problem_sites[problem_sites['Site_Code']==site_code]['Site_Name'].values[0]}) ---")
    site_data = df[df['site'] == site_code].copy()
    
    if len(site_data) == 0:
        continue
    
    site_y = site_data[target_col].dropna()
    site_X = site_data[feature_cols].copy()
    
    # Calculate site-specific correlations
    site_corrs = []
    for col in feature_cols:
        site_col_data = site_X[col].dropna()
        if len(site_col_data) > 5:  # Need enough data
            corr = site_col_data.corr(site_y.loc[site_col_data.index])
            if not np.isnan(corr):
                site_corrs.append({
                    'Feature': col,
                    'Correlation': corr,
                    'Abs_Correlation': abs(corr)
                })
    
    if site_corrs:
        site_corr_df = pd.DataFrame(site_corrs).sort_values('Abs_Correlation', ascending=False)
        print(f"Top 10 features correlated with visibility at this site:")
        print(site_corr_df.head(10)[['Feature', 'Correlation']].to_string(index=False))
        
        # Compare with global correlations
        site_corr_df = site_corr_df.merge(corr_df[['Feature', 'Correlation']], 
                                         on='Feature', suffixes=('_Site', '_Global'))
        site_corr_df['Difference'] = site_corr_df['Correlation_Site'] - site_corr_df['Correlation_Global']
        print(f"\nFeatures where site correlation differs most from global:")
        print(site_corr_df.nlargest(5, 'Difference', keep='all')[['Feature', 'Correlation_Site', 'Correlation_Global', 'Difference']].to_string(index=False))

# Save correlation data
corr_df.to_csv('models/feature_correlations_visibility.csv', index=False)
print("\n   Saved: models/feature_correlations_visibility.csv")

print("\n" + "="*80)
print("Analysis Complete!")
print("="*80)
print("\nKey Findings:")
print("1. Check plots/site_accuracy_analysis.png for site accuracy patterns")
print("2. Check plots/feature_correlations_visibility.png for feature correlations")
print("3. Check models/feature_correlations_visibility.csv for detailed correlation data")
