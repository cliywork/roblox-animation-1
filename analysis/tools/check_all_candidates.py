import json
import os
import sys
import cv2
import glob
import numpy as np

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

# Find all candidate cut frames where diff spikes
# A true camera cut in 24fps video is a sharp jump between frame k-1 and k.
# Let's inspect all peaks where px > 12.0 or hist > 0.35, or local peak > 8.0 with hist > 0.20
candidate_indices = []
for i in range(1, len(diffs)-1):
    d = diffs[i]
    # Check if local maximum
    p0 = diffs[i-1]['px']
    p1 = d['px']
    p2 = diffs[i+1]['px']
    h1 = d['hist']
    if p1 >= p0 and p1 >= p2 and (p1 > 10.0 or h1 > 0.3):
        candidate_indices.append(d['frame'])

print(f"Total candidate peaks: {len(candidate_indices)}")

# Let's inspect each candidate
os.makedirs('analysis/cut_candidates', exist_ok=True)
results = []
for f_idx in candidate_indices:
    t = f_idx / fps
    fa = get_frame(f_idx - 1)
    fb = get_frame(f_idx)
    if fa is None or fb is None:
        continue
    # crop letterbox
    ca = fa[100:910, :]
    cb = fb[100:910, :]
    diff_val = np.mean(np.abs(ca.astype(float) - cb.astype(float)))
    
    # Save a small pair image
    h, w = ca.shape[:2]
    small_a = cv2.resize(ca, (320, int(320 * h / w)))
    small_b = cv2.resize(cb, (320, int(320 * h / w)))
    pair = np.hstack([small_a, small_b])
    cv2.putText(pair, f"f{f_idx-1}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.putText(pair, f"f{f_idx} ({t:.3f}s)", (330, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    cv2.imwrite(f'analysis/cut_candidates/cut_f{f_idx:04d}_{t:06.2f}s.jpg', pair)
    results.append({'frame': f_idx, 'time': t, 'diff': diff_val})

print(f"Wrote {len(results)} candidate pairs to analysis/cut_candidates/")
