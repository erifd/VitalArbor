# VitalArbor
A Tree Falling risk detection and health and detection app which works sometimes and is in development. This app uses Meta's **Segment Anything 2 (SAM2)** model to segment images, and computer vision and YOLO11 to figure out the health of the tree. These pipelines will give you a risk score, which will be average to find the health of the tree, and if it is **at risk of falling**.


Currently, only the segmentation pipeline using **SAM2** has worked, and you can select the points of the tree to try to segment it. In a folder, I provided some images of the results, but they are crude.

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
1. You will need to use cmd again here, by running cd your path to VitalArbor

2. Next, you will do `python pipeline_runner.py`
3. You will be prompted with questions about where you want the photo to be.
4. Just copy down the path, but **DO NOT PUT QUOTES AROUND IT.**
5. Here, you will have to segment the image like in the segmentation code.
6. You will then get details about the tree, like the tilt angle.  
</details>

   

**IMPORTANT NOTE**

  If you get an error for sam2 segmentation, you must follow the instructions to download [SAM2](https://github.com/facebookresearch/sam2/blob/main/INSTALL.md) with that link. **Make sure that when you download it, you are downloading SAM2 into the same folder as your repo, but do not change anything else. It should work**
