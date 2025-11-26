import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt  # type: ignore
import os

# Get the directory paths
script_dir = os.path.dirname(os.path.abspath(__file__))
vitalarbor_dir = os.path.dirname(script_dir)
sam2_dir = os.path.join(vitalarbor_dir, "sam2")

# Add the inner sam2 directory to path
import sys
sam2_inner_dir = os.path.join(sam2_dir, "sam2")
if sam2_inner_dir not in sys.path:
    sys.path.insert(0, sam2_inner_dir)

# Now we can use the build_sam function
from build_sam import build_sam2  # type: ignore
from sam2_image_predictor import SAM2ImagePredictor  # type: ignore

# Load checkpoint
checkpoint_path = os.path.join(sam2_dir, "checkpoints", "sam2.1_hiera_large.pt")
model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"

# Build the model using the official build function
# Change directory temporarily so hydra can find configs
original_dir = os.getcwd()
os.chdir(sam2_inner_dir)

try:
    # Force CPU by setting device to cpu
    sam2_model = build_sam2(model_cfg, checkpoint_path, device="cpu")
    predictor = SAM2ImagePredictor(sam2_model)
finally:
    os.chdir(original_dir)

# Load your image
image_path = r"C:\Users\timishg\Documents\Github\VitalArbor\2025-26_Data_Links\10-21-2025\Norway_Spruce_photos\Norway Spruce.png"
image = Image.open(image_path)
image_np = np.array(image.convert("RGB"))

print(f"Image loaded: {image_np.shape}")
print("=== Interactive Segmentation ===")
print("Left click: Add positive point (include in mask)")
print("Right click: Add negative point (exclude from mask)")
print("Press 'r' to reset points")
print("Press 's' to save current segmentation (cutout with transparent background)")
print("Close window when done")

# Set the image in the predictor (encode it once)
print("Encoding image... (this may take a moment on CPU)")
with torch.inference_mode():
    predictor.set_image(image_np)
print("Image encoded! Ready for segmentation.")

# Interactive state
positive_points = []
negative_points = []
current_mask = None

# Create figure with subplots
fig, axes = plt.subplots(1, 2, figsize=(16, 8))
ax_img = axes[0]
ax_seg = axes[1]

def update_segmentation():
    """Run segmentation with current points and update display"""
    global current_mask
    
    if len(positive_points) == 0 and len(negative_points) == 0:
        # No points, just show original image
        ax_img.clear()
        ax_img.imshow(image_np)
        ax_img.set_title("Original Image (click to add points)")
        ax_img.axis('off')
        
        ax_seg.clear()
        ax_seg.imshow(image_np)
        ax_seg.set_title("Segmentation Result")
        ax_seg.axis('off')
        
        plt.draw()
        return
    
    # Combine all points
    all_points = positive_points + negative_points
    all_labels = [1] * len(positive_points) + [0] * len(negative_points)
    
    if len(all_points) == 0:
        return
    
    input_points = np.array(all_points)
    input_labels = np.array(all_labels)
    
    # Run prediction
    with torch.inference_mode():
        masks, scores, logits = predictor.predict(
            point_coords=input_points,
            point_labels=input_labels,
            multimask_output=False  # Single best mask
        )
    
    current_mask = masks[0]
    
    # Update left plot (image with points)
    ax_img.clear()
    ax_img.imshow(image_np)
    
    # Draw positive points (green)
    if len(positive_points) > 0:
        pos_pts = np.array(positive_points)
        ax_img.scatter(pos_pts[:, 0], pos_pts[:, 1], c='lime', s=200, marker='*', 
                      edgecolors='white', linewidths=2, label='Include')
    
    # Draw negative points (red)
    if len(negative_points) > 0:
        neg_pts = np.array(negative_points)
        ax_img.scatter(neg_pts[:, 0], neg_pts[:, 1], c='red', s=200, marker='X', 
                      edgecolors='white', linewidths=2, label='Exclude')
    
    ax_img.set_title(f"Points: {len(positive_points)} positive, {len(negative_points)} negative")
    ax_img.axis('off')
    if len(positive_points) > 0 or len(negative_points) > 0:
        ax_img.legend(loc='upper right')
    
    # Update right plot (segmentation result)
    ax_seg.clear()
    ax_seg.imshow(image_np)
    ax_seg.imshow(current_mask, alpha=0.5, cmap='jet')
    ax_seg.set_title(f"Segmentation (score: {scores[0]:.3f})")
    ax_seg.axis('off')
    
    plt.draw()

