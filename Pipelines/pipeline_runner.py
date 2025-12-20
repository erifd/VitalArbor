import sam2_segmentation
import tilt_detection
import tilt_detection2
import combo_tilt_detection
import width_of_trunk
import risk_score
import cv2
import os
import numpy as np

def main():
    """Main function to run tree analysis pipeline with tilt detection options."""
    
    # Get photo path from user
    photo = str(input("Enter the complete path of the photo you want to process: "))
    use_cutout_input = str(input("Do you want to use a cutout of the photo? (y/n): ")).lower()
    
    # Ask which tilt detection method to use
    print("\nTilt Detection Methods:")
    print("1. Original (Line Intersection only)")
    print("2. PCA Method")
    print("3. Combined (PCA + Line Intersection)")
    detection_method = str(input("Choose detection method (1, 2, or 3): ")).strip()
    
    # Run SAM2 segmentation
    if photo:
        sam2_segmentation.run_sam2_segmentation(photo)
    
    # Get the segmented photo path
    segmented_photo_path = sam2_segmentation.get_segmented_filename()
    
    # Determine which image to analyze
    if use_cutout_input == 'y':
        # Get trunk cutout
        trunk_path = width_of_trunk.get_trunk_width_analysis(segmented_photo_path)
        print(f"Checking if file exists: {os.path.exists(trunk_path)}")
        print(f"Full path: {os.path.abspath(trunk_path)}")
        analysis_path = trunk_path
    else:
        # Use full segmented image
        print(f"Checking if file exists: {os.path.exists(segmented_photo_path)}")
        print(f"Full path: {os.path.abspath(segmented_photo_path)}")
        analysis_path = segmented_photo_path
    
    # Run selected tilt detection method
    if detection_method == "2":
        # Use PCA method
        print("\n=== Running PCA Tilt Detection ===")
        result = tilt_detection2.analyze_tree(analysis_path)
        
        if result is not None:
            # Check if result is a tuple or single value
            if isinstance(result, tuple):
                # Full return format: (tilt, result_img, binary, trunk_lines_count)
                tilt, result_img, binary, trunk_lines_count = result
                
                # Print detailed results
                print(f"\n=== FINAL RESULT ===")
                print(f"PCA tilt angle: {tilt:.2f}° from vertical")
                print(f"Trunk lines detected: {trunk_lines_count}")
                
                # Display binary and result side by side
                display_height = 600
                aspect_ratio = binary.shape[1] / binary.shape[0]
                display_width = int(display_height * aspect_ratio)
                
                binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), 
                                            (display_width, display_height))
                result_display = cv2.resize(result_img, (display_width, display_height))
                
                combined_display = np.hstack([binary_display, result_display])
                
                cv2.imshow('Binary | PCA Detection', combined_display)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                
                # Save visualization
                output_filename = f"tilt_pca_{os.path.basename(analysis_path)}"
                cv2.imwrite(output_filename, result_img)
                print(f"\nDetailed visualization saved to: {output_filename}")
            else:
                # Simple return format: just tilt angle
                tilt = float(result)
                trunk_lines_count = 0
                
                print(f"\n=== FINAL RESULT ===")
                print(f"PCA tilt angle: {tilt:.2f}° from vertical")
                print("(Note: PCA method returned angle only, no visualization available)")
            
        else:
            print("\nERROR: Could not detect tree tilt using PCA")
            tilt = None
            trunk_lines_count = 0
    
    elif detection_method == "3":
        # Use combined method
        print("\n=== Running Combined Tilt Detection (PCA + Lines) ===")
        result = combo_tilt_detection.detect_tree_tilt_combined(
            analysis_path,
            pca_weight=0.6,  # 60% PCA, 40% line intersection
            rotation_angles=[-10, -5, 0, 5, 10]  # Try multiple PCA orientations
        )
        
        if result is not None:
            # Unpack results (same format as original)
            tilt, result_img, binary, trunk_lines_count = result
            
            # Print detailed results
            print(f"\n=== FINAL RESULT ===")
            print(f"Combined tilt angle: {tilt:.2f}° from vertical")
            print(f"Trunk lines detected: {trunk_lines_count}")
            
            # Display binary and result side by side
            display_height = 600
            aspect_ratio = binary.shape[1] / binary.shape[0]
            display_width = int(display_height * aspect_ratio)
            
            binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), 
                                        (display_width, display_height))
            result_display = cv2.resize(result_img, (display_width, display_height))
            
            combined_display = np.hstack([binary_display, result_display])
            
            cv2.imshow('Binary | Combined Detection (PCA=Magenta, Lines=Cyan)', combined_display)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            # Save visualization
            output_filename = f"tilt_combined_{os.path.basename(analysis_path)}"
            cv2.imwrite(output_filename, result_img)
            print(f"\nDetailed visualization saved to: {output_filename}")
            
        else:
            print("\nERROR: Could not detect tree tilt")
            tilt = None
            trunk_lines_count = 0
    
    else:
        # Use original method
        print("\n=== Running Original Tilt Detection (Line Intersection) ===")
        result = tilt_detection.detect_tree_tilt(analysis_path)
        
        if result is not None:
            tilt, result_img, binary, trunk_lines_count = result
            print(f"\n=== FINAL RESULT ===")
            print(f"Tree tilt angle: {tilt:.2f}° from vertical")
            print(f"Trunk lines detected: {trunk_lines_count}")
            
            # Display binary and result side by side
            display_height = 600
            aspect_ratio = binary.shape[1] / binary.shape[0]
            display_width = int(display_height * aspect_ratio)
            
            binary_display = cv2.resize(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR), 
                                        (display_width, display_height))
            result_display = cv2.resize(result_img, (display_width, display_height))
            
            combined_display = np.hstack([binary_display, result_display])
            
            cv2.imshow('Binary | Detected Lines', combined_display)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            # Save visualization
            output_filename = f"tilt_original_{os.path.basename(analysis_path)}"
            cv2.imwrite(output_filename, result_img)
            print(f"\nDetailed visualization saved to: {output_filename}")
        else:
            print("\nERROR: Could not detect tree trunk")
            tilt = None
            trunk_lines_count = 0
    
    # Calculate and display risk score (if tilt was detected)
    if tilt is not None:
        print("\n=== RISK ASSESSMENT ===")
        risk_score_value = risk_score.give_risk_score(tilt, trunk_lines_count)
        decision = risk_score.get_risk_category(risk_score_value)
        print(f"Risk Score: {risk_score_value:.1f}")
        print(f"Risk Category: {decision}")
        risk_score.display_risk_gradient(risk_score_value, tilt)


if __name__ == "__main__":
    main()