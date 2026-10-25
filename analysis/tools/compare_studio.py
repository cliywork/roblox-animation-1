"""
compare_studio.py - puts each reference frame beside the matching Roblox Studio capture, one image.

Usage (from the project root):
    python analysis/tools/compare_studio.py OUT_NAME  MOVIE_T:STUDIO_IMAGE  [MOVIE_T:STUDIO_IMAGE ...]

Example:
    python analysis/tools/compare_studio.py stab_check 81.10:C:/.../capture_a.jpg 82.37:C:/.../capture_b.jpg

Writes analysis/compare/OUT_NAME.jpg (the folder is created on save): one row per frame, left = reference (movie), right = Studio.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_analysis as m  # noqa: E402

ROW_W = 700  # width of each half


def main():
    name = sys.argv[1]
    pairs = []
    for arg in sys.argv[2:]:
        t_str, path = arg.split(":", 1)
        pairs.append((float(t_str), path))

    import glob
    full = m.ref_cap()
    top, bot = m.active_rows(full)
    clip = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*5.88sec clip*"))[0])
    clip_fps = clip.get(cv2.CAP_PROP_FPS)
    # 5.888-18.10 s clip: its frame 0 is movie frame 141 (frame = (t - 5.888) * fps)
    mid = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*05.888sec-18.10seconds*"))[0])
    rows = []
    for t, path in pairs:
        if t < 5.888:  # first clip: frame = t * fps
            clip.set(cv2.CAP_PROP_POS_FRAMES, round(t * clip_fps))
            ok, ref = clip.read()
            ref = ref[top:bot] if ok else np.zeros((bot - top, 1920, 3), np.uint8)
        elif t < m.OFF:  # middle clip: frame = (t - 5.888) * fps
            mid.set(cv2.CAP_PROP_POS_FRAMES, round((t - 5.888) * clip_fps))
            ok, ref = mid.read()
            ref = ref[top:bot] if ok else np.zeros((bot - top, 1920, 3), np.uint8)
        else:
            ref = m.ref_frame(full, t)[top:bot]
        studio = cv2.imread(path)
        if studio is None:
            raise SystemExit(f"cannot read {path}")
        ref = cv2.resize(ref, (ROW_W, int(ref.shape[0] * ROW_W / ref.shape[1])))
        studio = cv2.resize(studio, (ROW_W, int(studio.shape[0] * ROW_W / studio.shape[1])))
        h = min(ref.shape[0], studio.shape[0])
        ref, studio = ref[:h], studio[:h]
        ref = m.label(ref, f"MOVIE  t={t:.2f}  f{round((t - m.OFF) * m.REF_FPS)}")
        studio = m.label(studio, "ROBLOX")
        rows.append(np.hstack([ref, np.zeros((h, 6, 3), np.uint8) + 255, studio]))
    grid = np.vstack([np.vstack([r, np.zeros((6, r.shape[1], 3), np.uint8) + 255]) for r in rows])
    out = os.path.join(m.OUT, "compare", f"{name}.jpg")
    m.save(out, grid)
    print("wrote", out, grid.shape)


if __name__ == "__main__":
    main()