def onclick(event):
    """Handle mouse clicks"""
    if event.inaxes != ax_img:
        return
    
    if event.xdata is None or event.ydata is None:
        return
    
    x, y = int(event.xdata), int(event.ydata)
    
    if event.button == 1:  # Left click - positive point
        positive_points.append([x, y])
        print(f"Added positive point at ({x}, {y})")
    elif event.button == 3:  # Right click - negative point
        negative_points.append([x, y])
        print(f"Added negative point at ({x}, {y})")
    
    update_segmentation()

def onkey(event):
    """Handle keyboard presses"""
    global positive_points, negative_points, current_mask
    
    if event.key == 'r':  # Reset
        positive_points = []
        negative_points = []
        current_mask = None
        print("Reset all points")
        update_segmentation()
    
    elif event.key == 's':  # Save
        if current_mask is not None:
            # Save the cutout image with transparent background
            cutout_path = os.path.join(script_dir, "segmented_img.png")
            
            # Create RGBA image
            rgba_image = np.zeros((image_np.shape[0], image_np.shape[1], 4), dtype=np.uint8)
            
            # Copy RGB channels
            rgba_image[:, :, :3] = image_np
            
            # Set alpha channel based on mask (255 where mask is True, 0 where False)
            rgba_image[:, :, 3] = (current_mask * 255).astype(np.uint8)
            
            # Save as PNG with transparency
            cutout_img = Image.fromarray(rgba_image, mode='RGBA')
            cutout_img.save(cutout_path)
            
            print(f"✓ Saved cutout image to: {cutout_path}")
            
            # Also save visualization
            viz_path = os.path.join(script_dir, "contrast_img.png")
            
            fig_save, axes_save = plt.subplots(1, 3, figsize=(18, 6))
            
            # Original with points
            axes_save[0].imshow(image_np)
            if len(positive_points) > 0:
                pos_pts = np.array(positive_points)
                axes_save[0].scatter(pos_pts[:, 0], pos_pts[:, 1], c='lime', s=200, 
                                   marker='*', edgecolors='white', linewidths=2)
            if len(negative_points) > 0:
                neg_pts = np.array(negative_points)
                axes_save[0].scatter(neg_pts[:, 0], neg_pts[:, 1], c='red', s=200, 
                                   marker='X', edgecolors='white', linewidths=2)
            axes_save[0].set_title("Input Points")
            axes_save[0].axis('off')
            
            # Segmentation overlay
            axes_save[1].imshow(image_np)
            axes_save[1].imshow(current_mask, alpha=0.5, cmap='jet')
            axes_save[1].set_title("Segmentation Overlay")
            axes_save[1].axis('off')
            
            # Cutout preview (on white background for visualization)
            axes_save[2].imshow(rgba_image)
            axes_save[2].set_title("Cutout (saved with transparency)")
            axes_save[2].axis('off')
            
            plt.tight_layout()
            plt.savefig(viz_path, dpi=150, bbox_inches='tight')
            plt.close(fig_save)
            
            print(f"✓ Saved visualization to: {viz_path}")
        else:
            print("No segmentation to save yet - add some points first!")

# Connect event handlers
fig.canvas.mpl_connect('button_press_event', onclick)
fig.canvas.mpl_connect('key_press_event', onkey)

# Initial display
update_segmentation()

plt.tight_layout()
plt.show()