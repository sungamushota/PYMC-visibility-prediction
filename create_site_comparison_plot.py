#!/usr/bin/env python3
"""
Create a detailed comparison plot of the problematic high-sample sites.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('models/site_performance_metrics.csv')
vis_data = pd.read_csv('VIS_Reports_Augmented.csv')
vis_data['site_code'] = vis_data['site'].str.extract(r'\(([A-Z0-9]+)\)$')[0]

# Focus on sites with >50 samples
high_sample_sites = df[df['Total_Samples'] >= 50].sort_values('Total_Samples', ascending=False)

# Create detailed comparison figure
fig = plt.figure(figsize=(18, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Title
fig.suptitle('Detailed Analysis: High-Sample Sites Performance', 
             fontsize=18, fontweight='bold', y=0.98)

# Site codes and colors
site_codes = high_sample_sites['Site_Code'].tolist()
colors = []
for _, row in high_sample_sites.iterrows():
    if row['Within_3m_%'] < 40:
        colors.append('darkred')
    elif row['Within_3m_%'] < 60:
        colors.append('orange')
    else:
        colors.append('green')

# Plot 1: Bar chart of samples by site
ax1 = fig.add_subplot(gs[0, :2])
bars1 = ax1.bar(range(len(site_codes)), high_sample_sites['Total_Samples'], color=colors, alpha=0.7, edgecolor='black')
ax1.set_xticks(range(len(site_codes)))
ax1.set_xticklabels(site_codes, rotation=45, ha='right')
ax1.set_ylabel('Total Samples', fontsize=12, fontweight='bold')
ax1.set_title('Sample Size by Site (≥50 samples)', fontsize=14, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)
# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars1, high_sample_sites['Total_Samples'])):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
             str(int(val)), ha='center', va='bottom', fontsize=10, fontweight='bold')

# Plot 2: Performance legend/key
ax2 = fig.add_subplot(gs[0, 2])
ax2.axis('off')
legend_text = """
PERFORMANCE RATING:

🟢 GREEN (≥60%):
   Good accuracy
   
🟠 ORANGE (40-60%):
   Needs improvement
   
🔴 RED (<40%):
   Critical - Poor accuracy

