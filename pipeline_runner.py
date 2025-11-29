# import Pipelines.crop_out
import Pipelines.sam2_segmentation
# import Pipelines.tilt_detection

segmented_photo = Pipelines.sam2_segmentation.get_segmented_filename()
completed_path_segmented_photo = segmented_photo + ".png"
print(completed_path_segmented_photo)