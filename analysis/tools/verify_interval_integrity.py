import json
import os
import sys
import cv2
import glob
import numpy as np

# Load our 79 cut boundaries and verify each interval
# Let's define the 79 cuts with start frame and end frame
# Let's inspect maximum diff within each interval (excluding +-2 frames around cut boundaries)

with open('scratch_cuts_diff.json') as f:
    diffs = json.load(f)

cut_frames = [
    0, 20, 54, 63, 91, 141, 188, 220, 250, 380,
    434, 463, 495, 514, 540, 588, 611, 636, 656, 671, 686, 705,
    731, 746, 757, 765, 787, 845, 860, 895, 908, 924, 953, 985, 1002, 1015, 1026, 1040, 1057, 1068, 1079,
    1092, 1169, 1189, 1253, 1265, 1272, 1295, 1311, 1322, 1331, 1346, 1357, 1384, 1393, 1409, 1423,
    1446, 1492, 1520, 1552, 1569, 1591, 1625, 1643, 1691, 1718, 1747, 1760, 1783, 1798, 1821, 1834, 1856, 1866, 1899, 1915, 1931, 1943
]

print(f"Total cut frames listed: {len(cut_frames)}")

# Check interval integrity
anomalies = []
for i in range(len(cut_frames) - 1):
    f_start = cut_frames[i]
    f_end = cut_frames[i+1]
    
    # check inside f_start + 2 to f_end - 2
    for f in range(f_start + 2, f_end - 1):
        if f < len(diffs):
            d = diffs[f]
            # If px > 15 and hist > 0.4
            if d['px'] > 15.0 and d['hist'] > 0.4:
                anomalies.append((i+1, f, d['time'], d['px'], d['hist']))

print(f"Found {len(anomalies)} internal anomalies across all 78 intervals:")
for a in anomalies:
    print(f"Cut {a[0]} (between f{cut_frames[a[0]-1]} and f{cut_frames[a[0]]}): internal peak at f{a[1]} ({a[2]:.3f}s) px={a[3]:.1f} hist={a[4]:.2f}")
