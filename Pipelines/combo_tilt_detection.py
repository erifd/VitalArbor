import cv2
import numpy as np
import math
import os
from PIL import Image, ImageDraw
from sklearn.decomposition import PCA
from skimage.morphology import closing, square, remove_small_holes, remove_small_objects

def detect_tree_tilt_combined(image_path, pca_weight=0.5, rotation_angles=[-5, 0, 5]):
    """
    Combined tree tilt detection using both PCA and line intersection methods.
    
    Args:
        image_path: Path to the segmented tree image
        pca_weight: Weight for PCA result (0-1). Line intersection gets (1-pca_weight)
        rotation_angles: List of rotation angles to try for PCA (in degrees)
    
    Returns:
        dict with tilt_angle, method_results, and visualization image
    """
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"ERROR: File does not exist: {image_path}")
        return None
    
    # Read the image
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    if img is None:
        print(f"ERROR: Could not read image from {image_path}")
        return None
    
    print(f"Image shape: {img.shape}")
    height, width = img.shape[:2]
    
    # ===== STEP 1: Create binary mask =====
    if len(img.shape) == 3 and img.shape[2] == 4:
        binary = (img[:, :, 3] > 127).astype(np.uint8) * 255
        print("Created binary from alpha channel")
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        print("Created binary from grayscale")
    
    # Clean mask
    binary_bool = binary > 0
    mask_clean = remove_small_holes(binary_bool, area_threshold=200)
    mask_clean = remove_small_objects(mask_clean, min_size=200)
    mask_clean = closing(mask_clean, square(40))
    binary_cleaned = (mask_clean * 255).astype(np.uint8)
    
    # ===== STEP 2: PCA Method with Multiple Rotations =====
    pca_results = []
    
    # Get mask coordinates
    ys, xs = np.where(mask_clean == 1)
    mask_coords = np.column_stack((xs, ys))
    
    if len(mask_coords) > 0:
        # Try multiple rotation angles for PCA
        for rot_angle in rotation_angles:
            # Rotate coordinates
            rot_rad = math.radians(rot_angle)
            cos_a, sin_a = math.cos(rot_rad), math.sin(rot_rad)
            center_x, center_y = width / 2, height / 2
            
            # Translate to origin, rotate, translate back
            coords_centered = mask_coords - np.array([center_x, center_y])
            rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            coords_rotated = coords_centered @ rot_matrix.T
            
            # Fit PCA
            pca = PCA(n_components=2)
            pca.fit(coords_rotated)
            pc1 = pca.components_[0]
            pc1 = pc1 / np.linalg.norm(pc1)
            
            # Rotate PC1 back to original orientation
            pc1_original = rot_matrix.T @ pc1
            
            # Calculate angle from vertical
            vertical = np.array([0, -1])
            dot = np.dot(pc1_original, vertical)
            angle_rad = math.acos(np.clip(dot, -1.0, 1.0))
            angle_deg = math.degrees(angle_rad)
            
            # Determine sign (left/right tilt)
            cross = pc1_original[0] * vertical[1] - pc1_original[1] * vertical[0]
            if cross > 0:
                angle_deg = -angle_deg
            
            pca_results.append({
                'rotation': rot_angle,
                'angle': angle_deg,
                'component': pc1_original,
                'explained_variance': pca.explained_variance_ratio_[0]
            })
            
            print(f"PCA with rotation {rot_angle}°: tilt = {angle_deg:.2f}°, variance explained = {pca.explained_variance_ratio_[0]:.3f}")
    
    # Select best PCA result (highest explained variance)
    if pca_results:
        best_pca = max(pca_results, key=lambda x: x['explained_variance'])
        pca_angle = best_pca['angle']
        print(f"Best PCA angle: {pca_angle:.2f}° (rotation={best_pca['rotation']}°)")
    else:
        pca_angle = None
        print("PCA failed")
    
    # ===== STEP 3: Line Intersection Method =====
    trunk_start = int(height * 0.5)
    trunk_binary = binary_cleaned.copy()
    trunk_binary[:trunk_start, :] = 0
    
    lines = cv2.HoughLinesP(trunk_binary, 1, np.pi/180, threshold=30, 
                            minLineLength=max(30, int(height * 0.15)), maxLineGap=20)
    
    line_angle = None
    trunk_lines = []
    
    if lines is not None:
        print(f"Detected {len(lines)} lines")
        bottom_y = height - 1
        center_x = width / 2
        intersections = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            
            if dx == 0:
                angle_from_horizontal = 90
            else:
                angle_from_horizontal = abs(math.degrees(math.atan2(dy, dx)))
            
            if angle_from_horizontal > 30:
                if dy != 0:
                    slope = dx / dy
                    x_at_bottom = x1 + slope * (bottom_y - y1)
                    line_length = math.sqrt(dx**2 + dy**2)
                    
                    intersections.append((x_at_bottom, line_length))
                    trunk_lines.append((x1, y1, x2, y2, line_length, x_at_bottom))
        
        if intersections:
            total_weight = sum(i[1] for i in intersections)
            weighted_bottom_x = sum(i[0] * i[1] for i in intersections) / total_weight
            offset_from_center = weighted_bottom_x - center_x
            line_angle = math.degrees(math.atan(offset_from_center / height))
            
            print(f"Line intersection angle: {line_angle:.2f}°")
        else:
            print("No valid trunk lines found")
    else:
        print("No lines detected")
    
    # ===== STEP 4: Combine Results =====
    if pca_angle is not None and line_angle is not None:
        combined_angle = pca_weight * pca_angle + (1 - pca_weight) * line_angle
        print(f"Combined angle: {combined_angle:.2f}° (PCA: {pca_angle:.2f}°, Lines: {line_angle:.2f}°)")
    elif pca_angle is not None:
        combined_angle = pca_angle
        print(f"Using PCA only: {combined_angle:.2f}°")
    elif line_angle is not None:
        combined_angle = line_angle
        print(f"Using line intersection only: {combined_angle:.2f}°")
    else:
        print("ERROR: Both methods failed")
        return None
    
    # ===== STEP 5: Visualization =====
    result_img = cv2.cvtColor(binary_cleaned, cv2.COLOR_GRAY2BGR)
    
    # Draw line intersections
    if trunk_lines:
        for x1, y1, x2, y2, length, x_bottom in trunk_lines:
            intensity = min(255, int(100 + (length / height) * 155))
            cv2.line(result_img, (x1, y1), (x2, y2), (0, intensity, 0), 2)
            cv2.circle(result_img, (int(x_bottom), height-1), 5, (0, 255, 255), -1)
        
        if line_angle is not None:
            center_x = width / 2
            weighted_bottom_x = sum(i[0] * i[1] for i in intersections) / sum(i[1] for i in intersections)
            cv2.line(result_img, (int(center_x), trunk_start), 
                    (int(weighted_bottom_x), height-1), (0, 255, 255), 3)
    
    # Draw PCA axis
    if pca_angle is not None and len(mask_coords) > 0:
        centroid = mask_coords.mean(axis=0)
        scale = max(height, width)
        pc1 = best_pca['component']
        p1 = (int(centroid[0] - pc1[0] * scale), int(centroid[1] - pc1[1] * scale))
        p2 = (int(centroid[0] + pc1[0] * scale), int(centroid[1] + pc1[1] * scale))
        cv2.line(result_img, p1, p2, (255, 0, 255), 3)
        cv2.circle(result_img, (int(centroid[0]), int(centroid[1])), 8, (255, 0, 255), -1)
    
    # Draw center reference line
    cv2.line(result_img, (int(width/2), 0), (int(width/2), height), (0, 0, 255), 2)
    
    # Add text annotations
    y_pos = 30
    cv2.putText(result_img, f'Combined: {combined_angle:.2f} deg', 
                (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    y_pos += 35
    
    if pca_angle is not None:
        cv2.putText(result_img, f'PCA: {pca_angle:.2f} deg', 
                    (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        y_pos += 30
    
    if line_angle is not None:
        cv2.putText(result_img, f'Lines: {line_angle:.2f} deg', 
                    (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # Return results in same format as original tilt_detection
    trunk_lines_count = len(trunk_lines) if trunk_lines else 0
    return combined_angle, result_img, binary_cleaned, trunk_lines_count


if __name__ == "__main__":
    """
    Example usage of combined tilt detection.
    
    This script combines two methods:
    1. PCA (Principal Component Analysis) - finds the main axis of the tree shape
    2. Line Intersection - detects trunk lines and where they intersect the bottom
    
    The methods are combined using a weighted average for robust results.
    """
    
    # Set your image path
    image_path = "path/to/your/segmented_tree.png"
    
    # Configure detection parameters
    # pca_weight: How much to trust PCA vs line detection
    #   0.5 = equal weight to both methods
    #   0.7 = trust PCA more (good for full tree images)
    #   0.3 = trust line detection more (good for trunk closeups)
    
    # rotation_angles: Test PCA at different orientations to find best fit
    #   Helpful when tree leans significantly
    
    result = detect_tree_tilt_combined(
        image_path, 
        pca_weight=0.6,  # Give PCA slightly more weight
        rotation_angles=[-10, -5, 0, 5, 10]  # Try 5 different orientations
    )
    
    if result:
        print(f"\n{'='*50}")
        print(f"COMBINED TILT DETECTION RESULTS")
        print(f"{'='*50}")
        print(f"Combined tilt angle: {result['combined_angle']:.2f}°")
        print(f"  PCA method:              {result['pca_angle']:.2f}°" if result['pca_angle'] else "  PCA: Failed")
        print(f"  Line intersection method: {result['line_angle']:.2f}°" if result['line_angle'] else "  Line detection: Failed")
        print(f"  Trunk lines detected:     {result['num_lines']}")
        print(f"{'='*50}")
        
        # Interpret the angle
        angle = result['combined_angle']
        if abs(angle) < 2:
            interpretation = "Tree is nearly vertical (safe)"
        elif abs(angle) < 5:
            interpretation = "Slight lean (monitor)"
        elif abs(angle) < 10:
            interpretation = "Moderate lean (assess risk)"
        else:
            interpretation = "Significant lean (high risk)"
        
        direction = "right" if angle > 0 else "left"
        print(f"\nInterpretation: {interpretation}")
        print(f"Direction: Leaning {direction}")
        
        # Save visualization
        output_path = "tilt_analysis_combined.png"
        cv2.imwrite(output_path, result['visualization'])
        print(f"\nVisualization saved to: {output_path}")
        
        # Display the result
        cv2.imshow('Combined Tilt Detection (Magenta=PCA, Cyan=Lines)', result['visualization'])
        print("\nPress any key to close the visualization window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("\nERROR: Tilt detection failed!")
        print("Both methods were unable to analyze the tree.")