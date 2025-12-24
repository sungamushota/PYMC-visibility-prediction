"""
Create a summary infographic showing key insights from the analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np

# Load data
site_metrics = pd.read_csv('models/site_performance_metrics.csv')

# Create figure
fig = plt.figure(figsize=(16, 20))
gs = fig.add_gridspec(6, 2, hspace=0.4, wspace=0.3)

# Title
fig.suptitle('Site Accuracy & Feature Correlation Analysis - Key Insights', 
             fontsize=24, fontweight='bold', y=0.98)

# ============================================================================
# Panel 1: Main Finding - No Correlation
# ============================================================================
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')

# Main message box
rect = Rectangle((0.1, 0.2), 0.8, 0.6, facecolor='#ff6b6b', alpha=0.3, 
                 edgecolor='red', linewidth=3)
ax1.add_patch(rect)

ax1.text(0.5, 0.5, '🚨 MORE REPORTS ≠ BETTER ACCURACY 🚨', 
         ha='center', va='center', fontsize=26, fontweight='bold',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

ax1.text(0.5, 0.25, 'Correlation: r = -0.289 (p = 0.172) - NOT SIGNIFICANT', 
         ha='center', va='center', fontsize=16, style='italic')

ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)

# ============================================================================
# Panel 2: Problematic Sites
# ============================================================================
ax2 = fig.add_subplot(gs[1, :])
ax2.axis('off')

# Title
ax2.text(0.5, 0.95, 'Problematic Sites (>50 reports, MAE > 3m)', 
         ha='center', va='top', fontsize=18, fontweight='bold')

# Create table data
problematic = site_metrics[(site_metrics['Total_Samples'] > 50) & (site_metrics['MAE_m'] > 3.0)]
problematic = problematic.sort_values('MAE_m', ascending=False)

# Manual table layout
y_start = 0.8
row_height = 0.25

for i, (idx, row) in enumerate(problematic.iterrows()):
    y_pos = y_start - i * row_height
    
    # Background color based on severity
    if row['MAE_m'] > 7:
        color = '#ff4444'
        severity = '🔴 CRITICAL'
    elif row['MAE_m'] > 5:
        color = '#ff9944'
        severity = '🟠 SEVERE'
    else:
        color = '#ffdd44'
        severity = '🟡 MODERATE'
    
    # Background rectangle
    rect = Rectangle((0.05, y_pos - 0.2), 0.9, 0.22, 
                     facecolor=color, alpha=0.2, edgecolor='black', linewidth=2)
    ax2.add_patch(rect)
    
    # Text content
    ax2.text(0.08, y_pos - 0.03, f"{row['Site_Code']}: {row['Site_Name']}", 
             fontsize=14, fontweight='bold')
    
    ax2.text(0.08, y_pos - 0.1, 
             f"Reports: {row['Total_Samples']} | MAE: {row['MAE_m']:.2f}m | "
             f"R²: {row['R2_Score']:.2f} | Accuracy: {row['Within_3m_%']:.1f}%", 
             fontsize=11)
    
    ax2.text(0.85, y_pos - 0.06, severity, 
             fontsize=12, fontweight='bold', ha='right')

ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)

# ============================================================================
# Panel 3: Top Positive Correlations
# ============================================================================
ax3 = fig.add_subplot(gs[2, 0])
ax3.axis('off')

ax3.text(0.5, 0.95, '✅ Positive Correlations\n(Higher → Better Visibility)', 
         ha='center', va='top', fontsize=14, fontweight='bold')

positive_features = [
    ('Humidity', 0.152),
    ('Wind Gust', 0.114),
    ('Atmos. Visibility', 0.033),
    ('Air Temperature', 0.030),
    ('Water Temperature', 0.015),
]

y_start = 0.8
for i, (feat, corr) in enumerate(positive_features):
    y = y_start - i * 0.15
    
    # Bar
    bar_width = abs(corr) * 2
    rect = Rectangle((0.5, y - 0.05), bar_width, 0.08, 
                     facecolor='green', alpha=0.6)
    ax3.add_patch(rect)
    
    # Text
    ax3.text(0.05, y, feat, fontsize=11, va='center')
    ax3.text(0.95, y, f'{corr:.3f}', fontsize=11, va='center', ha='right',
             fontweight='bold')

ax3.set_xlim(0, 1)
ax3.set_ylim(0, 1)

# ============================================================================
# Panel 4: Top Negative Correlations
# ============================================================================
ax4 = fig.add_subplot(gs[2, 1])
ax4.axis('off')

ax4.text(0.5, 0.95, '⚠️ Negative Correlations\n(Higher → Worse Visibility)', 
         ha='center', va='top', fontsize=14, fontweight='bold')

negative_features = [
    ('Swell Height', -0.164),
    ('Swell Period', -0.117),
    ('Wave Height', -0.103),
    ('Wave Period', -0.098),
    ('Wind Direction', -0.068),
]

y_start = 0.8
for i, (feat, corr) in enumerate(negative_features):
    y = y_start - i * 0.15
    
    # Bar
    bar_width = abs(corr) * 2
    rect = Rectangle((0.5 - bar_width, y - 0.05), bar_width, 0.08, 
                     facecolor='red', alpha=0.6)
    ax4.add_patch(rect)
    
    # Text
    ax4.text(0.05, y, feat, fontsize=11, va='center')
    ax4.text(0.95, y, f'{corr:.3f}', fontsize=11, va='center', ha='right',
             fontweight='bold')

ax4.set_xlim(0, 1)
ax4.set_ylim(0, 1)

# ============================================================================
# Panel 5: Key Insight Box
# ============================================================================
ax5 = fig.add_subplot(gs[3, :])
ax5.axis('off')

# Insight box
rect = Rectangle((0.05, 0.15), 0.9, 0.7, facecolor='#4ecdc4', alpha=0.3, 
                 edgecolor='teal', linewidth=3)
ax5.add_patch(rect)

ax5.text(0.5, 0.75, '🌊 KEY INSIGHT 🌊', 
         ha='center', va='center', fontsize=20, fontweight='bold')

ax5.text(0.5, 0.5, 'Wave and Swell Conditions Are the Strongest\nPredictors of Underwater Visibility', 
         ha='center', va='center', fontsize=16, style='italic',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

ax5.text(0.5, 0.25, 'Larger swells stir up sediment → Lower visibility', 
         ha='center', va='center', fontsize=14)

ax5.set_xlim(0, 1)
ax5.set_ylim(0, 1)

# ============================================================================
# Panel 6: Variability Analysis
# ============================================================================
ax6 = fig.add_subplot(gs[4, :])

# Get high-sample sites
high_sample_sites = site_metrics[site_metrics['Total_Samples'] > 50].sort_values('MAE_m')

x_pos = np.arange(len(high_sample_sites))
bars1 = ax6.bar(x_pos - 0.2, high_sample_sites['MAE_m'], 0.4, 
                label='MAE (m)', alpha=0.8, color='red')

# Calculate CV for each
cv_values = []
full_data = pd.read_csv('stormglass_output/daily_rolling_averages.csv')
for site_code in high_sample_sites['Site_Code']:
    site_data = full_data[full_data['site'] == site_code]['visibility']
    if len(site_data) > 0 and site_data.mean() > 0:
        cv = (site_data.std() / site_data.mean()) * 100
    else:
        cv = 0
    cv_values.append(cv)

# Scale CV to fit on same axis
scaled_cv = [cv/10 for cv in cv_values]  # Divide by 10 to fit scale
bars2 = ax6.bar(x_pos + 0.2, scaled_cv, 0.4, 
                label='CV / 10 (%)', alpha=0.8, color='orange')

ax6.set_xlabel('Site Code', fontsize=12, fontweight='bold')
ax6.set_ylabel('Value', fontsize=12, fontweight='bold')
ax6.set_title('Prediction Error (MAE) vs Visibility Variability (CV)\nfor Sites with >50 Reports', 
              fontsize=14, fontweight='bold')
ax6.set_xticks(x_pos)
ax6.set_xticklabels(high_sample_sites['Site_Code'])
ax6.legend()
ax6.grid(True, alpha=0.3, axis='y')

# ============================================================================
# Panel 7: Recommendations
# ============================================================================
ax7 = fig.add_subplot(gs[5, :])
ax7.axis('off')

ax7.text(0.5, 0.95, '💡 Recommendations for Improvement 💡', 
         ha='center', va='top', fontsize=18, fontweight='bold')

recommendations = [
    "1. Add site-specific features: distance from river mouths, bottom depth, substrate type",
    "2. Add temporal features: days since last storm, recent rainfall, tidal patterns",
    "3. Consider separate models for problematic sites (RKM, NMF, SCR)",
    "4. Feature engineering: wave energy index, swell direction relative to site",
    "5. Collect additional data: turbidity sensors, current measurements, local rainfall",
]

y_start = 0.75
for i, rec in enumerate(recommendations):
    y = y_start - i * 0.13
    
    # Bullet point
    ax7.text(0.05, y, '●', fontsize=16, color='blue')
    
    # Recommendation text
    ax7.text(0.08, y, rec, fontsize=12, va='center')

ax7.set_xlim(0, 1)
ax7.set_ylim(0, 1)

plt.savefig('plots/site_accuracy_summary_infographic.png', dpi=300, bbox_inches='tight',
            facecolor='white')
print("✓ Saved: plots/site_accuracy_summary_infographic.png")

print("\n" + "="*80)
print("Summary infographic created successfully!")
print("="*80)
