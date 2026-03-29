import sys
# Add the parent directory of sam3 folder to Python path
sam3_path = r"C:\Users\family_2\Documents\GitHub\VitalArbor"  
sys.path.insert(0, sam3_path)
import cv2
import numpy as np
import os
from pathlib import Path
from sam3.model_builder import build_sam3_video_predictor


def segment_tree_trunk_from_video(video_path, text_prompt, output_path):
    """
    Segment tree trunk from video using SAM3 and save as new video
    
    Args:
        video_path: Path to input video file
        text_prompt: Text description of what to segment (e.g., "tree trunk")
        output_path: Path for output segmented video
    
    Returns:
        str: Path to segmented video file
    """
    print(f"\n{'='*70}")
    print("TREE TRUNK SEGMENTATION WITH SAM3")
    print(f"{'='*70}")
    print(f"Input video: {video_path}")
    print(f"Text prompt: '{text_prompt}'")
    print(f"Output video: {output_path}")
    
    # Load SAM3 model
    print("\nLoading SAM3 model...")
    video_predictor = build_sam3_video_predictor()
    print("✓ SAM3 model loaded")
    
    # Step 1: Start SAM3 session
    print("\n[1/4] Starting SAM3 session...")
    session_response = video_predictor.handle_request(
        request=dict(
            type="start_session",
            resource_path=video_path,
        )
    )
    session_id = session_response["session_id"]
    print(f"✓ Session started: {session_id}")
    
    # Step 2: Add text prompt for tree trunk segmentation
    print(f"\n[2/4] Segmenting with prompt: '{text_prompt}'...")
    prompt_response = video_predictor.handle_request(
        request=dict(
            type="add_prompt",
            session_id=session_id,
            frame_index=0,
            text=text_prompt,
        )
    )
    
    # Get segmentation outputs
    outputs = prompt_response["outputs"]
    print(f"✓ Segmentation complete for {len(outputs)} frames")
    
    # Step 3: Create segmented video
    print("\n[3/4] Creating segmented video...")
    create_segmented_video(video_path, outputs, output_path)
    
    # Step 4: Cleanup session
    print("\n[4/4] Cleaning up...")
    video_predictor.handle_request(
        request=dict(
            type="end_session",
            session_id=session_id,
        )
    )
    
    print(f"\n{'='*70}")
    print("✓ SEGMENTATION COMPLETE!")
    print(f"{'='*70}")
    print(f"Segmented video saved: {os.path.abspath(output_path)}")
    print(f"{'='*70}\n")
    
    return output_path


def create_segmented_video(video_path, outputs, output_path):
    """
    Create video with segmented tree trunk
    
    Args:
        video_path: Original video path
        outputs: Segmentation masks from SAM3
        output_path: Where to save output video
    """
    # Open original video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"  Video properties:")
    print(f"    - Resolution: {width}x{height}")
    print(f"    - FPS: {fps}")
    print(f"    - Total frames: {total_frames}")
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_idx = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Get mask for current frame
        if frame_idx < len(outputs):
            mask = outputs[frame_idx]
            segmented_frame = apply_mask_to_frame(frame, mask)
        else:
            segmented_frame = frame
        
        # Write frame to output video
        out.write(segmented_frame)
        
        frame_idx += 1
        print(f"  Processing frame {frame_idx}/{total_frames}", end='\r')
    
    print(f"\n  ✓ Processed {frame_idx} frames")
    
    # Release resources
    cap.release()
    out.release()


def apply_mask_to_frame(frame, mask):
    """
    Apply segmentation mask to frame
    
    Args:
        frame: Original BGR frame
        mask: Segmentation mask from SAM3
    
    Returns:
        Segmented frame with tree trunk isolated on black background
    """
    # Extract mask array from SAM3 output format
    if isinstance(mask, dict):
        mask = mask.get('segmentation', mask)
    
    # Ensure mask is 2D
    if len(mask.shape) > 2:
        mask = mask[:, :, 0] if mask.shape[2] == 1 else mask
    
    # Resize mask to match frame if needed
    if mask.shape[:2] != frame.shape[:2]:
        mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
    
    # Create binary mask
    binary_mask = (mask > 0.5).astype(np.uint8)
    
    # Expand mask to 3 channels
    binary_mask_3ch = np.stack([binary_mask] * 3, axis=-1)
    
    # Apply mask: black background with trunk only
    segmented = frame * binary_mask_3ch
    
    return segmented


def get_user_input():
    """
    Get video path, text prompt, and output path from user
    
    Returns:
        tuple: (video_path, text_prompt, output_path)
    """
    print("\n" + "="*70)
    print("SAM3 TREE TRUNK SEGMENTATION")
    print("="*70)
    
    # Get video path
    while True:
        print("\n📹 INPUT VIDEO")
        video_path = input("Enter the path to your video file: ").strip().strip('"\'')
        
        if os.path.exists(video_path):
            print(f"✓ Video found: {video_path}")
            break
        else:
            print(f"❌ File not found: {video_path}")
            print("Please check the path and try again.")
    
    # Get text prompt
    print("\n💬 SEGMENTATION PROMPT")
    print("Examples: 'tree trunk', 'oak tree', 'bark', 'wooden post'")
    text_prompt = "tree trunk" # sets the text prompt. TODO: make this better, and more specific after reviewing videos
    # Get output path
    print("\n💾 OUTPUT VIDEO")
    default_output = f"{os.path.splitext(os.path.basename(video_path))[0]}_segmented.mp4"
    print(f"Default output name: {default_output}")
    output_path = input(f"Enter output path (press Enter for default): ").strip().strip('"\'')
    
    if not output_path:
        output_path = default_output
        print(f"Using default: {output_path}")
    else:
        # Ensure .mp4 extension
        if not output_path.endswith('.mp4'):
            output_path += '.mp4'
        print(f"✓ Output will be saved as: {output_path}")
    
    return video_path, text_prompt, output_path


def main():
    """
    Main interactive pipeline for SAM3 tree trunk segmentation from video 
    """
    try:
        # Get user input
        video_path, text_prompt, output_path = get_user_input()
        
        # Confirm before processing
        print(f"\n{'='*70}")
        print("READY TO START")
        print(f"{'='*70}")
        print(f"Input:  {video_path}")
        print(f"Prompt: '{text_prompt}'")
        print(f"Output: {output_path}")
        print(f"{'='*70}")
        
        proceed = input("\nProceed with segmentation? (y/n): ").strip().lower()
        
        if proceed != 'y':
            print("❌ Cancelled by user")
            return
        
        # Run segmentation
        result = segment_tree_trunk_from_video(video_path, text_prompt, output_path)
        
        print(f"\n✅ SUCCESS!")
        print(f"Segmented video saved to: {result}")
        
    except KeyboardInterrupt:
        print("\n\n⊘ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    return result


if __name__ == "__main__":
    main()