import cv2
import numpy as np
import math
import os
import sam2_segmentation

def detect_tree_sweep(binary, tree_center_x, height, width):
    """
    Detect if the tree has a natural sweep (curves back toward vertical).
    Returns: (has_sweep, is_problematic_tilt, sweep_description, curvature_points)
    """
    print("\n=== Checking for Tree Sweep ===")
    
    # Divide the tree into horizontal sections (top to bottom)
    num_sections = 10
    section_height = height // num_sections
    
    center_points = []
    
    # For each section, find the horizontal center of the tree
    for i in range(num_sections):
        y_start = i * section_height
        y_end = min((i + 1) * section_height, height)
        
        section = binary[y_start:y_end, :]
        
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
    
    if len(center_points) < 5:
        print("Not enough data points to detect sweep")
        return False, False, "Insufficient data", []
    
    # Analyze the trend of center points from top to bottom
    x_coords = [p[0] for p in center_points]
    y_coords = [p[1] for p in center_points]
    
    # Split into upper and lower halves
    mid_idx = len(center_points) // 2
    
    upper_x = x_coords[:mid_idx]
    upper_y = y_coords[:mid_idx]
    lower_x = x_coords[mid_idx:]
    lower_y = y_coords[mid_idx:]
    
    # Calculate slopes for upper and lower sections
    # Positive slope = leaning right, negative = leaning left
    if len(upper_x) >= 2:
        upper_slope = (upper_x[-1] - upper_x[0]) / (upper_y[-1] - upper_y[0]) if (upper_y[-1] - upper_y[0]) != 0 else 0
    else:
        upper_slope = 0
    
    if len(lower_x) >= 2:
        lower_slope = (lower_x[-1] - lower_x[0]) / (lower_y[-1] - lower_y[0]) if (lower_y[-1] - lower_y[0]) != 0 else 0
    else:
        lower_slope = 0
    
    # Calculate the change in direction
    slope_difference = abs(upper_slope - lower_slope)
    
    # Detect sweep: if upper and lower sections lean in opposite directions
    # or if there's a significant change in slope direction
    has_opposite_lean = (upper_slope * lower_slope < 0) and (abs(upper_slope) > 0.1 or abs(lower_slope) > 0.1)
    has_significant_curve = slope_difference > 0.3
    
    # Calculate overall deviation from straight line
    # Fit a line through all center points
    if len(center_points) >= 3:
        coeffs = np.polyfit(y_coords, x_coords, 1)
        fitted_x = np.polyval(coeffs, y_coords)
        deviations = [abs(x - fx) for x, fx in zip(x_coords, fitted_x)]
        max_deviation = max(deviations)
        avg_deviation = np.mean(deviations)
        overall_slope = coeffs[0]
    else:
        max_deviation = 0
        avg_deviation = 0
        overall_slope = 0
    
    # Calculate overall tilt angle from the fitted line
    overall_tilt_angle = abs(math.degrees(math.atan(overall_slope)))
    
    # Determine if there's a sweep
    has_sweep = has_opposite_lean or has_significant_curve or (max_deviation > width * 0.05)
    
    # Determine if this is a problematic whole-trunk tilt
    # Problematic if: entire trunk is tilted consistently without curve-back AND tilt > 7 degrees
    is_whole_trunk_tilt = not has_opposite_lean and not has_significant_curve and overall_tilt_angle > 7
    is_problematic_tilt = is_whole_trunk_tilt
    
    print(f"Upper section slope: {upper_slope:.4f}")
    print(f"Lower section slope: {lower_slope:.4f}")
    print(f"Slope difference: {slope_difference:.4f}")
    print(f"Overall tilt angle: {overall_tilt_angle:.2f}°")
    print(f"Max deviation from straight: {max_deviation:.1f}px ({max_deviation/width*100:.1f}% of width)")
    print(f"Average deviation: {avg_deviation:.1f}px")
    
    # Generate description
    if has_sweep and not is_problematic_tilt:
        if has_opposite_lean:
            if upper_slope > 0 and lower_slope < 0:
                description = "NATURAL SWEEP: Tree leans right at top, curves back left - SAFE"
            elif upper_slope < 0 and lower_slope > 0:
                description = "NATURAL SWEEP: Tree leans left at top, curves back right - SAFE"
            else:
                description = "NATURAL SWEEP: Tree shows healthy curved growth - SAFE"
        elif has_significant_curve:
            description = f"NATURAL SWEEP: Significant curvature (recovers to vertical) - SAFE"
        else:
            description = f"NATURAL SWEEP: Tree deviates but curves back - SAFE"
    elif is_problematic_tilt:
        description = f" PROBLEMATIC TILT: Entire trunk tilted {overall_tilt_angle:.1f}° (>7°) - RISK"
    elif overall_tilt_angle <= 7:
        description = f"MINOR TILT: Tilt {overall_tilt_angle:.1f}° is within safe range (<7°) - SAFE"
    else:
        description = "No significant sweep or tilt detected - SAFE"
    
    print(description)
    
    return has_sweep, is_problematic_tilt, description, center_points