Metric: % predictions 
within ±3m of actual
"""
ax2.text(0.1, 0.5, legend_text, fontsize=11, verticalalignment='center',
         fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Plot 3: MAE comparison
ax3 = fig.add_subplot(gs[1, 0])
bars3 = ax3.barh(range(len(site_codes)), high_sample_sites['MAE_m'], color=colors, alpha=0.7, edgecolor='black')
ax3.set_yticks(range(len(site_codes)))
ax3.set_yticklabels(site_codes)
ax3.set_xlabel('MAE (meters)', fontsize=11, fontweight='bold')
ax3.set_title('Mean Absolute Error', fontsize=13, fontweight='bold')
ax3.axvline(x=3.0, color='orange', linestyle='--', alpha=0.5, linewidth=2, label='3m threshold')
ax3.grid(axis='x', alpha=0.3)
ax3.legend()
ax3.invert_yaxis()
# Add value labels
for i, (bar, val) in enumerate(zip(bars3, high_sample_sites['MAE_m'])):
    ax3.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}m', va='center', fontsize=9, fontweight='bold')

# Plot 4: Within ±3m percentage
ax4 = fig.add_subplot(gs[1, 1])
bars4 = ax4.barh(range(len(site_codes)), high_sample_sites['Within_3m_%'], color=colors, alpha=0.7, edgecolor='black')
ax4.set_yticks(range(len(site_codes)))
ax4.set_yticklabels(site_codes)
ax4.set_xlabel('Accuracy (%)', fontsize=11, fontweight='bold')
ax4.set_title('% Predictions Within ±3m', fontsize=13, fontweight='bold')
ax4.axvline(x=60, color='orange', linestyle='--', alpha=0.5, linewidth=2, label='60% target')
ax4.axvline(x=80, color='green', linestyle='--', alpha=0.5, linewidth=2, label='80% good')
ax4.grid(axis='x', alpha=0.3)
ax4.legend()
ax4.invert_yaxis()
# Add value labels
for i, (bar, val) in enumerate(zip(bars4, high_sample_sites['Within_3m_%'])):
    ax4.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}%', va='center', fontsize=9, fontweight='bold')

# Plot 5: R² Score
ax5 = fig.add_subplot(gs[1, 2])
r2_values = high_sample_sites['R2_Score'].values
bars5 = ax5.barh(range(len(site_codes)), r2_values, color=colors, alpha=0.7, edgecolor='black')
ax5.set_yticks(range(len(site_codes)))
ax5.set_yticklabels(site_codes)
ax5.set_xlabel('R² Score', fontsize=11, fontweight='bold')
ax5.set_title('R² Score (Model Fit)', fontsize=13, fontweight='bold')
ax5.axvline(x=0, color='red', linestyle='-', alpha=0.3, linewidth=2)
ax5.grid(axis='x', alpha=0.3)
ax5.invert_yaxis()
# Add value labels
for i, (bar, val) in enumerate(zip(bars5, r2_values)):
    ax5.text(bar.get_width() + 0.1 if val > 0 else bar.get_width() - 0.1, 
             bar.get_y() + bar.get_height()/2,
             f'{val:.2f}', va='center', ha='left' if val > 0 else 'right',
             fontsize=9, fontweight='bold')

# Plot 6: Visibility variability
ax6 = fig.add_subplot(gs[2, 0])
vis_stddevs = []
for site_code in site_codes:
    site_data = vis_data[vis_data['site_code'] == site_code]
    if len(site_data) > 0:
        vis_stddevs.append(site_data['visibility'].std())
    else:
        vis_stddevs.append(0)

bars6 = ax6.barh(range(len(site_codes)), vis_stddevs, color=colors, alpha=0.7, edgecolor='black')
ax6.set_yticks(range(len(site_codes)))
ax6.set_yticklabels(site_codes)
ax6.set_xlabel('Std Dev (meters)', fontsize=11, fontweight='bold')
ax6.set_title('Visibility Variability', fontsize=13, fontweight='bold')
ax6.grid(axis='x', alpha=0.3)
ax6.invert_yaxis()
# Add value labels
for i, (bar, val) in enumerate(zip(bars6, vis_stddevs)):
    ax6.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}m', va='center', fontsize=9, fontweight='bold')

# Plot 7: Visibility range
ax7 = fig.add_subplot(gs[2, 1])
vis_ranges = []
vis_mins = []
vis_maxs = []
for site_code in site_codes:
    site_data = vis_data[vis_data['site_code'] == site_code]
    if len(site_data) > 0:
        vis_mins.append(site_data['visibility'].min())
        vis_maxs.append(site_data['visibility'].max())
        vis_ranges.append(site_data['visibility'].max() - site_data['visibility'].min())
    else:
        vis_mins.append(0)
        vis_maxs.append(0)
        vis_ranges.append(0)

# Create horizontal range plot
for i, (vmin, vmax) in enumerate(zip(vis_mins, vis_maxs)):
    ax7.plot([vmin, vmax], [i, i], color=colors[i], linewidth=6, alpha=0.7)
    ax7.plot(vmin, i, 'o', color=colors[i], markersize=8, markeredgecolor='black', markeredgewidth=1)
    ax7.plot(vmax, i, 'o', color=colors[i], markersize=8, markeredgecolor='black', markeredgewidth=1)
    # Add range label
    ax7.text(vmax + 0.5, i, f'{vis_ranges[i]:.0f}m range', 
             va='center', fontsize=8, style='italic')

ax7.set_yticks(range(len(site_codes)))
ax7.set_yticklabels(site_codes)
ax7.set_xlabel('Visibility (meters)', fontsize=11, fontweight='bold')
ax7.set_title('Observed Visibility Range', fontsize=13, fontweight='bold')
ax7.grid(axis='x', alpha=0.3)
ax7.invert_yaxis()

# Plot 8: Summary table
ax8 = fig.add_subplot(gs[2, 2])
ax8.axis('off')

# Create summary statistics
summary_stats = []
for _, row in high_sample_sites.iterrows():
    site_code = row['Site_Code']
    site_vis = vis_data[vis_data['site_code'] == site_code]
    
    status = '🔴 CRITICAL' if row['Within_3m_%'] < 40 else ('🟠 POOR' if row['Within_3m_%'] < 60 else '🟢 GOOD')
    
    summary_stats.append({
        'Code': site_code,
        'Status': status,
        'n': int(row['Total_Samples']),
        'Acc%': f"{row['Within_3m_%']:.0f}%"
    })

summary_df = pd.DataFrame(summary_stats)

table_text = "SUMMARY STATUS\n" + "="*30 + "\n\n"
for _, row in summary_df.iterrows():
    table_text += f"{row['Code']:4s} | {row['Status']:12s}\n"
    table_text += f"      n={row['n']:3d}, acc={row['Acc%']}\n\n"

ax8.text(0.1, 0.95, table_text, fontsize=10, verticalalignment='top',
         fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))

# Add footnote
fig.text(0.5, 0.01, 
         'Critical Finding: 3 of 8 high-sample sites (≥50 observations) show poor accuracy (<60% within ±3m)',
         ha='center', fontsize=11, style='italic', 
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))

plt.savefig('plots/high_sample_sites_detailed_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: plots/high_sample_sites_detailed_comparison.png")

# Also create a simple summary CSV for easy reference
summary_full = []
for _, row in high_sample_sites.iterrows():
    site_code = row['Site_Code']
    site_vis = vis_data[vis_data['site_code'] == site_code]
    
    if len(site_vis) > 0:
        vis_range = site_vis['visibility'].max() - site_vis['visibility'].min()
        vis_std = site_vis['visibility'].std()
        vis_cv = vis_std / site_vis['visibility'].mean() if site_vis['visibility'].mean() > 0 else 0
    else:
        vis_range = vis_std = vis_cv = np.nan
    
    summary_full.append({
        'Site_Code': site_code,
        'Site_Name': row['Site_Name'],
        'Total_Samples': row['Total_Samples'],
        'MAE_m': row['MAE_m'],
        'RMSE_m': row['RMSE_m'],
        'R2_Score': row['R2_Score'],
        'Within_3m_%': row['Within_3m_%'],
        'Avg_Visibility_m': row['Avg_Visibility_m'],
        'Vis_StdDev_m': vis_std,
        'Vis_Range_m': vis_range,
        'Vis_CV': vis_cv,
        'Performance_Category': 'Good' if row['Within_3m_%'] >= 60 else ('Poor' if row['Within_3m_%'] >= 40 else 'Critical'),
        'Priority': 'HIGH' if row['Within_3m_%'] < 40 else ('MEDIUM' if row['Within_3m_%'] < 60 else 'LOW')
    })

summary_full_df = pd.DataFrame(summary_full)
summary_full_df.to_csv('models/high_sample_sites_analysis.csv', index=False)
print("✓ Saved: models/high_sample_sites_analysis.csv")

print("\n" + "="*60)
print("HIGH-SAMPLE SITES REQUIRING ATTENTION:")
print("="*60)
priority_sites = summary_full_df[summary_full_df['Priority'].isin(['HIGH', 'MEDIUM'])].sort_values('Within_3m_%')
print(priority_sites[['Site_Code', 'Site_Name', 'Total_Samples', 'Within_3m_%', 'Priority']].to_string(index=False))
