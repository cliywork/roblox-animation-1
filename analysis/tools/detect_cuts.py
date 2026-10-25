import json
import os
import sys
import cv2
import glob
import numpy as np

sys.path.insert(0, '.')
sys.path.insert(0, 'roblox_pipeline')

with open('scratch_cuts_diff.json') as f:
    diffs = json.load(f)

from scene import TIMELINE

print("Total planned shots in TIMELINE:", len(TIMELINE))

# Let's inspect each shot from TIMELINE and see its start time and corresponding frame
timeline_starts = [(s['shot'], s['start'], round(s['start'] * 23.97602), s['note']) for s in TIMELINE]

# For each diff, let's find local peaks
# We can look at a window of +- 2 frames
peaks = []
for i in range(1, len(diffs) - 1):
    d = diffs[i]
    prev_d = diffs[i-1]
    next_d = diffs[i+1]
    # Check if local peak
    if (d['px'] > 7.0 or d['hist'] > 0.15):
        if d['px'] >= prev_d['px'] and d['px'] >= next_d['px'] or d['hist'] >= prev_d['hist'] and d['hist'] >= next_d['hist']:
            peaks.append(d)

print(f"Total peaks found: {len(peaks)}")

# Let's check matching against planned timeline
for name, t_start, f_start, note in timeline_starts:
    # find closest peak
    best_p = min(diffs, key=lambda d: abs(d['time'] - t_start))
    # find highest peak within +- 5 frames
    window = [d for d in diffs if abs(d['frame'] - f_start) <= 5]
    max_p = max(window, key=lambda d: d['px']) if window else best_p
    print(f"Shot {name:4s} | Plan: t={t_start:6.3f}s (f{f_start:4d}) | Best Cut Peak: t={max_p['time']:6.3f}s (f{max_p['frame']:4d}) px={max_p['px']:4.1f} hist={max_p['hist']:.2f}")

