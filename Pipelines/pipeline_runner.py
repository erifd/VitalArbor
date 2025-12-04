import sam2_segmentation
import tilt_detection
import width_of_trunk
import cv2
import os
import numpy as np

photo = None
photo = str(input("Enter the complete path of the photo you want to process: "))
use_cutout = False
use_cutout_input = str(input("Do you want to use a cutout of the photo? (y/n): ")).lower()

if photo != None:
    sam2_segmentation.run_sam2_segmentation(photo)

# Get the full path that was saved
segmented_photo_path = sam2_segmentation.get_segmented_filename()

# Get trunk cutout & it's path
if use_cutout_input == 'y':
    trunk_path = width_of_trunk.get_trunk_width_analysis(segmented_photo_path)
    print(f"Checking if file exists: {os.path.exists(trunk_path)}")
    print(f"Full path: {os.path.abspath(trunk_path)}")

    result = tilt_detection.detect_tree_tilt(trunk_path)
    if result is not None:
        tilt, result_img, binary = result
        print(f"\n=== FINAL RESULT ===")
        print(f"Tree tilt angle: {tilt:.2f} degrees from vertical")
        
        # Display binary and result side by side
        display_height = 600
        aspect_ratio = binary.shape[1] / binary.shape[0]
        display_width = int(display_height * aspect_ratio)
        
        binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), (display_width, display_height))
        result_display = cv2.resize(result_img, (display_width, display_height))
        
        combined = np.hstack([binary_display, result_display])
        
        cv2.imshow('Binary | Detected Lines', combined)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Could not detect tree trunk")
else:
    # Detect tilt
    print(f"Checking if file exists: {os.path.exists(segmented_photo_path)}")
    print(f"Full path: {os.path.abspath(segmented_photo_path)}")

    result = tilt_detection.detect_tree_tilt(segmented_photo_path)
    if result is not None:
        tilt, result_img, binary = result
        print(f"\n=== FINAL RESULT ===")
        print(f"Tree tilt angle: {tilt:.2f} degrees from vertical")
        
        # Display binary and result side by side
        display_height = 600
        aspect_ratio = binary.shape[1] / binary.shape[0]
        display_width = int(display_height * aspect_ratio)
        
        binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), (display_width, display_height))
        result_display = cv2.resize(result_img, (display_width, display_height))
        
        combined = np.hstack([binary_display, result_display])
        
        cv2.imshow('Binary | Detected Lines', combined)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Could not detect tree trunk")