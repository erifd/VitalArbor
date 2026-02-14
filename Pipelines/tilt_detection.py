import cv2
import numpy as np
import math
import os
import sam2_segmentation

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

def detect_tree_sweep(binary, tree_center_x, height, width, tilt_angle):
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
        
        section = binary[y_start:y_end, :]
        
        tree_cols = []
        for row in section:
            cols = np.where(row > 0)[0]
            if len(cols) > 0:
                tree_cols.extend(cols)
        
        if len(tree_cols) > 0:
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

# [Rest of the file - validation, detection functions remain the same as before]
def validate_tilt_line(binary, tilt_line_bottom_x, tilt_line_bottom_y, tilt_line_top_x, tilt_line_top_y, trunk_start):
    """
    Validate if the tilt line accurately follows the tree trunk.
    Returns: (is_valid, accuracy_score)
    """
    height, width = binary.shape
    
    line_mask = np.zeros_like(binary)
    cv2.line(line_mask, (tilt_line_bottom_x, tilt_line_bottom_y), 
             (tilt_line_top_x, tilt_line_top_y), 255, 3)
    
    line_points = np.where(line_mask > 0)
    
    if len(line_points[0]) == 0:
        return False, 0.0
    
    trunk_line_points = [(y, x) for y, x in zip(line_points[0], line_points[1]) if y >= trunk_start]
    
    if len(trunk_line_points) == 0:
        return False, 0.0
    
    overlap_count = 0
    for y, x in trunk_line_points:
        if binary[y, x] > 0:
            overlap_count += 1
    
    overlap_percentage = overlap_count / len(trunk_line_points)
    
    sample_points = trunk_line_points[::max(1, len(trunk_line_points)//20)]
    
    neighborhood_overlap = 0
    neighborhood_radius = 10
    
    for y, x in sample_points:
        y_min = max(0, y - neighborhood_radius)
        y_max = min(height, y + neighborhood_radius)
        x_min = max(0, x - neighborhood_radius)
        x_max = min(width, x + neighborhood_radius)
        
        neighborhood = binary[y_min:y_max, x_min:x_max]
        if np.sum(neighborhood > 0) > 0:
            neighborhood_overlap += 1
    
    neighborhood_score = neighborhood_overlap / len(sample_points) if sample_points else 0
    
    accuracy = (overlap_percentage * 0.6) + (neighborhood_score * 0.4)
    
    is_valid = accuracy >= 0.5
    
    return is_valid, accuracy

def detect_tree_tilt(image_path, attempt=1, max_attempts=3):
    """
    Detect tree tilt using line detection on trunk.
    Now returns advanced sweep analysis data.
    
    Returns: (tilt_angle, combined_img, binary, trunk_lines_count, sweep_metrics)
    """
    print(f"\n{'='*60}")
    print(f"TILT DETECTION - Attempt {attempt}/{max_attempts}")
    print(f"{'='*60}")
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"ERROR: Could not read image: {image_path}")
        return None
    
    print(f"Image loaded: {img.shape[1]}x{img.shape[0]} pixels")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    
    height, width = binary.shape
    print(f"Binary image created: {width}x{height}")
    
    # Find trunk region
    print("\n=== Detecting Trunk Region ===")
    
    tree_pixels_per_row = np.sum(binary > 0, axis=1)
    non_zero_rows = np.where(tree_pixels_per_row > 0)[0]
    
    if len(non_zero_rows) == 0:
        print("ERROR: No tree pixels found in image")
        return None
    
    tree_top = non_zero_rows[0]
    tree_bottom = non_zero_rows[-1]
    tree_height = tree_bottom - tree_top
    
    print(f"Tree spans from row {tree_top} to {tree_bottom} (height: {tree_height}px)")
    
    trunk_start = int(tree_top + tree_height * 0.4)
    print(f"Trunk region starts at row {trunk_start}")
    
    # Detect trunk lines
    print("\n=== Detecting Trunk Lines ===")
    
    trunk_region = binary[trunk_start:, :]
    edges = cv2.Canny(trunk_region, 50, 150, apertureSize=3)
    
    min_line_length = int(height * 0.15)
    max_line_gap = int(height * 0.05)
    
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=30,
                            minLineLength=min_line_length, maxLineGap=max_line_gap)
    
    if lines is None:
        print("ERROR: No lines detected in trunk region")
        return None
    
    print(f"Detected {len(lines)} raw lines")
    
    # Filter for near-vertical lines
    print("\n=== Filtering for Trunk Lines ===")
    
    trunk_lines = []
    center_x = width / 2
    bottom_y = height - 1
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        y1 += trunk_start
        y2 += trunk_start
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dy == 0:
            continue
        
        angle = abs(math.degrees(math.atan(dx / dy)))
        
        if angle <= 35:
            length = math.sqrt(dx**2 + dy**2)
            
            if dy != 0:
                slope = dx / dy
                x_at_bottom = x2 + slope * (bottom_y - y2)
            else:
                x_at_bottom = x2
            
            trunk_lines.append((x1, y1, x2, y2, angle, length, x_at_bottom))
    
    if len(trunk_lines) == 0:
        print("ERROR: No valid trunk lines found")
        return None
    
    print(f"Found {len(trunk_lines)} trunk lines")
    
    # Calculate weighted average tilt
    print("\n=== Calculating Tilt Angle ===")
    
    total_weighted_x = 0
    total_weight = 0
    
    for x1, y1, x2, y2, angle, length, x_bottom in trunk_lines:
        weight = length
        total_weighted_x += x_bottom * weight
        total_weight += weight
    
    if total_weight == 0:
        print("ERROR: Total weight is zero")
        return None
    
    weighted_bottom_x = total_weighted_x / total_weight
    
    print(f"Weighted average bottom x-position: {weighted_bottom_x:.1f}")
    print(f"Image center x: {center_x:.1f}")
    
    horizontal_offset = weighted_bottom_x - center_x
    vertical_distance = height - trunk_start
    
    tilt_angle = math.degrees(math.atan(horizontal_offset / vertical_distance))
    
    print(f"\nCalculated tilt angle: {tilt_angle:.2f}° from vertical")
    print(f"Direction: {'RIGHT' if tilt_angle > 0 else 'LEFT'}")
    
    # Find tree center
    print("\n=== Finding Tree Trunk Center ===")
    
    trunk_region = binary[trunk_start:, :]
    tree_pixels_per_row = np.sum(trunk_region > 0, axis=1)
    valid_rows = np.where(tree_pixels_per_row > width * 0.05)[0]
    
    if len(valid_rows) > 0:
        left_edges = []
        right_edges = []
        
        for row_idx in valid_rows:
            row = trunk_region[row_idx, :]
            tree_cols = np.where(row > 0)[0]
            if len(tree_cols) > 0:
                left_edges.append(tree_cols[0])
                right_edges.append(tree_cols[-1])
        
        avg_left = np.mean(left_edges)
        avg_right = np.mean(right_edges)
        tree_center_x = (avg_left + avg_right) / 2
        print(f"Tree trunk center detected at x={tree_center_x:.1f}")
    else:
        tree_center_x = weighted_bottom_x
        print(f"Using weighted bottom x as tree center: {tree_center_x:.1f}")
    
    # Advanced sweep detection
    has_sweep, is_problematic_tilt, sweep_description, center_points, sweep_metrics = detect_tree_sweep(
        binary, tree_center_x, height, width, tilt_angle
    )
    
    # Create visualizations [visualization code continues as before...]
    # [Same visualization code as before - creating lines_img, plain_binary, tilt_img]
    
    lines_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    for x1, y1, x2, y2, _, length, x_bottom in trunk_lines:
        intensity = min(255, int(100 + (length / height) * 155))
        cv2.line(lines_img, (x1, y1), (x2, y2), (0, intensity, 0), 2)
        cv2.line(lines_img, (x2, y2), (int(x_bottom), bottom_y), (0, intensity//2, 0), 1)
        cv2.circle(lines_img, (int(x_bottom), bottom_y), 5, (0, 255, 255), -1)
    
    cv2.line(lines_img, (0, trunk_start), (width, trunk_start), (255, 0, 0), 2)
    cv2.line(lines_img, (int(center_x), trunk_start), (int(center_x), height), (0, 0, 255), 2)
    cv2.circle(lines_img, (int(weighted_bottom_x), bottom_y), 10, (255, 0, 255), -1)
    cv2.line(lines_img, (int(center_x), trunk_start), (int(weighted_bottom_x), bottom_y), (255, 0, 255), 3)
    
    cv2.putText(lines_img, f'Tilt: {tilt_angle:.2f} deg', 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(lines_img, f'{len(trunk_lines)} lines', 
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    plain_binary = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    tilt_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # Visualization based on sweep quality
    sweep_quality = sweep_metrics.get('sweep_quality', 'moderate')
    
    if sweep_quality in ['excellent', 'good'] and not is_problematic_tilt:
        # Green for good sweep
        for i in range(len(center_points) - 1):
            pt1 = (int(center_points[i][0]), int(center_points[i][1]))
            pt2 = (int(center_points[i+1][0]), int(center_points[i+1][1]))
            cv2.line(tilt_img, pt1, pt2, (0, 255, 0), 4)
        
        for cx, cy in center_points:
            cv2.circle(tilt_img, (int(cx), int(cy)), 5, (0, 255, 0), -1)
        
        cv2.putText(tilt_img, 'Good Sweep', 
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        
    elif sweep_quality in ['poor', 'critical'] or is_problematic_tilt:
        # Red for bad sweep
        for i in range(len(center_points) - 1):
            pt1 = (int(center_points[i][0]), int(center_points[i][1]))
            pt2 = (int(center_points[i+1][0]), int(center_points[i+1][1]))
            cv2.line(tilt_img, pt1, pt2, (0, 0, 255), 4)
        
        for cx, cy in center_points:
            cv2.circle(tilt_img, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        
        cv2.putText(tilt_img, 'Bad Sweep', 
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        
    else:
        # Yellow for moderate/neutral
        for i in range(len(center_points) - 1):
            pt1 = (int(center_points[i][0]), int(center_points[i][1]))
            pt2 = (int(center_points[i+1][0]), int(center_points[i+1][1]))
            cv2.line(tilt_img, pt1, pt2, (0, 255, 255), 4)
        
        for cx, cy in center_points:
            cv2.circle(tilt_img, (int(cx), int(cy)), 5, (0, 255, 255), -1)
        
        cv2.putText(tilt_img, 'Moderate Sweep', 
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
    
    # Add metrics to visualization
    cv2.putText(tilt_img, f'Tilt: {tilt_angle:.2f} deg', 
                (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(tilt_img, f'Sharp: {sweep_metrics.get("sharpness_score", 0):.2f}', 
                (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(tilt_img, f'Pattern: {sweep_metrics.get("movement_pattern", "")[:12]}', 
                (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    combined_img = np.hstack([lines_img, plain_binary, tilt_img])
    
    trunk_lines_count = len(trunk_lines)
    
    return tilt_angle, combined_img, binary, trunk_lines_count, sweep_metrics