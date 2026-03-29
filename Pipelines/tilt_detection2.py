import numpy as np
from PIL import Image, ImageDraw
from sklearn.decomposition import PCA
from skimage.morphology import closing, disk, remove_small_holes, remove_small_objects
import math
import os
import cv2


def calculate_curvature_metrics(center_points):
    """
    Calculate detailed curvature metrics for sweep analysis.
    
    Returns dict with:
    - sharpness: How sharp the curve is (rate of change of direction)
    - gradient_smoothness: How smooth/gradual the curve is
    - direction_vector: Overall movement direction
    """
    if len(center_points) < 3:
        return None
    
    x_coords = np.array([p[0] for p in center_points])
    y_coords = np.array([p[1] for p in center_points])
    
    # Calculate first and second derivatives (approximations)
    # First derivative = slope = direction
    dx_dy = np.gradient(x_coords, y_coords)
    
    # Second derivative = curvature = rate of change of slope
    d2x_dy2 = np.gradient(dx_dy, y_coords)
    
    # Curvature sharpness - higher values mean sharper curves
    curvature_values = np.abs(d2x_dy2) / (1 + dx_dy**2)**1.5
    
    # Calculate metrics
    max_curvature = np.max(curvature_values)
    avg_curvature = np.mean(curvature_values)
    curvature_variance = np.var(curvature_values)
    
    # Sharpness score: 0 = gradual, 1 = very sharp
    # Sharp curves are dangerous - they indicate stress concentrations
    sharpness_score = min(1.0, max_curvature * 1000)  # Scaled for visibility
    
    # Gradient smoothness: 0 = erratic changes, 1 = smooth gradual curve
    # Smooth is better - indicates controlled growth response
    if curvature_variance > 0:
        smoothness_score = 1.0 / (1.0 + curvature_variance * 100)
    else:
        smoothness_score = 1.0
    
    return {
        'curvature_values': curvature_values.tolist(),
        'max_curvature': float(max_curvature),
        'avg_curvature': float(avg_curvature),
        'sharpness_score': float(sharpness_score),
        'smoothness_score': float(smoothness_score),
        'first_derivative': dx_dy.tolist(),
        'second_derivative': d2x_dy2.tolist()
    }


def analyze_progressive_movement(center_points):
    """
    Analyze if tree is progressively leaning MORE (very bad) or correcting (good).
    
    Divides tree into bottom, middle, top thirds and analyzes movement pattern.
    
    Returns:
    - movement_pattern: 'progressive_out', 'stable_lean', 'correcting_inward', 'straight'
    - risk_level: 'critical', 'high', 'moderate', 'low'
    - pattern_score: -1.0 (worst) to +1.0 (best)
    """
    if len(center_points) < 6:
        return {
            'movement_pattern': 'insufficient_data',
            'risk_level': 'unknown',
            'pattern_score': 0.0
        }
    
    x_coords = np.array([p[0] for p in center_points])
    
    # Divide into thirds: bottom (roots), middle, top (crown)
    n = len(center_points)
    third = n // 3
    
    bottom_x = x_coords[:third]
    middle_x = x_coords[third:2*third]
    top_x = x_coords[2*third:]
    
    # Calculate average position for each third
    bottom_avg = np.mean(bottom_x)
    middle_avg = np.mean(middle_x)
    top_avg = np.mean(top_x)
    
    # Calculate movement trends
    # Positive = moving right (away from vertical if leaning right)
    # Negative = moving left (toward vertical if leaning right)
    bottom_to_middle = middle_avg - bottom_avg
    middle_to_top = top_avg - middle_avg
    
    # Determine overall lean direction from bottom position
    initial_lean = bottom_avg - x_coords[0]  # relative to base
    
    # Pattern analysis
    # Case 1: Progressive outward lean (VERY BAD)
    # Tree leans out at bottom, continues leaning MORE outward → active failure
    if abs(bottom_to_middle) > 5 and abs(middle_to_top) > 5:
        # Both segments moving same direction
        if np.sign(bottom_to_middle) == np.sign(middle_to_top):
            # Check if moving away from vertical
            if np.sign(bottom_to_middle) == np.sign(initial_lean):
                movement_pattern = 'progressive_out'
                risk_level = 'critical'
                pattern_score = -1.0
            else:
                # Moving back toward vertical throughout
                movement_pattern = 'correcting_inward'
                risk_level = 'low'
                pattern_score = 0.8
        else:
            # Directions change - some correction happening
            movement_pattern = 'correcting_inward'
            risk_level = 'moderate'
            pattern_score = 0.5
    
    # Case 2: Lean out then stable/straight up (MODERATE)
    # Tree leans at bottom but grows straight up from there
    elif abs(bottom_to_middle) > 5 and abs(middle_to_top) < 5:
        if np.sign(bottom_to_middle) == np.sign(initial_lean):
            movement_pattern = 'stable_lean'
            risk_level = 'moderate'
            pattern_score = 0.0
        else:
            movement_pattern = 'correcting_inward'
            risk_level = 'low'
            pattern_score = 0.6
    
    # Case 3: Correcting lean (GOOD)
    # Tree leans at bottom, curves back toward vertical
    elif abs(bottom_to_middle) > 5 and abs(middle_to_top) > 5:
        # Opposite directions = correction
        if np.sign(bottom_to_middle) != np.sign(middle_to_top):
            movement_pattern = 'correcting_inward'
            risk_level = 'low'
            pattern_score = 0.9
        else:
            movement_pattern = 'stable_lean'
            risk_level = 'moderate'
            pattern_score = 0.2
    
    # Case 4: Minimal movement (straight tree)
    else:
        movement_pattern = 'straight'
        risk_level = 'low'
        pattern_score = 1.0
    
    return {
        'movement_pattern': movement_pattern,
        'risk_level': risk_level,
        'pattern_score': float(pattern_score),
        'bottom_to_middle': float(bottom_to_middle),
        'middle_to_top': float(middle_to_top),
        'bottom_avg': float(bottom_avg),
        'middle_avg': float(middle_avg),
        'top_avg': float(top_avg)
    }


