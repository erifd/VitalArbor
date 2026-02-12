import cv2
import os
import subprocess
import glob
import shutil
import tempfile
from pathlib import Path


def extract_frames_from_video(video_path, output_dir, interval_ms=500, max_frames=500, blur_threshold=150):
    """
    Extract high-quality frames from video for 3D reconstruction
    Frames extracted every interval_ms milliseconds
    
    Args:
        video_path: Path to input video file
        output_dir: Directory to save extracted frames
        interval_ms: Milliseconds between frames (default: 500ms = 0.5 seconds)
        max_frames: Maximum number of frames to extract
        blur_threshold: Sharpness threshold (higher = stricter, 150 is good for outdoor scans)
    
    Returns:
        tuple: (list of frame paths, frames directory)
    """
    print(f"\n{'='*70}")
    print("EXTRACTING FRAMES")
    print(f"{'='*70}")
    print(f"Video: {video_path}")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file: {video_path}")
        return [], None
    
    # Get video properties
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / video_fps
    
    print(f"\nVideo Properties:")
    print(f"  - Resolution: {width}x{height}")
    print(f"  - FPS: {video_fps:.2f}")
    print(f"  - Total frames: {total_frames}")
    print(f"  - Duration: {duration:.2f} seconds")
    
    # Calculate frame interval based on milliseconds
    frames_per_interval = int((interval_ms / 1000.0) * video_fps)
    estimated_frames = min(int(duration / (interval_ms / 1000.0)), max_frames)
    
    print(f"\nExtraction Settings:")
    print(f"  - Interval: {interval_ms}ms (every {frames_per_interval} frames)")
    print(f"  - Blur threshold: {blur_threshold}")
    print(f"  - Estimated output: ~{estimated_frames} frames")
    print(f"  - Max frames: {max_frames}")
    
    frame_paths = []
    frame_count = 0
    saved_count = 0
    skipped_blurry = 0
    
    print(f"\nProcessing...")
    
    while cap.isOpened() and saved_count < max_frames:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Save frame at specified interval
        if frame_count % frames_per_interval == 0:
            # Check if frame is sharp enough
            sharpness = calculate_sharpness(frame)
            
            if sharpness > blur_threshold:
                frame_filename = f"frame_{saved_count:04d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # Save with high quality
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                frame_paths.append(frame_path)
                saved_count += 1
                
                print(f"  ✓ Saved: {saved_count}/{estimated_frames} frames (sharpness: {sharpness:.0f})", end='\r')
            else:
                skipped_blurry += 1
        
        frame_count += 1
    
    cap.release()
    
    print(f"\n\n{'='*70}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Saved: {saved_count} sharp frames")
    print(f"⊘ Skipped: {skipped_blurry} blurry frames")
    print(f"📁 Location: {os.path.abspath(output_dir)}")
    print(f"{'='*70}\n")
    
    return frame_paths, output_dir


