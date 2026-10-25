import json
import os
import cv2
import glob
import numpy as np

# Load the candidate files in analysis/cut_candidates/
files = sorted(glob.glob('analysis/cut_candidates/*.jpg'))
print(f"Total candidate images: {len(files)}")

# Let's write an analysis script to check candidates against scene.py TIMELINE
import sys
sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

fps = 23.976023976023978

# Map each timeline shot
shots_by_frame = {}
for s in TIMELINE:
    f = round(s['start'] * fps)
    shots_by_frame[f] = s

print(f"Total timeline shots: {len(TIMELINE)}")
