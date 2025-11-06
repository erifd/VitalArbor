import cv2
import scikit
img = cv2.imread(image_filename)
img = img.astype('uint8')
#convert to grayscale
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#calculate properties
brightness = (np.mean(img)) / 255
contrast = img.std()
entropy = skimage.measure.shannon_entropy(img)
laplacian = cv2.Laplacian(img, cv2.CV_64F).var()