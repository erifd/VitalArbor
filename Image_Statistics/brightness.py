import cv2
import numpy as np
average_brightness = 0
def get_Brightness(image_path, use_hsv_and_gray, use_hsv, use_gray):
    global average_brightness
    # --- Load image ---
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    v_channel = hsv[:, :, 2]  # Value channel represents brightness
    pixel_value = gray[50, 100]
    if use_hsv_and_gray:
        use_hsv = False
        use_gray = False
        average_brightness_hsv = np.mean(v_channel)
        average_brightness_gray = np.mean(gray)
        average_brightness = (average_brightness_hsv + average_brightness_gray)/2
        return average_brighness
    elif use_hsv:
        use_hsv_and_gray = False
        use_gray = False
        average_brightness_hsv = np.mean(v_channel)
        average_brightness = average_brightness_hsv
        return average_brighness
    elif use_gray:
        use_hsv = False
        use_hsv_and_gray = False
        average_brightness_gray = np.mean(gray)
        average_brighness = average_brightness_gray
        return average_brighness


