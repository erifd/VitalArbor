import cv2
import numpy as np


image_path = r"C:\Users\timishg\Documents\Github\VitalArbor\2025-26 Data Links\10-21-2025\Norway Spruce photos\Norway Spruce.jfif"
image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
# Apply the Laplacian operator
laplacian = cv2.Laplacian(image, cv2.CV_64F)  # Use 64-bit float for precision

# Convert back to 8-bit (optional, for visualization)
laplacian = cv2.convertScaleAbs(laplacian)

# Display the result
cv2.imshow('Original Image', image)
cv2.imshow('Laplacian', laplacian)
cv2.waitKey(0)
cv2.destroyAllWindows()
