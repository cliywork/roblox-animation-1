"""
threeway.py - one sheet per chunk: MOVIE | WIREFRAME | ROBLOX STUDIO, one row per moment.

    python analysis/tools/threeway.py OUT.jpg  wire_sheet_dir  t:studio_capture.jpg ...

- MOVIE: the reference, read from the right clip for each time (0-5.888 clip, 5.888-15.856 mid clip, rest full video).
- WIRE: the stick-figure panel from roblox_pipeline/preview.py (its right-hand half). The left half of that
  tool's output is ignored: its movie column reads the full video with an offset, which is wrong before 15.856 s.
- ROBLOX: the Studio capture at that moment.
"""
import glob
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_analysis as m  # noqa: E402

CELL_W = 520


def movie_frame(t, full, clip, mid, top, bot):
    if t < 5.888:
        clip.set(cv2.CAP_PROP_POS_FRAMES, round(t * clip.get(cv2.CAP_PROP_FPS)))
        ok, fr = clip.read()
    elif t < m.OFF:
        mid.set(cv2.CAP_PROP_POS_FRAMES, round((t - 5.888) * mid.get(cv2.CAP_PROP_FPS)))
        ok, fr = mid.read()
    else:
        fr = m.ref_frame(full, t)
        ok = fr is not None
    if not ok:
        return np.zeros((bot - top, 1920, 3), np.uint8)
    return fr[top:bot]


def wire_panels(sheet_dir):
    """every row of every preview sheet, right half only, in time order (the sheets list their rows in order)"""
    rows = []
    for path in sorted(glob.glob(os.path.join(sheet_dir, "compare_*.jpg")), key=lambda p: int(os.path.basename(p)[8:-4])):
        img = cv2.imread(path)
        h, w = img.shape[:2]
        n = 4
        for r in range(n):
            y0, y1 = r * h // n, (r + 1) * h // n
            rows.append(img[y0:y1, w // 2:])
    return rows


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(out, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    return out


def fit(img, w=CELL_W):
    return cv2.resize(img, (w, max(1, int(img.shape[0] * w / img.shape[1]))), interpolation=cv2.INTER_AREA)


def main():
    out, wire_dir = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    start = next((int(a.split("=")[1]) for a in args if a.startswith("--wire-start=")), 0)  # first wire row of this sheet
    pairs = []
    for arg in (a for a in args if not a.startswith("--")):
        t, path = arg.split(":", 1)
        pairs.append((float(t), path))

    full = m.ref_cap()
    top, bot = m.active_rows(full)
    clip = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*5.88sec clip*"))[0])
    mid = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*05.888sec-18.10seconds*"))[0])
    wires = wire_panels(wire_dir)
    rows = []
    for i, (t, path) in enumerate(pairs):
        movie = fit(movie_frame(t, full, clip, mid, top, bot))
        wire = fit(wires[start + i]) if start + i < len(wires) else np.zeros_like(movie)
        studio = cv2.imread(path) if path != "-" else None
        if studio is None:  # not captured yet: a grey placeholder keeps the row layout
            studio = np.full((wire.shape[0], CELL_W, 3), 60, np.uint8)
            cv2.putText(studio, "ROBLOX: not captured", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
        studio = fit(studio)
        h = min(movie.shape[0], wire.shape[0], studio.shape[0])
        cells = [label(c[:h], lbl) for c, lbl in (
            (movie, f"MOVIE  t={t:.2f}  f{round((t - m.OFF) * m.REF_FPS) if t >= m.OFF else round(t * m.REF_FPS)}"),
            (wire, f"WIREFRAME  t={t:.2f}"),
            (studio, f"ROBLOX STUDIO  t={t:.2f}"))]
        rows.append(np.hstack([cells[0], np.full((h, 6, 3), 255, np.uint8), cells[1],
                               np.full((h, 6, 3), 255, np.uint8), cells[2]]))
        rows.append(np.full((6, rows[-1].shape[1], 3), 255, np.uint8))
    grid = np.vstack(rows)
    m.save(out, grid)
    print("wrote", out, grid.shape)


if __name__ == "__main__":
    main()
