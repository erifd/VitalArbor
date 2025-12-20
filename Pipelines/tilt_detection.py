import cv2
import numpy as np
import math
import os
import sam2_segmentation

def detect_tree_tilt(image_path):
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
    
    # Focus on lower 50% for trunk
    trunk_start = int(height * 0.5)
    trunk_binary = binary.copy()
    trunk_binary[:trunk_start, :] = 0  # Zero out upper portion
    
    # Detect lines
    lines = cv2.HoughLinesP(trunk_binary, 1, np.pi/180, threshold=30, 
                            minLineLength=max(30, int(height * 0.15)), maxLineGap=20)
    
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
    
    # Visualize
    result_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # Draw all detected trunk lines
    for x1, y1, x2, y2, _, length, x_bottom in trunk_lines:
        # Color by length - longer lines are brighter
        intensity = min(255, int(100 + (length / height) * 155))
        cv2.line(result_img, (x1, y1), (x2, y2), (0, intensity, 0), 2)
        
        # Draw extension to bottom
        cv2.line(result_img, (x2, y2), (int(x_bottom), bottom_y), (0, intensity//2, 0), 1)
        
        # Mark bottom intersection
        cv2.circle(result_img, (int(x_bottom), bottom_y), 5, (0, 255, 255), -1)
    
    # Draw trunk region boundary
    cv2.line(result_img, (0, trunk_start), (width, trunk_start), (255, 0, 0), 2)
    
    # Draw center vertical reference line
    cv2.line(result_img, (int(center_x), trunk_start), (int(center_x), height), (0, 0, 255), 2)
    
    # Draw weighted average bottom point
    cv2.circle(result_img, (int(weighted_bottom_x), bottom_y), 10, (255, 0, 255), -1)
    
    # Draw angle visualization line from center top to weighted bottom
    cv2.line(result_img, (int(center_x), trunk_start), (int(weighted_bottom_x), bottom_y), (255, 0, 255), 3)
    
    # Draw angle text
    cv2.putText(result_img, f'Tilt: {tilt_angle:.2f} deg', 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(result_img, f'{len(trunk_lines)} lines', 
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    trunk_lines_count = len(trunk_lines)
    return tilt_angle, result_img, binary, trunk_lines_count