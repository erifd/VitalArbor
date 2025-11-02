import sys
from pathlib import Path

# --- Get the absolute path to the 'Image Statistics' folder ---
base_dir = Path(__file__).resolve().parent
stats_dir = base_dir / "Image Statistics"

# --- Add it to the Python import path ---
sys.path.append(str(stats_dir))

# --- Now import your function ---
from brightness import get_Brightness

# --- Use it! ---
image_path = r"2025-26 Data Links\10-21-2025\Norway Spruce photos\Norway Spruce.jfif"
full_image_path = base_dir / image_path

avg = get_Brightness(str(full_image_path), True,False, False)
print(f"Average brightness: {avg:.2f}")
