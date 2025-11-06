import sys
from pathlib import Path

# --- Base directory: the folder containing this script (VitalArbor) ---
base_dir = Path(__file__).resolve().parent

# --- Path to 'Image Statistics' folder ---
stats_dir = base_dir / "Image Statistics"

# --- Add 'Image Statistics' to import path ---
sys.path.append(str(stats_dir))

# --- Import function ---
from Image_Statistics.brightness import get_Brightness


# --- Build the full image path (relative to base folder) ---
image_path = base_dir / r"C:\Users\timishg\Documents\Github\VitalArbor\2025-26_Data_Links\10-21-2025\Norway_Spruce_photos\Norway Spruce.png"

# --- Call the function ---
avg = get_Brightness(str(image_path), True, False, False)

print(f"Average brightness: {avg:.2f} — hello")
