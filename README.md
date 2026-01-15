# VitalArbor
Vital Arbor is a tree failure detection and risk assessment app in development to warn users if ther tree is about to fall. This app uses Meta's **Segment Anything 2 (SAM2)** model to segment images, and computer vision and YOLO11 to figure out the health of the tree. These pipelines will give you a risk score, which will be average to find the health of the tree, and if it is **at risk of falling** or, **tree failure is imminent, and the tree should be removed.**

# Algorithms
VitalArbor has 2 tilt estimation methods, and you can select which one to use.
![VitalArbor Arcitecture](Systems_Architecture_Diagram.png?raw=true)
  ## The Math Model
  This model employs OpenCV's Hough Transform, and Geometry to calculate the tilt angle of the tree.
  First, it uses Hough's Transform to detect all possible lines in the image, which is possible due to SAM2 filtering out the tree, with it's image segmentation program. Then, the pipeline removes all lines that do not intersect with the bottom, and looks at the bottom 50%, which is reasonable for the tree trunk. It calculates the offset from the center, and then uses arctan on all of the lines which had the offsets, and calculates the tilt angle from an average.
  
  After the tilt angle has been calculated, the pipeline finds the center of the tree trunk from the binary mask, and projects the tilt angle. It checks how well the tilt angle sits on the tree, and if it is beneath a certain threshold, redoes the tilt angle calculation, which may change the angle by some amount. The tilt detection algorithm also looks at the tree trunk general structure, and tells you if the trunk has a natural sweep, where the trunk grows back to a vertical state and adapts to the tilt, or if it has a plated sweep, and has more of a danger of falling.

Additionally, if you want to see more about the pipelines, and their current errors, visit [VitalArbor statistics Molab](https://molab.marimo.io/notebooks/nb_H1GAb8eWgBhqYmGYULynUu) to view changes in tilt angles, and errors. 
Statistics will be published and updated as algorithms are fine-tuned.

# Running the code

Currently, only the segmentation pipeline using **SAM2** has worked, and you can select the points of the tree to try to segment it.


<details>
<summary>Running the code for a pipeline?</summary>
1. You need to locate the path of your repo, where you have cloned it

2. Find the path of the folder Pipelines.

3. Choose the image you want to segment, or crop out, or do tilt detection
4. Change it in the respective places for image path
5. Go to terminal
6. Use `cd <your path for the folder Pipelines>` to get to the area to run the pipeline
7. If your file is crop out, then run `python crop_out.py`
8. If your file is tilt detection, then run `python tilt_detection.py`
9. If your file is sam2 segmentation, then run `python sam2_segmentation.py`
</details>

<details>
<summary>Running the code for all of the pipelines?</summary>
1. Use cd in cmd to to get to the folder of Pipelines again, as the pipeline runner code is stored here.

2. Next, you will do `python pipeline_runner.py`
3. You will be prompted with questions about where you want the photo to be.
4. Just copy down the path, but **DO NOT PUT QUOTES AROUND IT.**
5. Here, you will have to segment the image like in the segmentation code.
6. You will then get details about the tree, like the tilt angle.  
</details>  

**IMPORTANT NOTE**

  If you get an error for sam2 segmentation, you must follow the instructions to download [SAM2](https://github.com/facebookresearch/sam2/blob/main/INSTALL.md) with that link. **Make sure that when you download it, you are downloading SAM2 into the same folder as your repo, but do not change anything else. It should work**