def detect_tree_sweep(binary_mask, tree_center_x, height, width, tilt_angle):
    """
    Advanced sweep detection with curvature analysis and progressive lean detection.
    
    Returns: (has_sweep, is_problematic_tilt, sweep_description, curvature_points, sweep_metrics)
    """
    print("\n=== Advanced Sweep Analysis ===")
    
    # Divide tree into sections (increased to 15 for better resolution)
    num_sections = 15
    section_height = height // num_sections
    
    center_points = []
    
    # Find center of each section
    for i in range(num_sections):
        y_start = i * section_height
        y_end = min((i + 1) * section_height, height)
        
        section = binary_mask[y_start:y_end, :]
        
        # Find tree pixels in this section
        tree_cols = []
        for row in section:
            cols = np.where(row > 0)[0]
            if len(cols) > 0:
                tree_cols.extend(cols)
        
        if len(tree_cols) > 0:
            # Calculate center as average of all tree pixels
            section_center = np.mean(tree_cols)
            center_y = (y_start + y_end) / 2
            center_points.append((section_center, center_y))
    
    if len(center_points) < 6:
        print("Not enough data points for advanced sweep analysis")
        return False, False, "Insufficient data", [], {
            'has_data': False,
            'sweep_quality': 'insufficient_data'
        }
    
    # Extract coordinates
    x_coords = [p[0] for p in center_points]
    y_coords = [p[1] for p in center_points]
    
    # === CURVATURE ANALYSIS ===
    curvature_metrics = calculate_curvature_metrics(center_points)
    
    # === PROGRESSIVE MOVEMENT ANALYSIS ===
    movement_analysis = analyze_progressive_movement(center_points)
    
    # === TRADITIONAL SWEEP METRICS (from original) ===
    # Split into thirds for comparison
    third = len(center_points) // 3
    
    top_x = x_coords[:third]
    mid_x = x_coords[third:2*third]
    bot_x = x_coords[2*third:]
    top_y = y_coords[:third]
    mid_y = y_coords[third:2*third]
    bot_y = y_coords[2*third:]
    
    def calculate_slope(x_vals, y_vals):
        if len(x_vals) >= 2 and (y_vals[-1] - y_vals[0]) != 0:
            return (x_vals[-1] - x_vals[0]) / (y_vals[-1] - y_vals[0])
        return 0
    
    top_slope = calculate_slope(top_x, top_y)
    mid_slope = calculate_slope(mid_x, mid_y)
    bot_slope = calculate_slope(bot_x, bot_y)
    
    # Overall linear fit
    coeffs = np.polyfit(y_coords, x_coords, 1)
    fitted_x = np.polyval(coeffs, y_coords)
    deviations = [abs(x - fx) for x, fx in zip(x_coords, fitted_x)]
    max_deviation = max(deviations)
    avg_deviation = np.mean(deviations)
    overall_slope = coeffs[0]
    
    # Quadratic fit for curvature
    quadratic_coeffs = np.polyfit(y_coords, x_coords, 2)
    curvature_coefficient = abs(quadratic_coeffs[0])
    
    overall_tilt_angle = abs(math.degrees(math.atan(overall_slope)))
    
    # Direction reversal check
    has_direction_reversal = (top_slope * bot_slope < 0) and (abs(top_slope) > 0.05 or abs(bot_slope) > 0.05)
    
    # Curve recovery calculation
    top_center = x_coords[0]
    mid_center = x_coords[len(x_coords)//2]
    bot_center = x_coords[-1]
    
    mid_deviation = abs(mid_center - top_center)
    bot_deviation = abs(bot_center - top_center)
    
    if mid_deviation > 0:
        curve_recovery = (mid_deviation - bot_deviation) / mid_deviation
        curve_recovery = max(-1.0, min(1.0, curve_recovery))
    else:
        curve_recovery = 0.0
    
    # Consistency score
    if avg_deviation > 0:
        consistency_score = 1.0 - (avg_deviation / (width * 0.1))
        consistency_score = max(0.0, min(1.0, consistency_score))
    else:
        consistency_score = 1.0
    
    # === INTEGRATED SWEEP QUALITY DETERMINATION ===
    
    movement_pattern = movement_analysis['movement_pattern']
    movement_risk = movement_analysis['risk_level']
    pattern_score = movement_analysis['pattern_score']
    
    sharpness = curvature_metrics['sharpness_score']
    smoothness = curvature_metrics['smoothness_score']
    
    # Determine sweep type with new research-based criteria
    print(f"\n=== Pattern Analysis ===")
    print(f"Movement Pattern: {movement_pattern}")
    print(f"Movement Risk: {movement_risk}")
    print(f"Pattern Score: {pattern_score:.3f}")
    print(f"Curve Sharpness: {sharpness:.3f} (0=gradual, 1=sharp)")
    print(f"Curve Smoothness: {smoothness:.3f} (0=erratic, 1=smooth)")
    print(f"Curve Recovery: {curve_recovery:.3f}")
    print(f"Overall Tilt: {overall_tilt_angle:.2f}°")
    
    # Critical case: Progressive outward lean
    if movement_pattern == 'progressive_out':
        sweep_type = 'progressive_failure'
        sweep_quality = 'critical'
        has_sweep = False
        is_problematic_tilt = True
        description = "⚠️ CRITICAL: Progressive outward lean detected - active root failure likely"
    
    # Sharp curve case - research shows these create stress concentrations
    elif sharpness > 0.6 and smoothness < 0.4:
        sweep_type = 'sharp_curve_stress'
        sweep_quality = 'poor'
        has_sweep = True
        is_problematic_tilt = True
        description = "⚠️ HIGH RISK: Sharp curve creates stress concentration points"
    
    # Good case: Gradual correcting curve
    elif movement_pattern == 'correcting_inward' and sharpness < 0.4 and smoothness > 0.6:
        sweep_type = 'gradual_correction'
        sweep_quality = 'excellent'
        has_sweep = True
        is_problematic_tilt = False
        description = "✓ EXCELLENT: Gradual correcting curve - reaction wood compensation working well"
    
    # Moderate case: Lean then straight growth
    elif movement_pattern == 'stable_lean' and overall_tilt_angle < 15:
        sweep_type = 'stable_lean'
        sweep_quality = 'moderate'
        has_sweep = True
        is_problematic_tilt = False
        description = "MODERATE: Tree leans but grows straight - some compensation evident"
    
    # Good case: Natural sweep with direction reversal
    elif has_direction_reversal and curve_recovery > 0.3 and sharpness < 0.5:
        sweep_type = 'natural_recovery'
        sweep_quality = 'good'
        has_sweep = True
        is_problematic_tilt = False
        description = "✓ GOOD: Natural sweep with gradual recovery - healthy growth pattern"
    
    # Poor case: Consistent tilt
    elif consistency_score > 0.75 and overall_tilt_angle > 10:
        sweep_type = 'straight_tilt'
        sweep_quality = 'poor'
        has_sweep = False
        is_problematic_tilt = True
        description = f"⚠️ POOR: Straight consistent tilt {overall_tilt_angle:.1f}° - no compensation"
    
    # Severe case
    elif overall_tilt_angle > 20:
        sweep_type = 'severe_tilt'
        sweep_quality = 'critical'
        has_sweep = False
        is_problematic_tilt = True
        description = f"⚠️ CRITICAL: Severe tilt {overall_tilt_angle:.1f}° - high failure risk"
    
    # Good case: minimal tilt
    elif overall_tilt_angle < 5:
        sweep_type = 'minimal_tilt'
        sweep_quality = 'excellent'
        has_sweep = False
        is_problematic_tilt = False
        description = f"✓ EXCELLENT: Minimal tilt {overall_tilt_angle:.1f}° - tree nearly vertical"
    
    # Default: neutral
    else:
        sweep_type = 'neutral'
        sweep_quality = 'moderate'
        has_sweep = True if max_deviation > width * 0.05 else False
        is_problematic_tilt = False
        description = "MODERATE: Mixed characteristics - standard assessment applies"
    
    # Create comprehensive sweep metrics
    sweep_metrics = {
        'has_data': True,
        'sweep_type': sweep_type,
        'sweep_quality': sweep_quality,
        
        # Curvature metrics (new)
        'sharpness_score': round(sharpness, 3),
        'smoothness_score': round(smoothness, 3),
        'max_curvature': round(curvature_metrics['max_curvature'], 6),
        'avg_curvature': round(curvature_metrics['avg_curvature'], 6),
        
        # Progressive movement metrics (new)
        'movement_pattern': movement_pattern,
        'movement_risk_level': movement_risk,
        'pattern_score': round(pattern_score, 3),
        'bottom_to_middle_movement': round(movement_analysis['bottom_to_middle'], 2),
        'middle_to_top_movement': round(movement_analysis['middle_to_top'], 2),
        
        # Traditional metrics
        'curve_recovery': round(curve_recovery, 3),
        'consistency_score': round(consistency_score, 3),
        'max_deviation': round(max_deviation, 2),
        'avg_deviation': round(avg_deviation, 2),
        'overall_tilt_angle': round(overall_tilt_angle, 2),
        'curvature_coefficient': round(curvature_coefficient, 6),
        
        # Slope data
        'top_slope': round(top_slope, 4),
        'mid_slope': round(mid_slope, 4),
        'bot_slope': round(bot_slope, 4),
        'has_direction_reversal': has_direction_reversal,
        
        # Metadata
        'num_sections': len(center_points)
    }
    
    print(f"\nSweep Quality: {sweep_quality.upper()}")
    print(f"Sweep Type: {sweep_type}")
    print(description)
    
    return has_sweep, is_problematic_tilt, description, center_points, sweep_metrics


def analyze_tree(segmented_image_path):
    """
    Analyze tree trunk tilt angle from vertical using PCA.
    Returns sweep structure for risk_score.py to analyze.
    
    Returns:
    --------
    tuple: (tilt_angle, result_img, binary_mask, trunk_lines_count, sweep_metrics)
    """

    # Setup paths
    base_name = os.path.splitext(os.path.basename(segmented_image_path))[0]
    
    input_dir = os.path.dirname(segmented_image_path)
    if "VitalArbor" in input_dir and "Pipelines" in input_dir:
        vital_arbor_root = input_dir.split("VitalArbor")[0] + "VitalArbor"
        output_dir = os.path.join(vital_arbor_root, "Segmented photos")
    else:
        output_dir = input_dir
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load image
    img = Image.open(segmented_image_path).convert("RGB")
    img_np = np.array(img)
    height, width = img_np.shape[:2]

    # Create binary mask
    gray = np.dot(img_np[..., :3], [0.2989, 0.5870, 0.1140])
    binary_mask = gray > 0
    
    # Clean mask
    mask_clean = remove_small_holes(binary_mask, area_threshold=200)
    mask_clean = remove_small_objects(mask_clean, min_size=200)
    mask_clean = closing(mask_clean, disk(20))

    # Get tree coordinates
    ys, xs = np.where(mask_clean == 1)
    
    if len(ys) == 0:
        raise ValueError("No tree pixels found in mask")
    
    tree_coords = np.column_stack((xs, ys))

    # PCA analysis
    pca = PCA(n_components=2)
    pca.fit(tree_coords)
    pc1 = pca.components_[0]
    pc1 = pc1 / np.linalg.norm(pc1)

    # Calculate tilt angle
    vertical = np.array([0, -1])
    dot = np.dot(pc1, vertical)
    angle_rad = math.acos(np.clip(dot, -1.0, 1.0))
    angle_deg = math.degrees(angle_rad)
    tilt_angle = 180 - angle_deg
    
    print(f"\n=== PCA Tilt Detection ===")
    print(f"PCA tilt angle: {tilt_angle:.2f}° from vertical")

    # Find tree center
    centroid = tree_coords.mean(axis=0)
    tree_center_x = centroid[0]
    
    # Detect sweep structure
    has_sweep, is_problematic_tilt, sweep_description, center_points, sweep_metrics = detect_tree_sweep(
        mask_clean, tree_center_x, height, width, tilt_angle
    )

    # Create visualizations
    vis_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # Sweep visualization - just show the curve structure
    sweep_vis = vis_bgr.copy()
    
    # Color based on problematic or not
    if is_problematic_tilt:
        color = (0, 0, 255)  # Red
        label = 'Problematic Tilt'
    elif has_sweep:
        color = (0, 255, 0)  # Green
        label = 'Natural Sweep'
    else:
        color = (0, 255, 255)  # Yellow
        label = 'Minor Tilt'
    
    # Draw the curve
    if len(center_points) > 1:
        for i in range(len(center_points) - 1):
            pt1 = (int(center_points[i][0]), int(center_points[i][1]))
            pt2 = (int(center_points[i+1][0]), int(center_points[i+1][1]))
            cv2.line(sweep_vis, pt1, pt2, color, 4)
        
        for cx, cy in center_points:
            cv2.circle(sweep_vis, (int(cx), int(cy)), 5, color, -1)
    
    cv2.putText(sweep_vis, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
    cv2.putText(sweep_vis, f'Tilt: {tilt_angle:.2f} deg', 
                (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # PCA axis visualization
    pca_vis = vis_bgr.copy()
    scale = max(height, width)
    p1 = (int(centroid[0] - pc1[0] * scale), int(centroid[1] - pc1[1] * scale))
    p2 = (int(centroid[0] + pc1[0] * scale), int(centroid[1] + pc1[1] * scale))
    
    cv2.line(pca_vis, p1, p2, (255, 0, 0), 3)
    cv2.circle(pca_vis, (int(centroid[0]), int(centroid[1])), 8, (255, 0, 0), -1)
    
    # Binary visualization
    binary_vis = cv2.cvtColor((mask_clean * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    
    # Combine
    combined_vis = np.hstack([pca_vis, binary_vis, sweep_vis])
    
    # Save
    cv2.imwrite(os.path.join(output_dir, f"{base_name}_pca_combined.png"), combined_vis)
    
    print(f"\nSweep detection complete: {len(center_points)} points")
    print(f"Visualization saved to: {output_dir}")
    
    # Return format: (tilt, result_img, binary, trunk_lines_count, sweep_metrics)
    trunk_lines_count = len(center_points)
    
    return tilt_angle, combined_vis, mask_clean, trunk_lines_count, sweep_metrics


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = analyze_tree(sys.argv[1])
        if result:
            tilt, img, binary, count, metrics = result
            print(f"\nFinal tilt angle: {tilt:.2f}°")
            print(f"Center points: {count}")
            if metrics:
                print(f"Sweep metrics: {metrics}")