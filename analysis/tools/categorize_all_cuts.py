import json
import os
import sys
import cv2
import glob
import numpy as np

sys.path.insert(0, '.')
sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

f1 = glob.glob('reference/*5.88sec clip*')[0]
f2 = glob.glob('reference/*05.888sec-18.10seconds*')[0]
f3 = glob.glob('reference/*full video*')[0]

c1 = cv2.VideoCapture(f1)
c2 = cv2.VideoCapture(f2)
c3 = cv2.VideoCapture(f3)

fps = 23.976023976023978

def get_frame(global_idx):
    if global_idx < 141:
        c1.set(cv2.CAP_PROP_POS_FRAMES, global_idx)
        ret, fr = c1.read()
        return fr
    elif global_idx < 380:
        c2.set(cv2.CAP_PROP_POS_FRAMES, global_idx - 141)
        ret, fr = c2.read()
        return fr
    elif global_idx < 1955:
        c3.set(cv2.CAP_PROP_POS_FRAMES, global_idx - 380)
        ret, fr = c3.read()
        return fr
    return None

# Load diffs
with open('scratch_cuts_diff.json') as f:
    diffs = json.load(f)

# Let's inspect each shot in TIMELINE and see if there are cuts inside its interval
cuts = []

for i in range(len(TIMELINE)):
    s = TIMELINE[i]
    shot_id = s['shot']
    t_start = s['start']
    dur = s['dur']
    t_end = t_start + dur
    f_start = round(t_start * fps)
    f_end = round(t_end * fps)
    
    # check inside this shot for any internal peaks
    # window from f_start+2 to f_end-2
    internal_peaks = []
    for f in range(f_start + 2, f_end - 1):
        if f < len(diffs):
            d = diffs[f]
            if d['px'] > 12.0 or d['hist'] > 0.4:
                internal_peaks.append((f, d['time'], d['px'], d['hist']))
    
    cuts.append({
        'shot': shot_id,
        'plan_start': t_start,
        'plan_dur': dur,
        'f_start': f_start,
        'f_end': f_end,
        'note': s.get('note', ''),
        'internal_peaks': internal_peaks
    })

print("Shots with strong internal peaks:")
for c in cuts:
    if c['internal_peaks']:
        print(f"Shot {c['shot']} (f{c['f_start']}-f{c['f_end']}): {c['internal_peaks']}")

