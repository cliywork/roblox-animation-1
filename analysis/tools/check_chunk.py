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

# Let's write a function to check a specific chunk
def check_chunk(name, f_start, f_end):
    print(f"\n==================== {name} (f{f_start} to f{f_end}, {f_start/fps:.2f}s to {f_end/fps:.2f}s) ====================")
    chunk_diffs = [d for d in diffs if f_start <= d['frame'] <= f_end]
    # find all local peaks with px > 9.0 or hist > 0.22
    for i in range(1, len(chunk_diffs) - 1):
        d = chunk_diffs[i]
        p0 = chunk_diffs[i-1]['px']
        p1 = d['px']
        p2 = chunk_diffs[i+1]['px']
        if (p1 >= p0 and p1 >= p2 and (p1 > 9.0 or d['hist'] > 0.22)) or (p1 > 12.0):
            t = d['frame'] / fps
            print(f"Candidate Peak: f{d['frame']:4d} ({t:6.3f}s) | px: {p1:5.1f} | hist: {d['hist']:5.3f}")

# Run for all chunks
check_chunk("Chunk 1: Standoff & Dialogue", 0, 434)
check_chunk("Chunk 2: Missiles & Charge", 434, 705)
check_chunk("Chunk 3: Helmet & Recover", 705, 845)
check_chunk("Chunk 4: Beam & Counter-Blow", 845, 1092)
check_chunk("Chunk 5: Blood & Face-off", 1092, 1265)
check_chunk("Chunk 6: Beatdown Punches", 1265, 1446)
check_chunk("Chunk 7: Blast & March", 1446, 1625)
check_chunk("Chunk 8: Fire-Lasers & Stab", 1625, 1954)


