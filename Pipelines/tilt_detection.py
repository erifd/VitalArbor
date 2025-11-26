import cv2
import sys
import numpy as np
from pathlib import Path

base_dir = Path(__file__).resolve().parent
stats_dir = base_dir / "Image Statistics"
sys.path.append(str(stats_dir))

# Use absolute path directly
image_path = Path(r"C:\Users\timishg\Documents\Github\VitalArbor\2025-26_Data_Links\10-21-2025\Norway_Spruce_photos\Norway Spruce.png")

image = cv2.imread(str(image_path))

# Add error checking
if image is None:
    print(f"Error: Could not load image from {image_path}")
    sys.exit(1)

kernel_size = (10, 10)

# Apply blur
blurred_image = cv2.blur(image, kernel_size)

# Resize to fit screen - adjust scale_percent as needed (50 = 50% of original size)
scale_percent = 25  # Change this value to resize more/less
width = int(blurred_image.shape[1] * scale_percent / 100)
height = int(blurred_image.shape[0] * scale_percent / 100)
dim = (width, height)

resized_image = cv2.resize(blurred_image, dim, interpolation=cv2.INTER_AREA)

# Display the result
cv2.imshow("Actual Image", image)
cv2.imshow("Blurred Image", resized_image)
cv2.waitKey(0)
cv2.destroyAllWindows()