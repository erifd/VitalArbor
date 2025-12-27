import sam2_segmentation
import tilt_detection
import tilt_detection2
import combo_tilt_detection
import width_of_trunk
import risk_score
import tree_species_classification as tsp
import API_Key_storage
import diagnose
import cv2
import os
import numpy as np
import sys

def run_tilt_detection(analysis_path, detection_method):
    """
    Run the selected tilt detection method on the given image path.
    Returns: (tilt, result_img, binary, trunk_lines_count) or None if failed
    """
    if detection_method == "2":
        # Use PCA method
        print("\n=== Running PCA Tilt Detection ===")
        result = tilt_detection2.analyze_tree(analysis_path)
        
        if result is not None:
            if isinstance(result, tuple):
                tilt, result_img, binary, trunk_lines_count = result
            else:
                tilt = float(result)
                result_img = None
                binary = None
                trunk_lines_count = 0
            return (tilt, result_img, binary, trunk_lines_count)
        return None
    
    elif detection_method == "3":
        # Use combined method
        print("\n=== Running Combined Tilt Detection (PCA + Lines) ===")
        result = combo_tilt_detection.detect_tree_tilt_combined(
            analysis_path,
            pca_weight=0.6,
            rotation_angles=[-10, -5, 0, 5, 10]
        )
        return result
    
    else:
        # Use original method
        print("\n=== Running Original Tilt Detection (Line Intersection) ===")
        result = tilt_detection.detect_tree_tilt(analysis_path)
        return result

def display_and_save_results(tilt, result_img, binary, trunk_lines_count, analysis_path, method_name):
    """Display and save tilt detection results."""
    print(f"\n=== FINAL RESULT ===")
    print(f"{method_name} tilt angle: {tilt:.2f}° from vertical")
    print(f"Trunk lines detected: {trunk_lines_count}")
    
    # Only display if we have images
    if result_img is not None and binary is not None:
        # Display binary and result side by side
        display_height = 600
        aspect_ratio = binary.shape[1] / binary.shape[0]
        display_width = int(display_height * aspect_ratio)
        
        binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), 
                                    (display_width, display_height))
        result_display = cv2.resize(result_img, (display_width, display_height))
        
        combined_display = np.hstack([binary_display, result_display])
        
        window_name = f'Binary | {method_name} Detection'
        cv2.imshow(window_name, combined_display)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Save visualization
        output_filename = f"tilt_{method_name.lower().replace(' ', '_')}_{os.path.basename(analysis_path)}"
        cv2.imwrite(output_filename, result_img)
        print(f"\nDetailed visualization saved to: {output_filename}")
    else:
        print("(Note: Method returned angle only, no visualization available)")