def validate_tilt_line(binary, tilt_line_bottom_x, tilt_line_bottom_y, tilt_line_top_x, tilt_line_top_y, trunk_start):
    """
    Validate if the tilt line accurately follows the tree trunk.
    Returns: (is_valid, accuracy_score)
    """
    height, width = binary.shape
    
    # Create a mask of the tilt line
    line_mask = np.zeros_like(binary)
    cv2.line(line_mask, (tilt_line_bottom_x, tilt_line_bottom_y), 
             (tilt_line_top_x, tilt_line_top_y), 255, 3)
    
    # Get all points along the line
    line_points = np.where(line_mask > 0)
    
    if len(line_points[0]) == 0:
        return False, 0.0
    
    # Check what percentage of the line overlaps with tree pixels
    # Focus on the trunk region (from trunk_start down)
    trunk_line_points = [(y, x) for y, x in zip(line_points[0], line_points[1]) if y >= trunk_start]
    
    if len(trunk_line_points) == 0:
        return False, 0.0
    
    # Count how many line points overlap with tree
    overlap_count = 0
    for y, x in trunk_line_points:
        if binary[y, x] > 0:
            overlap_count += 1
    
    # Calculate overlap percentage
    overlap_percentage = overlap_count / len(trunk_line_points)
    
    # Also check if the line stays within reasonable bounds of the tree
    # Sample points along the line and check neighborhood
    sample_points = trunk_line_points[::max(1, len(trunk_line_points)//20)]  # Sample ~20 points
    
    neighborhood_overlap = 0
    neighborhood_radius = 10  # pixels
    
    for y, x in sample_points:
        # Check if there are tree pixels in the neighborhood
        y_min = max(0, y - neighborhood_radius)
        y_max = min(height, y + neighborhood_radius)
        x_min = max(0, x - neighborhood_radius)
        x_max = min(width, x + neighborhood_radius)
        
        neighborhood = binary[y_min:y_max, x_min:x_max]
        if np.sum(neighborhood > 0) > 0:
            neighborhood_overlap += 1
    
    neighborhood_percentage = neighborhood_overlap / len(sample_points) if len(sample_points) > 0 else 0
    
    # Combined accuracy score
    accuracy_score = (overlap_percentage * 0.6) + (neighborhood_percentage * 0.4)
    
    print(f"Tilt line validation:")
    print(f"  Direct overlap: {overlap_percentage*100:.1f}%")
    print(f"  Neighborhood overlap: {neighborhood_percentage*100:.1f}%")
    print(f"  Combined accuracy: {accuracy_score*100:.1f}%")
    
    # Consider valid if accuracy is above 40%
    is_valid = accuracy_score > 0.4
    
    return is_valid, accuracy_score

def detect_tree_tilt(image_path, attempt=1, max_attempts=3):
    print(f"\n{'='*60}")
    print(f"TILT DETECTION ATTEMPT {attempt}/{max_attempts}")
    print(f"{'='*60}")
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"ERROR: File does not exist: {image_path}")
        return None
    
    # Read the image with alpha channel
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    if img is None:
        print(f"ERROR: Could not read image from {image_path}")
        return None
    
    print(f"Image shape: {img.shape}")
    
    # Step 1: Convert to binary image with better visibility
    if len(img.shape) == 3 and img.shape[2] == 4:
        # Use alpha channel as mask - anything with alpha > 20 is tree
        binary = (img[:, :, 3] > 20).astype(np.uint8) * 255
        print("Created binary from alpha channel (threshold=20)")
    elif len(img.shape) == 3:
        # Convert to grayscale first
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Use Otsu's method for automatic thresholding to preserve detail
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("Created binary from grayscale using Otsu's method")
    else:
        # Already grayscale
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print("Created binary from grayscale using Otsu's method")
    
    # Optional: Apply morphological operations to clean up the binary image
    # Remove small noise
    kernel_small = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small)
    
    # Fill small holes
    kernel_medium = np.ones((5, 5), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_medium)
    
    print("Applied morphological operations to clean binary image")
    
    # Step 2: Find lines in binary image using Hough Transform
    height, width = binary.shape
    
    # Adjust parameters based on attempt number
    if attempt == 1:
        # Standard parameters
        threshold = 30
        min_line_length = max(30, int(height * 0.15))
        max_line_gap = 20
        trunk_percentage = 0.5
    elif attempt == 2:
        # More lenient parameters
        threshold = 20
        min_line_length = max(20, int(height * 0.10))
        max_line_gap = 30
        trunk_percentage = 0.4
    else:
        # Most lenient parameters
        threshold = 15
        min_line_length = max(15, int(height * 0.08))
        max_line_gap = 40
        trunk_percentage = 0.3
    
    print(f"Using detection parameters (attempt {attempt}):")
    print(f"  Threshold: {threshold}, Min length: {min_line_length}, Max gap: {max_line_gap}")
    print(f"  Trunk region: lower {trunk_percentage*100:.0f}%")
    
    # Focus on lower portion for trunk
    trunk_start = int(height * trunk_percentage)
    trunk_binary = binary.copy()
    trunk_binary[:trunk_start, :] = 0  # Zero out upper portion
    
    # Detect lines
    lines = cv2.HoughLinesP(trunk_binary, 1, np.pi/180, threshold=threshold, 
                            minLineLength=min_line_length, maxLineGap=max_line_gap)
    
    if lines is None:
        print("No lines detected in binary image")
        return None
    
    print(f"Detected {len(lines)} lines")
    
    # Step 3: Find where each line intersects the bottom of the image
    bottom_y = height - 1
    center_x = width / 2
    
    intersections = []
    trunk_lines = []
    
    for line in lines:
        x1, y1, x2, y2 = line[0]
        
        # Calculate angle from horizontal
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0:
            angle_from_horizontal = 90
        else:
            angle_from_horizontal = abs(math.degrees(math.atan2(dy, dx)))
        
        # Only process somewhat vertical lines
        if angle_from_horizontal > 30:
            # Extend line to bottom of image
            # Line equation: y - y1 = m(x - x1), solve for x when y = bottom_y
            if dy != 0:
                slope = dx / dy
                x_at_bottom = x1 + slope * (bottom_y - y1)
                
                # Calculate distance from center
                distance_from_center = x_at_bottom - center_x
                
                line_length = math.sqrt(dx**2 + dy**2)
                actual_angle = math.degrees(math.atan2(dy, dx))
                
                intersections.append((x_at_bottom, distance_from_center, line_length))
                trunk_lines.append((x1, y1, x2, y2, actual_angle, line_length, x_at_bottom))
                
                print(f"  Line intersects bottom at x={x_at_bottom:.1f}, distance from center: {distance_from_center:.1f}")
    
    if not intersections:
        print("No valid trunk lines found")
        return None
    
    print(f"Found {len(trunk_lines)} trunk lines")
    
    # Calculate weighted average bottom intersection point (weighted by line length)
    total_weight = sum(intersection[2] for intersection in intersections)
    weighted_bottom_x = sum(intersection[0] * intersection[2] for intersection in intersections) / total_weight
    
    # Calculate tilt angle based on where trunk hits bottom vs center
    # Positive angle = tilted right, negative = tilted left
    offset_from_center = weighted_bottom_x - center_x
    
    # Calculate angle: arctan(horizontal offset / vertical distance)
    # Using full height as vertical distance for the angle calculation
    tilt_angle = math.degrees(math.atan(offset_from_center / height))
    
    print(f"Weighted bottom intersection: x={weighted_bottom_x:.1f}")
    print(f"Center x: {center_x:.1f}")
    print(f"Offset from center: {offset_from_center:.1f} pixels")
    print(f"Tilt angle: {tilt_angle:.2f}°")
    
    # === Find the horizontal center of the tree at trunk level ===
    # Scan the trunk region to find actual tree boundaries
    trunk_region = binary[trunk_start:, :]
    tree_pixels_per_row = np.sum(trunk_region > 0, axis=1)
    
    # Find rows with significant tree content
    valid_rows = np.where(tree_pixels_per_row > width * 0.05)[0]  # At least 5% of width
    
    if len(valid_rows) > 0:
        # For each valid row, find the leftmost and rightmost tree pixels
        left_edges = []
        right_edges = []
        
        for row_idx in valid_rows:
            row = trunk_region[row_idx, :]
            tree_cols = np.where(row > 0)[0]
            if len(tree_cols) > 0:
                left_edges.append(tree_cols[0])
                right_edges.append(tree_cols[-1])
        
        # Calculate average horizontal center of the tree trunk
        avg_left = np.mean(left_edges)
        avg_right = np.mean(right_edges)
        tree_center_x = (avg_left + avg_right) / 2
        print(f"Tree trunk center detected at x={tree_center_x:.1f}")
    else:
        # Fallback to weighted bottom x
        tree_center_x = weighted_bottom_x
        print(f"Using weighted bottom x as tree center: {tree_center_x:.1f}")
    
    # === Create three separate visualizations ===
    
    # 1. Green lines visualization (original detailed view)
    lines_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # Draw all detected trunk lines
    for x1, y1, x2, y2, _, length, x_bottom in trunk_lines:
        # Color by length - longer lines are brighter
        intensity = min(255, int(100 + (length / height) * 155))
        cv2.line(lines_img, (x1, y1), (x2, y2), (0, intensity, 0), 2)
        
        # Draw extension to bottom
        cv2.line(lines_img, (x2, y2), (int(x_bottom), bottom_y), (0, intensity//2, 0), 1)
        
        # Mark bottom intersection
        cv2.circle(lines_img, (int(x_bottom), bottom_y), 5, (0, 255, 255), -1)
    
    # Draw trunk region boundary
    cv2.line(lines_img, (0, trunk_start), (width, trunk_start), (255, 0, 0), 2)
    
    # Draw center vertical reference line
    cv2.line(lines_img, (int(center_x), trunk_start), (int(center_x), height), (0, 0, 255), 2)
    
    # Draw weighted average bottom point
    cv2.circle(lines_img, (int(weighted_bottom_x), bottom_y), 10, (255, 0, 255), -1)
    
    # Draw angle visualization line from center top to weighted bottom
    cv2.line(lines_img, (int(center_x), trunk_start), (int(weighted_bottom_x), bottom_y), (255, 0, 255), 3)
    
    # Draw angle text
    cv2.putText(lines_img, f'Tilt: {tilt_angle:.2f} deg', 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(lines_img, f'{len(trunk_lines)} lines', 
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # 2. Plain binary (just convert to BGR for consistency)
    plain_binary = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # 3. Final tilt line visualization
    tilt_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # Check for sweep before drawing the tilt line
    has_sweep, is_problematic_tilt, sweep_description, center_points = detect_tree_sweep(binary, tree_center_x, height, width)
    
    # Draw visualization based on sweep and tilt analysis
    if has_sweep and not is_problematic_tilt:
        # Natural sweep - draw the curved path (SAFE)
        for i in range(len(center_points) - 1):
            pt1 = (int(center_points[i][0]), int(center_points[i][1]))
            pt2 = (int(center_points[i+1][0]), int(center_points[i+1][1]))
            cv2.line(tilt_img, pt1, pt2, (0, 255, 0), 4)  # GREEN for safe sweep
        
        # Mark center points
        for cx, cy in center_points:
            cv2.circle(tilt_img, (int(cx), int(cy)), 5, (0, 255, 0), -1)
        
        # Add safe sweep indicator
        cv2.putText(tilt_img, 'NATURAL SWEEP', 
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        cv2.putText(tilt_img, 'SAFE', 
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.putText(tilt_img, f'Tilt: {tilt_angle:.2f} deg', 
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    elif is_problematic_tilt:
        # Problematic whole-trunk tilt (>7 degrees, no curve-back) - RED WARNING
        for i in range(len(center_points) - 1):
            pt1 = (int(center_points[i][0]), int(center_points[i][1]))
            pt2 = (int(center_points[i+1][0]), int(center_points[i+1][1]))
            cv2.line(tilt_img, pt1, pt2, (0, 0, 255), 4)  # RED for danger
        
        # Mark center points
        for cx, cy in center_points:
            cv2.circle(tilt_img, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        
        # Add warning
        cv2.putText(tilt_img, 'WHOLE TRUNK TILT', 
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
        cv2.putText(tilt_img, 'RISK!', 
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.putText(tilt_img, f'Tilt: {tilt_angle:.2f} deg (>7 deg)', 
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    else:
        # Minor tilt or straight growth - draw simple tilt line
        # Calculate the line endpoints
        tilt_line_bottom_x = int(tree_center_x)
        tilt_line_bottom_y = height - 1
        
        # Project upward along the tilt angle
        vertical_distance = height
        horizontal_displacement = vertical_distance * math.tan(math.radians(tilt_angle))
        
        tilt_line_top_x = int(tree_center_x - horizontal_displacement)
        tilt_line_top_y = 0
        
        # Color based on angle: green if <7°, yellow if >=7°
        if abs(tilt_angle) < 7:
            line_color = (0, 255, 0)  # Green - SAFE
            status_text = 'SAFE'
            status_color = (0, 255, 0)
        else:
            line_color = (0, 255, 255)  # Yellow - CAUTION
            status_text = 'CAUTION'
            status_color = (0, 255, 255)
        
        # Draw the main tilt line as an arrow
        cv2.arrowedLine(tilt_img,
                        (tilt_line_bottom_x, tilt_line_bottom_y),
                        (tilt_line_top_x, tilt_line_top_y),
                        line_color, 6, tipLength=0.03)
        
        # Add status and angle text
        cv2.putText(tilt_img, status_text, 
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
        cv2.putText(tilt_img, f'Tilt: {tilt_angle:.2f} deg', 
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
        
        # Add label at the center of the tilt line
        label_x = int((tilt_line_bottom_x + tilt_line_top_x) / 2)
        label_y = int((tilt_line_bottom_y + tilt_line_top_y) / 2)
        cv2.putText(tilt_img, 'TILT', 
                    (label_x + 15, label_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, line_color, 3)
    
    # Combine all three images side by side
    combined_img = np.hstack([lines_img, plain_binary, tilt_img])
    
    # === VALIDATE THE TILT LINE (only if straight tilt, not problematic) ===
    if not has_sweep and not is_problematic_tilt:
        # Need to recalculate tilt line endpoints for validation
        tilt_line_bottom_x = int(tree_center_x)
        tilt_line_bottom_y = height - 1
        vertical_distance = height
        horizontal_displacement = vertical_distance * math.tan(math.radians(tilt_angle))
        tilt_line_top_x = int(tree_center_x - horizontal_displacement)
        tilt_line_top_y = 0
        
        is_valid, accuracy = validate_tilt_line(binary, tilt_line_bottom_x, tilt_line_bottom_y, 
                                                 tilt_line_top_x, tilt_line_top_y, trunk_start)
        
        if not is_valid and attempt < max_attempts:
            print(f"\n Tilt line validation FAILED (accuracy: {accuracy*100:.1f}%)")
            print(f"Retrying with adjusted parameters...")
            
            # Recursively call with next attempt
            return detect_tree_tilt(image_path, attempt + 1, max_attempts)
        
        if is_valid:
            print(f"\n Tilt line validation PASSED (accuracy: {accuracy*100:.1f}%)")
        else:
            print(f"\n Tilt line validation FAILED after {max_attempts} attempts (accuracy: {accuracy*100:.1f}%)")
            print("Proceeding with best available result...")
    elif has_sweep and not is_problematic_tilt:
        print(f"\n NATURAL SWEEP DETECTED - Tree is SAFE")
        print(f"Tree curves back toward vertical - this is healthy growth behavior")
    elif is_problematic_tilt:
        print(f"\n PROBLEMATIC WHOLE-TRUNK TILT DETECTED")
        print(f"Entire trunk is tilted beyond safe threshold (>7°) - RISK")
    else:
        print(f"\n Minor tilt within safe range (<7°)")
    
    trunk_lines_count = len(trunk_lines)
    return tilt_angle, combined_img, binary, trunk_lines_count