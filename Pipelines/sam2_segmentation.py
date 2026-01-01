import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.widgets import Button
import os

# Get the directory paths
def run_sam2_segmentation(image_path):
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
    image = Image.open(image_path)
    image_np = np.array(image.convert("RGB"))

    # Create output directory and generate output filename
    # Get the parent directory (one level up from script_dir)
    output_dir = os.path.join(os.path.dirname(script_dir), "Segmented photos")
    os.makedirs(output_dir, exist_ok=True)

    # Extract the base filename without extension and create new name
    base_filename = os.path.splitext(os.path.basename(image_path))[0]
    output_filename = f"{base_filename}_crop_out.png"
    saved_file_path = None  # Track the actual saved file path

    print(f"Image loaded: {image_np.shape}")
    print(f"Output will be saved as: {output_filename}")
    print(f"Output directory: {output_dir}")
    print("=== Interactive Segmentation ===")
    print("MOBILE-FRIENDLY CONTROLS:")
    print("- Tap 'POS' button then tap image to ADD points")
    print("- Tap 'NEG' button then tap image to REMOVE points")
    print("- Tap 'RESET' to clear | 'SAVE' to save cutout")

    # Set the image in the predictor (encode it once)
    print("Encoding image... (this may take a moment on CPU)")
    with torch.inference_mode():
        predictor.set_image(image_np)
    print("Image encoded! Ready for segmentation.")

    # Interactive state
    positive_points = []
    negative_points = []
    current_mask = None
    point_mode = 'positive'  # Current mode: 'positive' or 'negative'

    # Create figure with compact mobile layout
    # Adjust figure size based on screen - smaller for mobile
    fig = plt.figure(figsize=(8, 10))  # Portrait orientation, compact
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05, hspace=0.15)
    
    # Compact button row at top (smaller height)
    button_height = 0.04  # Small buttons
    button_y = 0.96  # Near top
    button_width = 0.22  # Fit 4 buttons with spacing
    button_spacing = 0.24
    
    ax_btn_positive = fig.add_axes([0.02, button_y, button_width, button_height])
    ax_btn_negative = fig.add_axes([0.02 + button_spacing, button_y, button_width, button_height])
    ax_btn_reset = fig.add_axes([0.02 + 2*button_spacing, button_y, button_width, button_height])
    ax_btn_save = fig.add_axes([0.02 + 3*button_spacing, button_y, button_width, button_height])
    
    # Main image area below buttons
    ax_img = fig.add_axes([0.05, 0.5, 0.9, 0.43])  # Top half
    ax_seg = fig.add_axes([0.05, 0.05, 0.9, 0.43])  # Bottom half

    # Create compact buttons
    btn_positive = Button(ax_btn_positive, 'POS ✓', 
                         color='lightgreen', hovercolor='green')
    btn_negative = Button(ax_btn_negative, 'NEG ✗', 
                         color='lightcoral', hovercolor='red')
    btn_reset = Button(ax_btn_reset, 'RESET', 
                      color='lightgray', hovercolor='gray')
    btn_save = Button(ax_btn_save, 'SAVE', 
                     color='lightblue', hovercolor='blue')

    def update_button_colors():
        """Update button colors based on current mode"""
        if point_mode == 'positive':
            btn_positive.color = 'green'
            btn_positive.hovercolor = 'darkgreen'
            btn_negative.color = 'lightcoral'
            btn_negative.hovercolor = 'red'
        else:
            btn_positive.color = 'lightgreen'
            btn_positive.hovercolor = 'green'
            btn_negative.color = 'red'
            btn_negative.hovercolor = 'darkred'
        fig.canvas.draw_idle()

    def update_segmentation():
        """Run segmentation with current points and update display"""
        nonlocal current_mask
        
        if len(positive_points) == 0 and len(negative_points) == 0:
            # No points, just show original image
            ax_img.clear()
            ax_img.imshow(image_np)
            mode_text = "POS" if point_mode == 'positive' else "NEG"
            mode_color = 'green' if point_mode == 'positive' else 'red'
            ax_img.set_title(f"Mode: {mode_text} | Tap to add points", 
                           fontsize=10, fontweight='bold', color=mode_color)
            ax_img.axis('off')
            
            ax_seg.clear()
            ax_seg.imshow(image_np)
            ax_seg.set_title("Segmentation Result", fontsize=10, fontweight='bold')
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
        
        # Update top plot (image with points)
        ax_img.clear()
        ax_img.imshow(image_np)
        
        # Draw positive points (green stars)
        if len(positive_points) > 0:
            pos_pts = np.array(positive_points)
            ax_img.scatter(pos_pts[:, 0], pos_pts[:, 1], c='lime', s=200, marker='*', 
                        edgecolors='white', linewidths=2, zorder=10)
        
        # Draw negative points (red X)
        if len(negative_points) > 0:
            neg_pts = np.array(negative_points)
            ax_img.scatter(neg_pts[:, 0], neg_pts[:, 1], c='red', s=200, marker='X', 
                        edgecolors='white', linewidths=2, zorder=10)
        
        mode_text = "POS ✓" if point_mode == 'positive' else "NEG ✗"
        mode_color = 'green' if point_mode == 'positive' else 'red'
        ax_img.set_title(f"{len(positive_points)}✓ {len(negative_points)}✗ | Mode: {mode_text}", 
                       fontsize=10, fontweight='bold', color=mode_color)
        ax_img.axis('off')
        
        # Update bottom plot (segmentation result)
        ax_seg.clear()
        ax_seg.imshow(image_np)
        ax_seg.imshow(current_mask, alpha=0.5, cmap='jet')
        ax_seg.set_title(f"Result (score: {scores[0]:.3f})", 
                       fontsize=10, fontweight='bold')
        ax_seg.axis('off')
        
        plt.draw()

    def onclick(event):
        """Handle mouse/touch clicks on the image"""
        if event.inaxes != ax_img:
            return
        
        if event.xdata is None or event.ydata is None:
            return
        
        x, y = int(event.xdata), int(event.ydata)
        
        # Use current mode to determine point type
        if point_mode == 'positive':
            positive_points.append([x, y])
            print(f"Added POS point at ({x}, {y})")
        else:  # negative mode
            negative_points.append([x, y])
            print(f"Added NEG point at ({x}, {y})")
        
        update_segmentation()

    def set_positive_mode(event):
        """Switch to positive point mode"""
        nonlocal point_mode
        point_mode = 'positive'
        print("→ POS mode")
        update_button_colors()
        update_segmentation()

    def set_negative_mode(event):
        """Switch to negative point mode"""
        nonlocal point_mode
        point_mode = 'negative'
        print("→ NEG mode")
        update_button_colors()
        update_segmentation()

    def reset_points(event):
        """Reset all points"""
        global positive_points, negative_points, current_mask
        positive_points = []
        negative_points = []
        current_mask = None
        print("→ Reset")
        update_segmentation()

    def save_segmentation(event):
        """Save current segmentation"""
        global saved_file_path
        
        if current_mask is not None:
            # Save the cutout image with transparent background
            cutout_path = os.path.join(output_dir, output_filename)
            saved_file_path = cutout_path  # Store the actual path
            
            # Create RGBA image
            rgba_image = np.zeros((image_np.shape[0], image_np.shape[1], 4), dtype=np.uint8)
            
            # Copy RGB channels ONLY where mask is True
            for c in range(3):
                rgba_image[:, :, c] = image_np[:, :, c] * current_mask
            
            # Set alpha channel based on mask (255 where mask is True, 0 where False)
            rgba_image[:, :, 3] = (current_mask * 255).astype(np.uint8)
            
            # Find bounding box of the mask to crop
            coords = np.argwhere(current_mask)
            if len(coords) > 0:
                y_min, x_min = coords.min(axis=0)
                y_max, x_max = coords.max(axis=0)
                
                # Crop to bounding box
                rgba_cropped = rgba_image[y_min:y_max+1, x_min:x_max+1]
                
                # Save as PNG with transparency
                cutout_img = Image.fromarray(rgba_cropped, mode='RGBA')
                cutout_img.save(cutout_path)
                
                print(f"✓ Saved: {cutout_path}")
                print(f"  Size: {rgba_cropped.shape}")
                
                # Also save visualization
                viz_filename = f"{base_filename}_crop_out_contrast.png"
                viz_path = os.path.join(output_dir, viz_filename)
                
                fig_save, axes_save = plt.subplots(1, 3, figsize=(15, 5))
                
                # Original with points
                axes_save[0].imshow(image_np)
                if len(positive_points) > 0:
                    pos_pts = np.array(positive_points)
                    axes_save[0].scatter(pos_pts[:, 0], pos_pts[:, 1], c='lime', s=150, 
                                    marker='*', edgecolors='white', linewidths=2)
                if len(negative_points) > 0:
                    neg_pts = np.array(negative_points)
                    axes_save[0].scatter(neg_pts[:, 0], neg_pts[:, 1], c='red', s=150, 
                                    marker='X', edgecolors='white', linewidths=2)
                axes_save[0].set_title("Input Points", fontsize=10)
                axes_save[0].axis('off')
                
                # Segmentation overlay
                axes_save[1].imshow(image_np)
                axes_save[1].imshow(current_mask, alpha=0.5, cmap='jet')
                axes_save[1].set_title("Overlay", fontsize=10)
                axes_save[1].axis('off')
                
                # Cutout preview
                axes_save[2].imshow(rgba_cropped)
                axes_save[2].set_title("Cutout", fontsize=10)
                axes_save[2].axis('off')
                
                plt.tight_layout()
                plt.savefig(viz_path, dpi=150, bbox_inches='tight')
                plt.close(fig_save)
                
                print(f"✓ Viz saved: {viz_path}")
            else:
                print("ERROR: No mask content!")
        else:
            print("Add points first!")

    # Connect button handlers
    btn_positive.on_clicked(set_positive_mode)
    btn_negative.on_clicked(set_negative_mode)
    btn_reset.on_clicked(reset_points)
    btn_save.on_clicked(save_segmentation)

    # Connect click handler for image
    fig.canvas.mpl_connect('button_press_event', onclick)

    # Initial display and button colors
    update_button_colors()
    update_segmentation()

    plt.show()

    # Access the saved filename variable after the window is closed
    if saved_file_path:
        print(f"\nSaved: {saved_file_path}")
        return saved_file_path
    else:
        print("\nNo file saved")
        return None

def get_segmented_filename():
    """Returns the path to the saved segmented image, or None if not saved"""
    return saved_file_path