"""
VitalArbor Statistics Viewer
=============================
Displays comprehensive box plot statistics for Offset Model and PCA Model
tilt angle error analysis across different tree categories.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ============================================================================
# DATA
# ============================================================================

# Straight Trunk
straight_offset = [0.26, -2.16, -5.52, 1.98, -7.79, -0.24, 2.16, 0.58, -0.14, 
                   -6.19, -4.73, -10.84, 6.13, -4.2, -0.67, -3.71, -6.09, -0.45, -7.39]
straight_pca = [1.69, 0.8, 4.98, 4.98, -18.07, 2.72, 1.44, -1, -2.93, 
                -7, -7.57, 0.35, -11.7, -8.53, 0.82, -2.54, -2.98, 4.11, -6.67]

# Crooked Trunk
crooked_offset = [-7.56, -5.29, 0.3, -4.73, -0.73, 0.44, 5.5, -8.85, 2.16]
crooked_pca = [-8.03, 6.26, 2.15, -7.57, -4.29, -0.69, 10.62, -12.09, -3.26]

# Large Tilt
large_offset = [-7.56, -7.79, -5.29, -0.14, -3.52, -4.73, -10.84, 6.13, 0.44, 
                -3.71, 5.5, -8.85, -6.09, -7.39, 2.16]
large_pca = [-8.03, -18.07, 6.26, -2.93, -7.33, -7.57, 0.35, -11.7, -0.69, 
             -2.54, 10.62, -12.09, -2.98, -6.67, -3.26]

# Small Tilt
small_offset = [0.26, -2.16, -5.52, 1.98, -0.24, 2.16, 0.58, 0.3, -6.19, 
                -0.73, -4.2, -0.67, -0.45]
small_pca = [1.69, 0.8, -1.31, 4.98, 2.72, 1.44, -1, 2.15, -7, -4.29, 
             -8.53, 0.82, 4.11]

# Deciduous
deciduous_offset = [0.26, -2.16, -5.52, 1.98, -5.29, -0.24, 2.16, -0.14, 0.3, 
                    -6.19, -3.52, -4.73, -10.84, 0.44, -4.2, -0.67, -3.71, -0.45]
deciduous_pca = [1.69, 0.8, -1.31, 4.98, 6.26, 2.72, 1.44, -2.93, 2.15, -7, 
                 -7.33, -7.57, 0.35, -0.69, -8.53, 0.82, -2.54, 4.11]

# Evergreen
evergreen_offset = [-7.56, -7.79, 6.13, -0.73, 5.5, -8.85, -6.09, -7.39, 2.16]
evergreen_pca = [-8.03, -18.07, -11.7, -4.29, 10.62, -12.09, -2.98, -6.67, -3.26]

# All trees combined
all_offset = [0.26, -2.16, -7.56, -5.52, 1.98, -7.79, -5.29, -0.24, 2.16, 0.58,
              -0.14, 0.3, -6.19, -3.52, -4.73, -10.84, 6.13, -0.73, 0.44, -4.2,
              -0.67, -3.71, 5.5, -8.85, -6.09, -0.45, -7.39, 2.16]
all_pca = [1.69, 0.8, -8.03, -1.31, 4.98, -18.07, 6.26, 2.72, 1.44, -1,
           -2.93, 2.15, -7, -7.33, -7.57, 0.35, -11.7, -4.29, -0.69, -8.53,
           0.82, -2.54, 10.62, -12.09, -2.98, 4.11, -6.67, -3.26]

# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def create_comparison_boxplot(data1, data2, title, subtitle, color1, color2, 
                               theme_bg, theme_header, theme_text, theme_footer_bg, 
                               theme_footer_edge, theme_grid, theme_bg_light):
    """Create comparison box plot with two error types side by side"""
    
    fig = plt.figure(figsize=(4, 2.5), dpi=150)
    fig.patch.set_facecolor(theme_bg)
    
    card_ax = fig.add_axes([0, 0, 1, 1])
    card_ax.set_xlim(0, 1)
    card_ax.set_ylim(0, 1)
    card_ax.axis('off')
    
    card = FancyBboxPatch((0.015, 0.015), 0.97, 0.97,
                          boxstyle="round,pad=0.01",
                          facecolor='white', edgecolor='none',
                          alpha=0.95, transform=card_ax.transAxes)
    card_ax.add_patch(card)
    
    header = FancyBboxPatch((0.015, 0.865), 0.97, 0.12,
                           boxstyle="round,pad=0.008",
                           facecolor=theme_header, edgecolor='none',
                           transform=card_ax.transAxes)
    card_ax.add_patch(header)
    
    card_ax.text(0.5, 0.94, title, 
                ha='center', va='center', fontsize=7.5, fontweight='bold',
                color='white', family='DejaVu Sans Mono')
    card_ax.text(0.5, 0.895, subtitle,
                ha='center', va='center', fontsize=5,
                color='#f0f0f0', family='DejaVu Sans Mono')
    
    ax = fig.add_axes([0.18, 0.20, 0.74, 0.60])
    
    positions = [1, 2]
    bp = ax.boxplot([data1, data2], 
                     positions=positions,
                     widths=0.6,
                     patch_artist=True,
                     showfliers=False,
                     medianprops=dict(color=theme_header, linewidth=2),
                     boxprops=dict(facecolor=theme_bg_light, edgecolor=theme_header, 
                                   linewidth=1.5, alpha=0.7),
                     whiskerprops=dict(color=theme_header, linewidth=1.5),
                     capprops=dict(color=theme_header, linewidth=1.5))
    
    for i, (data, pos, color) in enumerate(zip([data1, data2], positions, 
                                                [color1, color2])):
        x_position = pos - 0.45
        ax.scatter([x_position] * len(data), data, c=color, s=30, alpha=0.7, 
                  edgecolors=color, linewidths=1, zorder=3)
    
    ax.set_ylabel('ERROR VALUE', fontsize=6.5, fontweight='bold',
                 color=theme_text, family='DejaVu Sans Mono', labelpad=3)
    ax.set_xlabel('ERROR TYPE', fontsize=6.5, fontweight='bold',
                 color=theme_text, family='DejaVu Sans Mono', labelpad=-8)
    
    ax.set_xticks(positions)
    ax.set_xticklabels(['OFFSET\nMODEL', 'PCA\nMODEL'], 
                       fontsize=5.5, fontweight='bold', family='DejaVu Sans Mono')
    
    ax.tick_params(axis='both', labelsize=5.5, colors=theme_text, 
                  width=0.8, length=3, pad=2)
    
    ax.grid(True, alpha=0.25, color=theme_grid, linewidth=0.6, 
           zorder=1, linestyle='-', axis='y')
    ax.set_axisbelow(True)
    
    ax.set_facecolor(theme_bg_light)
    for spine in ax.spines.values():
        spine.set_edgecolor(theme_header)
        spine.set_linewidth(1)
        spine.set_alpha(0.6)
    
    card_ax.text(0.30, 0.155, '●', ha='center', va='center', 
                fontsize=7, color=color1, fontweight='bold')
    card_ax.text(0.78, 0.155, '●', ha='center', va='center',
                fontsize=7, color=color2, fontweight='bold')
    
    offset_median = np.median(data1)
    offset_q1 = np.percentile(data1, 25)
    offset_q3 = np.percentile(data1, 75)
    pca_median = np.median(data2)
    pca_q1 = np.percentile(data2, 25)
    pca_q3 = np.percentile(data2, 75)
    
    footer = FancyBboxPatch((0.015, 0.015), 0.97, 0.055,
                           boxstyle="round,pad=0.008",
                           facecolor=theme_footer_bg, edgecolor=theme_footer_edge, 
                           linewidth=0.8,
                           transform=card_ax.transAxes)
    card_ax.add_patch(footer)
    
    card_ax.text(0.04, 0.042, f'OFFSET: MED={offset_median:.2f}, IQR={offset_q3-offset_q1:.2f}',
                ha='left', va='center', fontsize=4.5, color=theme_text, 
                family='DejaVu Sans Mono', fontweight='bold')
    card_ax.text(0.96, 0.042, f'PCA: MED={pca_median:.2f}, IQR={pca_q3-pca_q1:.2f}',
                ha='right', va='center', fontsize=4.5, color=theme_text, 
                family='DejaVu Sans Mono', fontweight='bold')
    
    return fig

# ============================================================================
# GENERATE ALL PLOTS
# ============================================================================

def main():
    """Generate and display all box plots"""
    
    print("=" * 70)
    print("VitalArbor Statistics Viewer")
    print("=" * 70)
    print("\nGenerating box plots for tilt angle error analysis...")
    print("Categories: Straight/Crooked, Large/Small, Deciduous/Evergreen, General")
    print("\nClose each plot window to view the next plot.\n")
    
    plots = []
    
    # Straight vs Crooked (Green Theme)
    print("Generating Straight vs Crooked Trunk plots (Green Theme)...")
    plots.append(("Straight Trunk Comparison", create_comparison_boxplot(
        straight_offset, straight_pca,
        'STRAIGHT TRUNK ERROR COMPARISON',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#9333ea', '#2563eb',
        '#2d5a27', '#3a7a30', '#1e3a1c', '#e8f5e8', '#a8d5a5', '#5a8a52', '#f8fdf8'
    )))
    
    plots.append(("Crooked Trunk Comparison", create_comparison_boxplot(
        crooked_offset, crooked_pca,
        'CROOKED TRUNK ERROR COMPARISON',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#9333ea', '#2563eb',
        '#2d5a27', '#3a7a30', '#1e3a1c', '#e8f5e8', '#a8d5a5', '#5a8a52', '#f8fdf8'
    )))
    
    # Large vs Small (Brown Theme)
    print("Generating Large vs Small Tilt plots (Brown Theme)...")
    plots.append(("Large Tilt Comparison", create_comparison_boxplot(
        large_offset, large_pca,
        'LARGE TILT ERROR COMPARISON',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#2d7a2d', '#ff4500',
        '#6B4423', '#8B4513', '#3d2817', '#f5e6d3', '#d4a373', '#a67c52', '#fdf8f3'
    )))
    
    plots.append(("Small Tilt Comparison", create_comparison_boxplot(
        small_offset, small_pca,
        'SMALL TILT ERROR COMPARISON',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#2d7a2d', '#ff4500',
        '#6B4423', '#8B4513', '#3d2817', '#f5e6d3', '#d4a373', '#a67c52', '#fdf8f3'
    )))
    
    # Deciduous vs Evergreen (Orange Theme)
    print("Generating Deciduous vs Evergreen plots (Orange Theme)...")
    plots.append(("Deciduous Comparison", create_comparison_boxplot(
        deciduous_offset, deciduous_pca,
        'DECIDUOUS ERROR COMPARISON',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#9b3542', '#373f6e',
        '#D2691E', '#FF8C00', '#6B3410', '#FFEFD5', '#F4A460', '#CD853F', '#FFF8F0'
    )))
    
    plots.append(("Evergreen Comparison", create_comparison_boxplot(
        evergreen_offset, evergreen_pca,
        'EVERGREEN ERROR COMPARISON',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#9b3542', '#373f6e',
        '#D2691E', '#FF8C00', '#6B3410', '#FFEFD5', '#F4A460', '#CD853F', '#FFF8F0'
    )))
    
    # General - All Trees (Teal Theme)
    print("Generating General All Trees plot (Teal Theme)...")
    plots.append(("General - All Trees", create_comparison_boxplot(
        all_offset, all_pca,
        'GENERAL ERROR COMPARISON - ALL TREES',
        'BOX & WHISKER PLOT WITH DATA POINTS',
        '#ff4500', '#373f6e',
        '#006666', '#008080', '#004d4d', '#E0F2F1', '#80CBC4', '#4d9999', '#F1F8F8'
    )))
    
    print(f"\n✓ Generated {len(plots)} plots successfully!\n")
    
    # Display all plots
    print("=" * 70)
    print("Displaying plots... (close each window to see the next)")
    print("=" * 70)
    
    for name, fig in plots:
        print(f"\nShowing: {name}")
        plt.show()
    
    print("\n" + "=" * 70)
    print("All plots displayed!")
    print("=" * 70)
    print("\nStatistics Summary:")
    print(f"  Total Trees Analyzed: {len(all_offset)}")
    print(f"  Offset Model - Median Error: {np.median(all_offset):.2f}°")
    print(f"  PCA Model - Median Error: {np.median(all_pca):.2f}°")
    print("\nTree Categories:")
    print(f"  - Straight Trunk: {len(straight_offset)} trees")
    print(f"  - Crooked Trunk: {len(crooked_offset)} trees")
    print(f"  - Large Tilt: {len(large_offset)} trees")
    print(f"  - Small Tilt: {len(small_offset)} trees")
    print(f"  - Deciduous: {len(deciduous_offset)} trees")
    print(f"  - Evergreen: {len(evergreen_offset)} trees")
    print("=" * 70)

if __name__ == "__main__":
    main()