def calculate_sharpness(frame):
    """
    Calculate frame sharpness using Laplacian variance
    Higher values = sharper image
    
    Args:
        frame: OpenCV image (BGR)
    
    Returns:
        float: Sharpness score
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var


def run_meshroom_batch(images_dir, output_dir="./meshroom_output", meshroom_path=None):
    """
    Run Meshroom photogrammetry processing
    
    Args:
        images_dir: Directory containing input images
        output_dir: Where to save output 3D model
        meshroom_path: Path to Meshroom batch executable
    
    Returns:
        str: Path to output mesh file (or None if failed)
    """
    print(f"\n{'='*70}")
    print("RUNNING MESHROOM PHOTOGRAMMETRY")
    print(f"{'='*70}")
    
    if not meshroom_path:
        print("❌ No Meshroom path provided")
        return None
    
    # Verify Meshroom exists
    if not os.path.exists(meshroom_path):
        print(f"❌ Meshroom not found at: {meshroom_path}")
        return None
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Count images
    image_count = len([f for f in os.listdir(images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
    
    print(f"\nInput:")
    print(f"  - Images: {image_count}")
    print(f"  - Location: {os.path.abspath(images_dir)}")
    print(f"\nOutput:")
    print(f"  - Location: {os.path.abspath(output_dir)}")
    
    # Build command
    cmd = [
        meshroom_path,
        "--input", os.path.abspath(images_dir),
        "--output", os.path.abspath(output_dir)
    ]
    
    print(f"\nEstimated processing time:")
    print(f"  - {image_count} images: ~{image_count * 0.5:.0f}-{image_count * 2:.0f} minutes")
    print(f"  - This depends on your CPU/GPU performance")
    
    print(f"\n⏳ Processing started... Please wait...")
    print(f"{'='*70}\n")
    
    try:
        # Run Meshroom with live output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Show progress
        for line in process.stdout:
            if line.strip():
                print(f"  {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print(f"\n{'='*70}")
            print("✓ MESHROOM PROCESSING COMPLETE")
            print(f"{'='*70}\n")
            
            # Find output mesh
            mesh_path = find_meshroom_output(output_dir)
            return mesh_path
        else:
            print(f"\n❌ Meshroom failed with error code {process.returncode}")
            stderr = process.stderr.read()
            if stderr:
                print(f"Error details: {stderr}")
            return None
        
    except Exception as e:
        print(f"\n❌ Error running Meshroom: {e}")
        return None


def find_meshroom_output(output_dir):
    """
    Find the generated mesh file in Meshroom output
    
    Args:
        output_dir: Meshroom output directory
    
    Returns:
        str: Path to mesh file or None
    """
    # Meshroom typically outputs to MeshroomCache/Texturing/
    search_patterns = [
        os.path.join(output_dir, "MeshroomCache", "Texturing", "**", "*.obj"),
        os.path.join(output_dir, "MeshroomCache", "Meshing", "**", "*.obj"),
        os.path.join(output_dir, "**", "*.obj")
    ]
    
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        if files:
            mesh_path = files[0]
            file_size = os.path.getsize(mesh_path) / (1024 * 1024)  # MB
            print(f"✓ Found mesh: {os.path.basename(mesh_path)}")
            print(f"  - Size: {file_size:.2f} MB")
            print(f"  - Path: {mesh_path}")
            return mesh_path
    
    print(f"⚠️  Could not find output mesh automatically")
    print(f"Check directory: {os.path.abspath(output_dir)}")
    return None


def convert_obj_to_stl(obj_path, stl_output_path):
    """
    Convert OBJ file to STL format
    
    Args:
        obj_path: Input OBJ file
        stl_output_path: Output STL file path
    
    Returns:
        str: Path to STL file or None
    """
    try:
        import trimesh
        
        print(f"\nConverting to STL format...")
        
        # Load mesh
        mesh = trimesh.load(obj_path)
        
        # Get mesh info
        print(f"  - Vertices: {len(mesh.vertices):,}")
        print(f"  - Faces: {len(mesh.faces):,}")
        
        # Export as STL
        mesh.export(stl_output_path)
        
        stl_size = os.path.getsize(stl_output_path) / (1024 * 1024)
        print(f"✓ STL file created: {os.path.basename(stl_output_path)}")
        print(f"  - Size: {stl_size:.2f} MB")
        print(f"  - Path: {stl_output_path}")
        
        return stl_output_path
        
    except ImportError:
        print("\n⚠️  trimesh library not installed")
        print("Install with: pip install trimesh")
        print(f"\nYou can still use the OBJ file at: {obj_path}")
        return None
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None


def get_user_input():
    """
    Get video path and Meshroom path from user
    
    Returns:
        tuple: (video_path, meshroom_path, output_stl_path)
    """
    print("\n" + "="*70)
    print("VIDEO TO 3D MODEL CONVERTER")
    print("Extracts frames every 500ms for optimal 3D reconstruction")
    print("="*70)
    
    # Get video path
    while True:
        print("\n📹 VIDEO FILE")
        video_path = input("Enter the path to your video file: ").strip().strip('"\'')
        
        if os.path.exists(video_path):
            print(f"✓ Video found: {video_path}")
            break
        else:
            print(f"❌ File not found: {video_path}")
            print("Please check the path and try again.")
    
    # Get output STL path
    print("\n💾 OUTPUT STL FILE")
    default_name = os.path.splitext(os.path.basename(video_path))[0] + ".stl"
    output_stl = input(f"Enter output STL filename (or press Enter for '{default_name}'): ").strip().strip('"\'')
    
    if not output_stl:
        output_stl = default_name
    
    if not output_stl.endswith('.stl'):
        output_stl += '.stl'
    
    print(f"✓ STL will be saved as: {output_stl}")
    
    # Get Meshroom path
    print("\n🔧 MESHROOM SETUP")
    print("Meshroom is required for 3D reconstruction.")
    print("Download from: https://alicevision.org/")
    
    while True:
        print("\n")
        meshroom_path = input("Enter the path to meshroom_batch executable: ").strip().strip('"\'')
        
        if os.path.exists(meshroom_path):
            print(f"✓ Meshroom found: {meshroom_path}")
            break
        else:
            print(f"❌ File not found: {meshroom_path}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Cannot proceed without Meshroom. Exiting.")
                exit(1)
    
    return video_path, meshroom_path, output_stl


def main():
    """
    Main pipeline using temporary directory that gets deleted after STL is created
    """
    # Get user input
    video_path, meshroom_path, output_stl_path = get_user_input()
    
    # Create temporary directory for all intermediate files
    temp_dir = tempfile.mkdtemp(prefix="video_to_3d_")
    print(f"\n📁 Using temporary directory: {temp_dir}")
    print("(This will be deleted after STL is created)")
    
    try:
        frames_dir = os.path.join(temp_dir, "frames")
        meshroom_dir = os.path.join(temp_dir, "meshroom_output")
        
        # Step 1: Extract frames every 500ms
        print(f"\n{'='*70}")
        print("STEP 1: EXTRACTING FRAMES (500ms intervals)")
        print(f"{'='*70}")
        
        frame_paths, frames_directory = extract_frames_from_video(
            video_path,
            output_dir=frames_dir,
            interval_ms=500,  # Extract frame every 500 milliseconds
            max_frames=500,
            blur_threshold=150
        )
        
        if not frame_paths:
            print("❌ No frames extracted. Exiting.")
            return
        
        # Step 2: Run Meshroom
        print(f"\n{'='*70}")
        print("STEP 2: 3D RECONSTRUCTION WITH MESHROOM")
        print(f"{'='*70}")
        
        mesh_obj = run_meshroom_batch(frames_directory, meshroom_dir, meshroom_path)
        
        if not mesh_obj:
            print("❌ Meshroom processing failed. Exiting.")
            return
        
        # Step 3: Convert to STL
        print(f"\n{'='*70}")
        print("STEP 3: CONVERTING TO STL")
        print(f"{'='*70}")
        
        mesh_stl = convert_obj_to_stl(mesh_obj, output_stl_path)
        
        if not mesh_stl:
            print("❌ STL conversion failed. Exiting.")
            return
        
        # Final summary
        print(f"\n{'='*70}")
        print("PROCESSING COMPLETE!")
        print(f"{'='*70}")
        print(f"\n✓ STL file created: {os.path.abspath(output_stl_path)}")
        stl_size = os.path.getsize(output_stl_path) / (1024 * 1024)
        print(f"  - Size: {stl_size:.2f} MB")
        print(f"{'='*70}\n")
        
    finally:
        # Clean up temporary directory
        print(f"\n🗑️  Cleaning up temporary files...")
        try:
            shutil.rmtree(temp_dir)
            print(f"✓ Temporary directory deleted: {temp_dir}")
        except Exception as e:
            print(f"⚠️  Could not delete temporary directory: {e}")
            print(f"You may manually delete: {temp_dir}")


if __name__ == "__main__":
    main()