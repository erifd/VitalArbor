import os
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

def get_trunk_width_analysis(mask_path):
    # ---------------------------------------------------
    # 1. Determine Paths Based on Your Structure
    # ---------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    target_dir = os.path.join(root_dir, "Segmented photos")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # ---------------------------------------------------
    # 2. Load image - preserve original format (RGB/RGBA)
    # ---------------------------------------------------
    img_original = Image.open(mask_path)
    
    # Convert to RGB for color analysis (handle RGBA)
    if img_original.mode == 'RGBA':
        img_rgb = img_original.convert('RGB')
    else:
        img_rgb = img_original.convert('RGB')
    
    # Create grayscale version for mask detection
    img_gray = img_original.convert("L")
    mask = np.array(img_gray)
    img_rgb_array = np.array(img_rgb)

    mask_bin = (mask > 127).astype(np.uint8) * 255
    h, w = mask_bin.shape

    # ---------------------------------------------------
    # 3. Compute width profile and color profile with gap handling
    # ---------------------------------------------------
    widths = np.zeros(h)
    mean_colors = np.zeros((h, 3))  # Store mean R, G, B for each row
    valid_rows = []  # Track which rows have actual pixels
    
    for row in range(h):
        cols = np.where(mask_bin[row] > 0)[0]
        if len(cols) > 0:
            widths[row] = cols.max() - cols.min()
            # Get mean color for this row
            row_pixels = img_rgb_array[row, cols, :]
            mean_colors[row] = np.mean(row_pixels, axis=0)
            valid_rows.append(row)
        else:
            widths[row] = 0
            mean_colors[row] = [0, 0, 0]
    
    valid_rows = np.array(valid_rows)
    
    # Fill small gaps in width profile (interpolate across gaps < 20 pixels)
    max_gap = 20
    for i in range(len(valid_rows) - 1):
        gap_size = valid_rows[i+1] - valid_rows[i] - 1
        if 0 < gap_size <= max_gap:
            # Linear interpolation for width
            start_row = valid_rows[i]
            end_row = valid_rows[i+1]
            start_width = widths[start_row]
            end_width = widths[end_row]
            for r in range(start_row + 1, end_row):
                alpha = (r - start_row) / (end_row - start_row)
                widths[r] = start_width * (1 - alpha) + end_width * alpha
                # Also interpolate colors
                mean_colors[r] = mean_colors[start_row] * (1 - alpha) + mean_colors[end_row] * alpha

    # ---------------------------------------------------
    # 4. Smooth width & Iteratively detect trunk
    # ---------------------------------------------------
    smoothed_width = savgol_filter(widths, window_length=301, polyorder=3, mode="interp")
    slope = np.abs(np.gradient(smoothed_width))

    stable_slope_thresh = 1.2  # More lenient for fragmented masks
    
    # Look for trunk-like widths (not the thinnest branches, not the full canopy)
    valid_widths = smoothed_width[smoothed_width > 10]  # Ignore near-zero widths
    if len(valid_widths) == 0:
        raise ValueError("No valid width measurements found in image")
    
    max_trunk_width = np.percentile(valid_widths, 65)
    min_trunk_width = np.percentile(valid_widths, 20)
    
    print(f"Width range for trunk detection: {min_trunk_width:.1f} to {max_trunk_width:.1f} pixels")
    
    # Color stability threshold (standard deviation across RGB channels)
    color_stability_thresh = 20.0  # More lenient for real-world trunk texture
    
    # Additional constraint: trunk should be in lower portion of image
    # and have consistent brownish/grayish color
    min_trunk_row = int(h * 0.25)  # Don't look for trunk in top 25% of image
    
    # Minimum trunk height to avoid tiny slivers - but allow for gaps
    min_trunk_height = 150  # pixels
    max_gap_in_trunk = 30  # Allow gaps up to this many pixels within a trunk region
    
    # Exclusion zones (rows to skip in future iterations)
    excluded_rows = set()
    
    max_iterations = 10
    trunk_start = None
    trunk_end = None
    
    # Progressive relaxation: if we can't find anything, gradually relax criteria
    relaxation_levels = [
        {"color_thresh": 20.0, "brightness_thresh": 30.0, "min_height": 150},
        {"color_thresh": 25.0, "brightness_thresh": 35.0, "min_height": 120},
        {"color_thresh": 30.0, "brightness_thresh": 40.0, "min_height": 100},
        {"color_thresh": 40.0, "brightness_thresh": 50.0, "min_height": 80},
    ]
    
    current_relaxation = 0
    
    for iteration in range(max_iterations):
        # Apply current relaxation level
        if iteration > 0 and iteration % 3 == 0 and current_relaxation < len(relaxation_levels) - 1:
            current_relaxation += 1
            excluded_rows.clear()  # Reset exclusions when relaxing
            print(f"\n*** Relaxing criteria to level {current_relaxation + 1} ***")
        
        relax = relaxation_levels[current_relaxation]
        color_stability_thresh = relax["color_thresh"]
        brightness_stability_thresh = relax["brightness_thresh"]
        min_trunk_height = relax["min_height"]
        
        print(f"\n--- Iteration {iteration + 1} (Relaxation Level {current_relaxation + 1}) ---")
        print(f"Thresholds: color<{color_stability_thresh}, brightness<{brightness_stability_thresh}, height>{min_trunk_height}")
        
        # Find stable width regions (excluding already rejected rows)
        stable_rows = np.where(
            (slope < stable_slope_thresh) &
            (smoothed_width < max_trunk_width) &
            (smoothed_width > min_trunk_width) &  # Not too thin
            (np.arange(h) >= min_trunk_row)  # Only consider lower portion
        )[0]
        
        # Remove excluded rows
        stable_rows = np.array([r for r in stable_rows if r not in excluded_rows])
        
        if len(stable_rows) == 0:
            print("No more stable width regions found.")
            if current_relaxation < len(relaxation_levels) - 1:
                continue  # Will relax on next iteration
            else:
                break
        
        # Find the largest contiguous segment (allowing small gaps)
        segments = []
        current_segment = [stable_rows[0]]
        
        for i in range(1, len(stable_rows)):
            gap = stable_rows[i] - stable_rows[i-1]
            if gap == 1 or gap <= max_gap_in_trunk:  # Contiguous or small gap
                current_segment.append(stable_rows[i])
            else:  # Large gap, start new segment
                segments.append(current_segment)
                current_segment = [stable_rows[i]]
        segments.append(current_segment)
        
        # Get the longest segment (by span, not count - to handle gaps)
        longest_segment = max(segments, key=lambda seg: max(seg) - min(seg))
        candidate_start = min(longest_segment)
        candidate_end = max(longest_segment)
        
        # Check if segment is tall enough (total span)
        segment_height = candidate_end - candidate_start + 1
        # Also check that we have enough actual data rows (not just gaps)
        actual_row_count = len(longest_segment)
        
        if segment_height < min_trunk_height or actual_row_count < min_trunk_height * 0.6:
            print(f"Segment too short (span: {segment_height}, rows: {actual_row_count}), excluding...")
            excluded_rows.update(longest_segment)
            continue
        
        print(f"Candidate trunk band: rows {candidate_start} to {candidate_end} (height: {segment_height}, actual rows: {actual_row_count})")
        
        # ---------------------------------------------------
        # 5. Check color stability in this region
        # ---------------------------------------------------
        trunk_colors = mean_colors[candidate_start:candidate_end+1]
        
        # Filter out rows with no pixels (all zeros)
        valid_color_rows = trunk_colors[np.any(trunk_colors > 0, axis=1)]
        
        if len(valid_color_rows) == 0:
            print("No valid color data in this region.")
            excluded_rows.update(longest_segment)
            continue
        
        # Calculate color standard deviation across the trunk region
        color_std = np.std(valid_color_rows, axis=0)
        mean_color_std = np.mean(color_std)
        
        # Also check for extreme brightness variation (sky vs dark areas)
        brightness = np.mean(valid_color_rows, axis=1)
        brightness_std = np.std(brightness)
        
        # Check mean color - trunk should be brownish/grayish, not bright or very dark
        mean_color = np.mean(valid_color_rows, axis=0)
        mean_brightness = np.mean(mean_color)
        
        print(f"Color std dev (R, G, B): {color_std}")
        print(f"Mean color std dev: {mean_color_std:.2f}")
        print(f"Brightness std dev: {brightness_std:.2f}")
        print(f"Mean brightness: {mean_brightness:.2f}")
        
        # Trunk criteria:
        # 1. Low color variation
        # 2. Low brightness variation (no sky patches)
        # 3. Moderate brightness (not pure white/black)
        is_color_stable = mean_color_std < color_stability_thresh
        is_brightness_stable = brightness_std < brightness_stability_thresh
        is_reasonable_color = 20 < mean_brightness < 220  # Very broad range
        
        if is_color_stable and is_brightness_stable and is_reasonable_color:
            print(f"✓ Region passes all stability checks! Trunk detected.")
            trunk_start = candidate_start
            trunk_end = candidate_end
            break
        else:
            reasons = []
            if not is_color_stable:
                reasons.append(f"color unstable ({mean_color_std:.2f} > {color_stability_thresh})")
            if not is_brightness_stable:
                reasons.append(f"brightness unstable ({brightness_std:.2f} > {brightness_stability_thresh})")
            if not is_reasonable_color:
                reasons.append(f"unreasonable brightness ({mean_brightness:.2f})")
            
            print(f"✗ Region failed: {', '.join(reasons)}")
            print(f"Excluding rows {candidate_start}-{candidate_end} and retrying...")
            excluded_rows.update(longest_segment)
    
    if trunk_start is None or trunk_end is None:
        # Last resort fallback: just take the largest width-stable region in lower half
        print("\n!!! FALLBACK MODE: Using largest width-stable region regardless of color !!!")
        fallback_rows = np.where(
            (slope < stable_slope_thresh * 1.5) &
            (smoothed_width > min_trunk_width) &
            (np.arange(h) >= min_trunk_row)
        )[0]
        
        if len(fallback_rows) == 0:
            raise ValueError("No stable trunk region detected even in fallback mode.")
        
        # Find longest contiguous segment
        segments = []
        current_segment = [fallback_rows[0]]
        for i in range(1, len(fallback_rows)):
            if fallback_rows[i] - fallback_rows[i-1] <= 50:  # Very lenient gap
                current_segment.append(fallback_rows[i])
            else:
                segments.append(current_segment)
                current_segment = [fallback_rows[i]]
        segments.append(current_segment)
        
        longest_segment = max(segments, key=lambda seg: max(seg) - min(seg))
        trunk_start = min(longest_segment)
        trunk_end = max(longest_segment)
        print(f"Fallback trunk: rows {trunk_start} to {trunk_end}")
    
    print(f"\nFinal detected trunk band: rows {trunk_start} to {trunk_end}")

    # ---------------------------------------------------
    # 6. Crop Logic
    # ---------------------------------------------------
    trunk_cols = []
    for row in range(trunk_start, trunk_end + 1):
        cols = np.where(mask_bin[row] > 0)[0]
        if len(cols) > 0:
            trunk_cols.extend([cols.min(), cols.max()])

    if not trunk_cols:
        raise ValueError("No trunk pixels found in detected band.")

    x_min = max(min(trunk_cols), 0)
    x_max = min(max(trunk_cols), w - 1)

    # ---------------------------------------------------
    # 7. Save Logic - CROP ORIGINAL IMAGE
    # ---------------------------------------------------
    base_name = os.path.splitext(os.path.basename(mask_path))[0]
    
    crop_name = f"{base_name}_trunk_part.png"
    vis_name = f"{base_name}_vis_trunk.png"
    
    crop_save_path = os.path.join(target_dir, crop_name)
    vis_save_path = os.path.join(target_dir, vis_name)

    # Save cropped image - USE ORIGINAL IMAGE to preserve color/alpha
    cropped_trunk = img_original.crop((x_min, trunk_start, x_max, trunk_end))
    cropped_trunk.save(crop_save_path)
    print(f"Saved crop to: {crop_save_path}")
    print(f"Cropped image mode: {cropped_trunk.mode}")

    # ---------------------------------------------------
    # 8. Visualization Logic
    # ---------------------------------------------------
    vis_img = Image.fromarray(mask_bin).convert("RGB")
    draw = ImageDraw.Draw(vis_img)

    for row in range(h):
        cols = np.where(mask_bin[row] > 0)[0]
        if len(cols) > 0:
            x1, x2 = cols.min(), cols.max()
            color = (255, 0, 0)  # Red for non-trunk
            if trunk_start <= row <= trunk_end:
                color = (0, 255, 0)  # Green for detected trunk
            elif row in excluded_rows:
                color = (128, 128, 128)  # Gray for excluded regions
            draw.line([(x1, row), (x2, row)], fill=color, width=1)

    vis_img.save(vis_save_path)
    print(f"Saved visualization to: {vis_save_path}")
    
    return crop_save_path