def main():
    """Main function to run tree analysis pipeline with tilt detection options."""
    
    # Get photo paths from user
    # Check if we have command-line arguments from Java
    if len(sys.argv) >= 6:
        photo = sys.argv[1]
        tilt_photo = sys.argv[2]
        backup = sys.argv[3]
        use_cutout_input = sys.argv[4]
        detection_method = sys.argv[5]
    else:
        photo = str(input("Enter the complete path of the photo you want to process for tree classification: ")).strip()
        tilt_photo = str(input("Enter the complete path of the photo you want to process for tilt detection: ")).strip()
        backup = str(input("Enter the complete path of the photo you want to process for backup tilt detection (aka a trunk to ground image): ")).strip()
        use_cutout_input = str(input("Do you want to use a cutout of the photo? (y/n): ")).lower().strip()
    
        # Ask which tilt detection method to use
        print("\nTilt Detection Methods:")
        print("1. Original (Line Intersection only)")
        print("2. PCA Method")
        print("3. Combined (PCA + Line Intersection)")
        detection_method = str(input("Choose detection method (1, 2, or 3): ")).strip()
    
    # Initialize paths
    segmented_photo_path = None
    segmented_classification_path = None
    segmented_backup_path = None
    
    # Run SAM2 segmentation and store results
    print("\n=== Running SAM2 Segmentation ===")
    
    if tilt_photo and os.path.exists(tilt_photo):
        print(f"Segmenting tilt photo: {tilt_photo}")
        sam2_segmentation.run_sam2_segmentation(tilt_photo)
        segmented_photo_path = sam2_segmentation.get_segmented_filename()
        print(f"Tilt segmentation saved to: {segmented_photo_path}")
    else:
        print(f"Warning: Tilt photo not found or not provided: {tilt_photo}")
    
    if photo and os.path.exists(photo):
        print(f"Segmenting classification photo: {photo}")
        sam2_segmentation.run_sam2_segmentation(photo)
        segmented_classification_path = sam2_segmentation.get_segmented_filename()
        print(f"Classification segmentation saved to: {segmented_classification_path}")
    else:
        print(f"Warning: Classification photo not found or not provided: {photo}")
    
    if backup and os.path.exists(backup):
        print(f"Segmenting backup photo: {backup}")
        sam2_segmentation.run_sam2_segmentation(backup)
        segmented_backup_path = sam2_segmentation.get_segmented_filename()
        print(f"Backup segmentation saved to: {segmented_backup_path}")
    else:
        print(f"Warning: Backup photo not found or not provided: {backup}")
    
    # Determine which image to analyze for tilt detection
    analysis_path = None
    
    if segmented_photo_path and os.path.exists(segmented_photo_path):
        if use_cutout_input == 'y':
            # Get trunk cutout
            print("\n=== Creating Trunk Cutout ===")
            trunk_path = width_of_trunk.get_trunk_width_analysis(segmented_photo_path)
            if trunk_path and os.path.exists(trunk_path):
                print(f"Using trunk cutout: {trunk_path}")
                analysis_path = trunk_path
            else:
                print("Warning: Could not create trunk cutout, using full segmented image")
                analysis_path = segmented_photo_path
        else:
            # Use full segmented image
            print(f"\nUsing full segmented image: {segmented_photo_path}")
            analysis_path = segmented_photo_path
    else:
        print("ERROR: Primary tilt photo segmentation failed or file not found")
    
    # Run tilt detection with fallback to backup
    tilt = None
    result_img = None
    binary = None
    trunk_lines_count = 0
    method_name = {
        "1": "Original",
        "2": "PCA",
        "3": "Combined"
    }.get(detection_method, "Original")
    
    # Try primary image
    if analysis_path and os.path.exists(analysis_path):
        print(f"\nAttempting tilt detection on primary image: {analysis_path}")
        result = run_tilt_detection(analysis_path, detection_method)
        
        if result is not None:
            tilt, result_img, binary, trunk_lines_count = result
            display_and_save_results(tilt, result_img, binary, trunk_lines_count, analysis_path, method_name)
        else:
            print(f"\nWARNING: Primary tilt detection failed. Attempting backup photo...")
    
    # Try backup if primary failed
    if tilt is None and segmented_backup_path and os.path.exists(segmented_backup_path):
        print(f"\nAttempting tilt detection on backup image: {segmented_backup_path}")
        result = run_tilt_detection(segmented_backup_path, detection_method)
        
        if result is not None:
            tilt, result_img, binary, trunk_lines_count = result
            display_and_save_results(tilt, result_img, binary, trunk_lines_count, segmented_backup_path, f"{method_name} (Backup)")
        else:
            print("\nERROR: Both primary and backup tilt detection failed.")
    elif tilt is None:
        print("\nERROR: Tilt detection failed and no backup photo available.")
    
    # Perform tree species classification
    multiplier = 1.0  # Default multiplier
    species = "Unknown"  # Default species
    
    if segmented_classification_path and os.path.exists(segmented_classification_path):
        try:
            print("\n=== Tree Species Classification ===")
            multiplier, species = tsp.get_species_info(
                API_Key_storage.give_api_key(), 
                segmented_classification_path, 
                False, 
                False
            )
            print(f"Species: {species}")
            print(f"Risk Multiplier: {multiplier}")
        except Exception as e:
            print(f"Warning: Species classification failed: {e}")
            print("Using default values (species=Unknown, multiplier=1.0)")
    else:
        print("\nWarning: No classification photo available. Using default species values.")
    
    # Calculate and display risk score (if tilt was detected)
    if tilt is not None:
        try:
            print("\n=== RISK ASSESSMENT ===")
            combined_risk_score_val = risk_score.combined_tree_risk(multiplier, tilt, species, trunk_lines_count)
            decision = risk_score.get_risk_category(combined_risk_score_val)
            print(f"Risk Score: {combined_risk_score_val:.1f}")
            print(f"Risk Category: {decision}")
            
            # Get diagnosis and fixes
            try:
                diagnosis = diagnose.get_plant_diagnosis_groq(segmented_classification_path)
                fixes = diagnose.get_plant_fixes_groq(diagnosis, segmented_classification_path)
                risk_score.display_risk_gradient(combined_risk_score_val, tilt, diagnosis, fixes)
            except Exception as e:
                print(f"Warning: Could not get plant diagnosis: {e}")
                risk_score.display_risk_gradient(combined_risk_score_val, tilt, "Diagnosis unavailable", "Fixes unavailable")
        except Exception as e:
            print(f"Error calculating risk assessment: {e}")
    else:
        print("\n=== RISK ASSESSMENT ===")
        print("Cannot calculate risk score: Tilt detection failed on all available images.")
    
    print("\n=== Analysis Complete ===")

if __name__ == "__main__":
    main()