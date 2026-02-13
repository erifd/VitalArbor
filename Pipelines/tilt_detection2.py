import numpy as np
from PIL import Image, ImageDraw
from sklearn.decomposition import PCA
from skimage.morphology import closing, disk, remove_small_holes, remove_small_objects
import math
import os


def analyze_tree(segmented_image_path):
    """
    Analyze tree trunk tilt angle from vertical using PCA on the entire tree.
    
    Parameters:
    -----------
    segmented_image_path : str
        Path to segmented tree image
    """

    # ------------------------------------------------------
    # 1) Setup paths for saving outputs
    # ------------------------------------------------------
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(segmented_image_path))[0]
    
    # Determine output directory
    input_dir = os.path.dirname(segmented_image_path)
    if "VitalArbor" in input_dir and "Pipelines" in input_dir:
        # Navigate to VitalArbor\Segmented photos
        vital_arbor_root = input_dir.split("VitalArbor")[0] + "VitalArbor"
        output_dir = os.path.join(vital_arbor_root, "Segmented photos")
    else:
        # Save in same directory as input
        output_dir = input_dir
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # ------------------------------------------------------
    # 2) Load image
    # ------------------------------------------------------
    img = Image.open(segmented_image_path).convert("RGB")
    img_np = np.array(img)

    # ------------------------------------------------------
    # 3) Convert to grayscale and create binary mask
    # ------------------------------------------------------
    gray = np.dot(img_np[..., :3], [0.2989, 0.5870, 0.1140])
    binary_mask = gray > 0
    Image.fromarray((binary_mask * 255).astype(np.uint8)).save(
        os.path.join(output_dir, f"{base_name}_mask_debug.png")
    )

    # ------------------------------------------------------
    # 4) Mask cleaning
    # ------------------------------------------------------
    mask_clean = remove_small_holes(binary_mask, area_threshold=200)
    mask_clean = remove_small_objects(mask_clean, min_size=200)
    mask_clean = closing(mask_clean, disk(20))
    Image.fromarray((mask_clean * 255).astype(np.uint8)).save(
        os.path.join(output_dir, f"{base_name}_mask_clean.png")
    )

    # ------------------------------------------------------
    # 5) Get all tree coordinates
    # ------------------------------------------------------
    ys, xs = np.where(mask_clean == 1)
    
    if len(ys) == 0:
        raise ValueError("No tree pixels found in mask")
    
    tree_coords = np.column_stack((xs, ys))

    # ------------------------------------------------------
    # 6) PCA on entire tree from center
    # ------------------------------------------------------
    pca = PCA(n_components=2)
    pca.fit(tree_coords)
    pc1 = pca.components_[0]  # Principal axis
    pc1 = pc1 / np.linalg.norm(pc1)

    # ------------------------------------------------------
    # 7) Calculate tilt angle from vertical
    # ------------------------------------------------------
    vertical = np.array([0, -1])  # Pointing up
    dot = np.dot(pc1, vertical)
    angle_rad = math.acos(np.clip(dot, -1.0, 1.0))
    angle_deg = math.degrees(angle_rad)

    # ------------------------------------------------------
    # 8) Visualization
    # ------------------------------------------------------
    vis = img.copy()
    draw = ImageDraw.Draw(vis)

    # Draw PCA axis through center of tree
    centroid = tree_coords.mean(axis=0)
    scale = max(img_np.shape[0], img_np.shape[1])
    p1 = (centroid[0] - pc1[0] * scale, centroid[1] - pc1[1] * scale)
    p2 = (centroid[0] + pc1[0] * scale, centroid[1] + pc1[1] * scale)

    draw.line([p1, p2], fill=(255, 0, 0), width=3)
    draw.ellipse([(centroid[0]-5, centroid[1]-5),
                  (centroid[0]+5, centroid[1]+5)], fill=(255, 0, 0))

    vis.save(os.path.join(output_dir, f"{base_name}_tilt_axis.png"))

    # Return tilt angle (0° = perfectly vertical)
    return 180 - angle_deg

