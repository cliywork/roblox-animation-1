import json
import os
import sys
import cv2
import glob
import numpy as np

with open('scratch_cuts_diff.json') as f:
    diffs = json.load(f)

# Find all potential cut events
# Hard cuts: px > 9.0 or hist > 0.22
clusters = []
curr = []
for d in diffs:
    if d['px'] > 9.0 or d['hist'] > 0.22:
        curr.append(d)
    else:
        if curr:
            peak = max(curr, key=lambda x: x['px'])
            clusters.append(peak)
            curr = []
if curr:
    clusters.append(max(curr, key=lambda x: x['px']))

print(f"Total potential cut clusters: {len(clusters)}")
for i, c in enumerate(clusters):
    print(f"{i+1:3d}: frame {c['frame']:4d} | time {c['time']:6.3f}s | px {c['px']:5.1f} | hist {c['hist']:5.3f}")
