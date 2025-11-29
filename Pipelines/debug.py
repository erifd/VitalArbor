import cv2


img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

if img is None:
    print("Image not found or couldn't be loaded!")
else:
    print(f"Image loaded successfully! Shape: {img.shape}")
    
    # Scale down for display while maintaining aspect ratio
    display_height = 600
    aspect_ratio = img.shape[1] / img.shape[0]
    display_width = int(display_height * aspect_ratio)
    display_img = cv2.resize(img, (display_width, display_height))
    
    cv2.imshow('Image', display_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()