import cv2
import numpy as np
import math
import os
import sam2_segmentation
# sam2_segmentation.run_sam2_segmentation(r"C:\Users\family_2\Documents\GitHub\VitalArbor\2025-26_Data_Links\10-21-2025\Spruce_Photos\Spruce_1_.png")

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
    
    # Step 1: Convert to binary image
    if len(img.shape) == 3 and img.shape[2] == 4:
        # Use alpha channel as mask
        binary = (img[:, :, 3] > 127).astype(np.uint8) * 255
        print("Created binary from alpha channel")
    else:
        # Convert to grayscale and threshold
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        print("Created binary from grayscale")
    
    # Step 2: Find lines in binary image using Hough Transform
    height, width = binary.shape
    
    # Focus on lower 45% for trunk
    trunk_start = int(height * 0.55)  # Start at 55% down (lower 45%)
    trunk_binary = binary.copy()
    trunk_binary[:trunk_start, :] = 0  # Zero out upper portion
    
    # Detect lines
    lines = cv2.HoughLinesP(trunk_binary, 1, np.pi/180, threshold=30, 
                            minLineLength=max(30, int(height * 0.15)), maxLineGap=20)
    
    if lines is None:
        print("No lines detected in binary image")
        return None
    
    print(f"Detected {len(lines)} lines")
    
    # Step 3: Filter for ROUGHLY vertical lines (much more lenient)
    trunk_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        
        # Calculate angle from horizontal
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0:
            angle_from_horizontal = 90  # Perfectly vertical
        else:
            angle_from_horizontal = abs(math.degrees(math.atan2(dy, dx)))
        
        # Accept lines that are MORE vertical than horizontal
        # (angle from horizontal > 45 degrees means more vertical than horizontal)
        if angle_from_horizontal > 30:  # Very lenient - just needs to be somewhat vertical
            line_length = math.sqrt(dx**2 + dy**2)
            actual_angle = math.degrees(math.atan2(dy, dx))
            trunk_lines.append((x1, y1, x2, y2, actual_angle, line_length))
            print(f"  Line: ({x1},{y1})->({x2},{y2}), angle: {actual_angle:.1f}°, length: {line_length:.1f}")
    
    if not trunk_lines:
        print("No trunk lines found")
        return None
    
    print(f"Found {len(trunk_lines)} trunk lines")
    
    # Calculate weighted average angle (weighted by line length)
    total_weight = sum(line[5] for line in trunk_lines)
    weighted_angle = sum(line[4] * line[5] for line in trunk_lines) / total_weight
    
    # Tilt angle from vertical (0 = perfectly vertical, which is 90 from horizontal)
    tilt_angle = -1* (weighted_angle - 90)
    if tilt_angle > 90:
        tilt_angle = 180 - tilt_angle
    
    print(f"Weighted angle from horizontal: {weighted_angle:.2f}°")
    print(f"Tilt angle from vertical: {tilt_angle:.2f}°")
    
    # Visualize
    result_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    
    # Draw all detected trunk lines
    for x1, y1, x2, y2, _, length in trunk_lines:
        # Color by length - longer lines are brighter
        intensity = min(255, int(100 + (length / height) * 155))
        cv2.line(result_img, (x1, y1), (x2, y2), (0, intensity, 0), 2)
    
    # Draw trunk region boundary
    cv2.line(result_img, (0, trunk_start), (width, trunk_start), (255, 0, 0), 2)
    
    # Draw a reference vertical line
    center_x = width // 2
    cv2.line(result_img, (center_x, trunk_start), (center_x, height), (0, 0, 255), 2)
    
    # Draw angle text
    cv2.putText(result_img, f'Tilt: {tilt_angle:.2f} deg', 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(result_img, f'{len(trunk_lines)} lines', 
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    return tilt_angle, result_img, binary

# Usage
# image_path = r"C:\Users\family_2\Documents\GitHub\VitalArbor\Segmented photos\Spruce_1__crop_out.png"
# print(f"Checking if file exists: {os.path.exists(image_path)}")
# print(f"Full path: {os.path.abspath(image_path)}")

# result = detect_tree_tilt(image_path)
# if result is not None:
#     tilt, result_img, binary = result
#     print(f"\n=== FINAL RESULT ===")
#     print(f"Tree tilt angle: {tilt:.2f} degrees from vertical")
    
#     # Display binary and result side by side
#     display_height = 600
#     aspect_ratio = binary.shape[1] / binary.shape[0]
#     display_width = int(display_height * aspect_ratio)
    
#     binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), (display_width, display_height))
#     result_display = cv2.resize(result_img, (display_width, display_height))
    
#     combined = np.hstack([binary_display, result_display])
    
#     cv2.imshow('Binary | Detected Lines', combined)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()
# else:
#     print("Could not detect tree trunk")