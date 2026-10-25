import json
import os
import sys
import cv2
import glob
import numpy as np

sys.path.insert(0, '.')
sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

fps = 23.976023976023978

with open('scratch_cuts_diff.json') as f:
    diffs = json.load(f)

# Let's inspect each shot from TIMELINE
# We want to find the exact frame where the cut occurs in the video (where pixel diff / hist diff peaks)
verified_cuts = []

for i, s in enumerate(TIMELINE):
    shot_id = s['shot']
    t_start = s['start']
    dur = s['dur']
    f_plan = round(t_start * fps)
    
    if i == 0:
        # First shot starts at frame 0
        best_f = 0
        best_t = 0.000
        best_diff = 0.0
    else:
        # Look in window of +- 5 frames around f_plan
        window = [d for d in diffs if abs(d['frame'] - f_plan) <= 4]
        if window:
            # Pick highest px diff
            best_d = max(window, key=lambda d: d['px'])
            best_f = best_d['frame']
            best_t = best_d['time']
            best_diff = best_d['px']
        else:
            best_f = f_plan
            best_t = t_start
            best_diff = 0.0
            
    verified_cuts.append({
        'shot': shot_id,
        'plan_t': t_start,
        'plan_f': f_plan,
        'exact_f': best_f,
        'exact_t': best_t,
        'diff': best_diff,
        'note': s.get('note', '')
    })

# Check shot 130 which has 130a and 130b in the movie
# We know at frame 540 (22.522s) there is a cut from 130a to 130b
print(f"Total TIMELINE shots matched: {len(verified_cuts)}")

# Print all matched cuts with their offset from plan
for c in verified_cuts:
    off_ms = (c['exact_t'] - c['plan_t']) * 1000
    print(f"Shot {c['shot']:4s} | Exact: f{c['exact_f']:4d} ({c['exact_t']:6.3f}s) | Plan: f{c['plan_f']:4d} ({c['plan_t']:6.3f}s) | Off: {off_ms:+4.0f}ms | Diff: {c['diff']:4.1f}")

