import sam2_segmentation
import tilt_detection

photo = None
photo = str(input("Enter the complete path of the photo you want to process: "))

if photo != None:
    sam2_segmentation.run_sam2_segmentation(photo)

# Get the full path that was saved
segmented_photo_path = sam2_segmentation.get_segmented_filename()

if segmented_photo_path:
    print(f"Segmented photo path: {segmented_photo_path}")
    
    # Now run tilt detection on the segmented photo
    result = tilt_detection.detect_tree_tilt(segmented_photo_path)
    
    if result is not None:
        tilt, result_img, binary = result
        print(f"Tree tilt angle: {tilt:.2f} degrees from vertical")
    else:
        print("Could not detect tree tilt")
else:
    print("No segmented photo was saved")