import cv2
import numpy as np

# --- Use your exact image path ---
image_path = r"C:\Users\timishg\Documents\Github\VitalArbor\2025-26 Data Links\10-21-2025\Norway Spruce photos\Norway Spruce.jfif"

# --- Load image ---
image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"Image not found at path: {image_path}")

# --- Convert to HSV color space ---
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

# --- Extract the V (brightness) channel ---
v_channel = hsv[:, :, 2]  # Value channel represents brightness
pixel_value = gray[50, 100]
print(f"Pixel (50,100) brightness: {pixel_value}")

# --- Compute average brightness ---
average_brightness_hsv = np.mean(v_channel)
average_brightness_gray = np.mean(gray)
average_brightness = (average_brightness_hsv + average_brightness_gray)/2

# --- Print results ---
print(f"Average brightness (hsv) (0–255 scale): {average_brightness_hsv:.2f}")
print(f"Average brightness (hsv) (0–1 normalized): {average_brightness_hsv / 255:.3f}")
print(f"Average brightness (gray): {average_brightness_gray:.2f}")
print(f"Average brightness: {average_brightness:.2f}")


# --- Optional visualization ---
cv2.imshow("Original", image)
cv2.imshow("Brightness (V Channel)", v_channel)
cv2.waitKey(0)
cv2.destroyAllWindows()
