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

with open('scratch_cuts_diff.json') as f:
    diffs = json.load(f)

# Let's inspect intervals
# 1. 0s to 5.88s:
# Candidate frames from analyze_real_cuts:
# f20 (0.834s): shot 020
# f37 (1.543s): wait, is f37 a cut or middle of shot 020?
# f46 (1.919s)?
# f54 (2.252s): shot 030
# f63 (2.628s): shot 040
# f77 (3.212s)?
# f91 (3.795s): shot 050
# f141 (5.881s): shot 060

test_frames = [20, 37, 46, 54, 63, 77, 91, 141]
for tf in test_frames:
    fa = get_frame(tf - 1)
    fb = get_frame(tf)
    # compute diff
    diff = np.mean(np.abs(fa.astype(float) - fb.astype(float)))
    print(f"Frame {tf-1} -> {tf} ({tf/fps:.3f}s): diff = {diff:.2f}")

