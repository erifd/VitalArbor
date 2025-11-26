import cv2
import sys
import numpy as np
from pathlib import Path

base_dir = Path(__file__).resolve().parent
stats_dir = base_dir / "Image Statistics"
sys.path.append(str(stats_dir))

# Use absolute path directly
image_path = Path(r"<insert path>")

image = cv2.imread(str(image_path))

# Add error checking
if image is None:
    print(f"Error: Could not load image from {image_path}")
    sys.exit(1)

# Convert to grayscale for easier processing
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Find all non-black pixels (threshold to handle near-black pixels too)
_, thresh = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

# Find contours of non-black regions
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Get the bounding box of the largest contour (the actual tree image)
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Crop the image to remove black borders and white bars
    cropped_image = image[y:y+h, x:x+w]
    
    kernel_size = (10, 10)
    
    # Apply blur to cropped image
    
    # Resize to fit screen
    scale_percent = 50
    width = int(cropped_image.shape[1] * scale_percent / 100)
    height = int(cropped_image.shape[0] * scale_percent / 100)
    dim = (width, height)
    
    resized_image = cv2.resize(cropped_image, dim, interpolation=cv2.INTER_AREA)
    
    # Display the result
    cv2.imshow("Cropped and Blurred Image", resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # Optional: Save the cropped image
    output_path = base_dir / "cropped_norway_spruce.png"
    cv2.imwrite(str(output_path), cropped_image)
    print(f"Cropped image saved to: {output_path}")
else:
    print("No valid content found in image")