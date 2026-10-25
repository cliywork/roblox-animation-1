import cv2
import numpy as np

# Let's inspect the diagnostic images
# We want to know: did the camera angle change between left and right?
# We can print structural similarity or inspect visually.
# Let's write a script that analyzes the diagnostic pairs.

def analyze_pair(f_idx):
    img = cv2.imread(f"analysis/diagnostic_f{f_idx}.jpg")
    if img is None:
        return
    h, w = img.shape[:2]
    left = img[:, :w//2]
    right = img[:, w//2:]
    
    # Let's compute color histogram correlation
    h_l = cv2.calcHist([left], [0, 1, 2], None, [8, 8, 8], [0, 256]*3)
    h_r = cv2.calcHist([right], [0, 1, 2], None, [8, 8, 8], [0, 256]*3)
    h_l = cv2.normalize(h_l, h_l).flatten()
    h_r = cv2.normalize(h_r, h_r).flatten()
    corr = cv2.compareHist(h_l, h_r, cv2.HISTCMP_CORREL)
    diff = np.mean(np.abs(left.astype(float) - right.astype(float)))
    
    print(f"f{f_idx:4d}: diff={diff:5.2f}, hist_corr={corr:5.3f}")

# Test all questionable
from verify_questionable import questionable
for f_idx, desc in questionable:
    analyze_pair(f_idx)

