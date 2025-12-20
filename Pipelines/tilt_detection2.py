import numpy as np
from PIL import Image, ImageDraw
from sklearn.decomposition import PCA
from skimage.morphology import skeletonize, closing, square, remove_small_holes, remove_small_objects
import math


def analyze_tree(segmented_image_path):

    # ------------------------------------------------------
    # 1) Load image
    # ------------------------------------------------------
    img = Image.open(segmented_image_path).convert("RGB")
    img_np = np.array(img)

    # ------------------------------------------------------
    # 2) Convert to grayscale
    # ------------------------------------------------------
    gray = np.dot(img_np[..., :3], [0.2989, 0.5870, 0.1140])

    # Raw mask: nonzero = tree
    binary_mask = gray > 0
    Image.fromarray((binary_mask * 255).astype(np.uint8)).save("mask_debug.png")

    # ------------------------------------------------------
    # 3) Mask cleaning to prevent skeleton fragmentation
    # ------------------------------------------------------
    # Fill small holes inside tree silhouettes
    mask_clean = remove_small_holes(binary_mask, area_threshold=200)

    # Remove tiny speckles outside tree
    mask_clean = remove_small_objects(mask_clean, min_size=200)

    # Close small gaps in trunk outline
    mask_clean = closing(mask_clean, square(40))

    # Get (x, y) coordinates of mask
    ys, xs = np.where(binary_mask == 1)
    mask_coords = np.column_stack((xs, ys))

    Image.fromarray((mask_clean * 255).astype(np.uint8)).save("mask_clean.png")

    # ------------------------------------------------------
    # 4) PCA on mask
    # ------------------------------------------------------
    pca = PCA(n_components=2)
    pca.fit(mask_coords)
    pc1 = pca.components_[0]
    pc1 = pc1 / np.linalg.norm(pc1)

    # ------------------------------------------------------
    # 5) Angle from vertical
    # ------------------------------------------------------
    vertical = np.array([0, -1])
    dot = np.dot(pc1, vertical)
    angle_rad = math.acos(np.clip(dot, -1.0, 1.0))
    angle_deg = math.degrees(angle_rad)

    # ------------------------------------------------------
    # 6) Visualization (axis plotted on original image)
    # ------------------------------------------------------
    vis = img.copy()
    draw = ImageDraw.Draw(vis)

    # # Draw skeleton in green
    # for x, y in coords:
    #     draw.point((x, y), fill=(0, 255, 0))

    # PCA line in red
    centroid = mask_coords.mean(axis=0)
    scale = max(img_np.shape[0], img_np.shape[1])
    p1 = (centroid[0] - pc1[0] * scale, centroid[1] - pc1[1] * scale)
    p2 = (centroid[0] + pc1[0] * scale, centroid[1] + pc1[1] * scale)

    draw.line([p1, p2], fill=(255, 0, 0), width=3)
    draw.ellipse([(centroid[0]-4, centroid[1]-4),
                  (centroid[0]+4, centroid[1]+4)], fill=(255,0,0))

    vis.save("tree_with_axis.png")

    return 180 - angle_deg

