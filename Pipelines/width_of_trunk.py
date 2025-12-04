import os
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

def get_trunk_width_analysis(mask_path):
    # ---------------------------------------------------
    # 1. Determine Paths Based on Your Structure
    # ---------------------------------------------------
    # Get the folder where this script is running (VitalArbor/Pipelines)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Go up one level to the root (VitalArbor)
    root_dir = os.path.dirname(script_dir)
    
    # Define the target folder (VitalArbor/Segmented photos)
    target_dir = os.path.join(root_dir, "Segmented photos")
    
    # Ensure the directory exists (just in case)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # ---------------------------------------------------
    # 2. Load binary mask
    # ---------------------------------------------------
    img = Image.open(mask_path).convert("L")
    mask = np.array(img)

    mask_bin = (mask > 127).astype(np.uint8) * 255
    h, w = mask_bin.shape

    # ---------------------------------------------------
    # 3. Compute width profile
    # ---------------------------------------------------
    widths = np.zeros(h)
    for row in range(h):
        cols = np.where(mask_bin[row] > 0)[0]
        if len(cols) > 0:
            widths[row] = cols.max() - cols.min()
        else:
            widths[row] = 0

    # ---------------------------------------------------
    # 4. Smooth & Detect Trunk
    # ---------------------------------------------------
    smoothed = savgol_filter(widths, window_length=301, polyorder=3, mode="interp")
    slope = np.abs(np.gradient(smoothed))

    stable_slope_thresh = 0.5
    max_trunk_width = np.percentile(smoothed, 50)

    stable_rows = np.where(
        (slope < stable_slope_thresh) &
        (smoothed < max_trunk_width) &
        (smoothed > 0)
    )[0]

    if len(stable_rows) == 0:
        raise ValueError("No stable trunk region detected.")

    trunk_start = stable_rows.min()
    trunk_end = stable_rows.max()
    print(f"Detected trunk band: rows {trunk_start} to {trunk_end}")

    # ---------------------------------------------------
    # 5. Crop Logic
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
    # 6. Save Logic (Using target_dir)
    # ---------------------------------------------------
    # Get the original filename (e.g. "tree1") from the path provided
    base_name = os.path.splitext(os.path.basename(mask_path))[0]
    
    # Construct new filenames
    crop_name = f"{base_name}_trunk_part.png"
    vis_name = f"{base_name}_vis_trunk.png"
    
    # Join them with the target directory path
    crop_save_path = os.path.join(target_dir, crop_name)
    vis_save_path = os.path.join(target_dir, vis_name)

    # Save cropped image
    cropped_trunk = img.crop((x_min, trunk_start, x_max, trunk_end))
    cropped_trunk.save(crop_save_path)
    print(f"Saved crop to: {crop_save_path}")

    # ---------------------------------------------------
    # 7. Visualization Logic
    # ---------------------------------------------------
    vis_img = Image.fromarray(mask_bin).convert("RGB")
    draw = ImageDraw.Draw(vis_img)

    for row in range(h):
        cols = np.where(mask_bin[row] > 0)[0]
        if len(cols) > 0:
            x1, x2 = cols.min(), cols.max()
            color = (255, 0, 0)
            if trunk_start <= row <= trunk_end:
                color = (0, 255, 0)
            draw.line([(x1, row), (x2, row)], fill=color, width=1)

    vis_img.save(vis_save_path)
    print(f"Saved visualization to: {vis_save_path}")
    
    # Optional: Plotting code removed for brevity, add back if needed
    
    return crop_save_path