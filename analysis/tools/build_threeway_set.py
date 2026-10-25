"""
build_threeway_set.py - the three-way set that Argon reads, one image per shot.

    python analysis/tools/build_threeway_set.py            # all three steps
    python analysis/tools/build_threeway_set.py real       # only the movie frames
    python analysis/tools/build_threeway_set.py python     # only the stick-figure renders
    python analysis/tools/build_threeway_set.py sheets     # only the chunk sheets (after replacing an image)

Writes into docs/images/threeway/:
    real/           MOVIE frame of each shot          <shot>.jpg   (this script, from reference/)
    python_line/    stick-figure render of each shot  <shot>.jpg   (this script, from roblox_pipeline/preview.py)
    roblox/         Roblox Studio capture of each shot <shot>.jpg  (copied in once; replace a file to update it)
    chunk_sheets/   MOVIE | PYTHON LINE | ROBLOX STUDIO, one sheet per chunk, at most 12 rows per sheet

Times and frames come from analysis/threeway_all/moments.json (one moment per shot).
A missing image becomes a grey "NOT CAPTURED" placeholder, so a sheet always builds.
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_analysis as m  # noqa: E402
import threeway as tw      # noqa: E402

OUT = os.path.join(m.ROOT, "docs", "images", "threeway")
MOMENTS = os.path.join(m.ROOT, "analysis", "threeway_all", "moments.json")
ROWS_PER_SHEET = 12
CHUNKS = [  # (number, name, last shot id in the chunk); each shot joins the first chunk whose last id is >= it
    (1, "standoff_dialogue", 100), (2, "missiles", 185), (3, "helmet", 230), (4, "beam", 310),
    (5, "drop_blood", 360), (6, "beatdown", 430), (7, "blast_walk", 460), (8, "lasers_stab", 560),
]


def load_moments():
    with open(MOMENTS, encoding="utf-8") as f:
        return json.load(f)


def chunk_of(shot):
    for num, name, last in CHUNKS:
        if int(shot) <= last:
            return num, name
    raise ValueError(f"shot {shot} is outside every chunk")


def make_real(moments):
    full = m.ref_cap()
    top, bot = m.active_rows(full)
    clip = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*5.88sec clip*"))[0])
    mid = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*05.888sec-18.10seconds*"))[0])
    folder = os.path.join(OUT, "real")
    os.makedirs(folder, exist_ok=True)
    for mo in moments:
        fr = tw.movie_frame(mo["t"], full, clip, mid, top, bot)
        cv2.imwrite(os.path.join(folder, mo["shot"] + ".jpg"), fr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("real:", len(moments), "frames in", folder)


def make_python(moments):
    pipeline = os.path.join(m.ROOT, "roblox_pipeline")
    here = os.getcwd()
    os.chdir(pipeline)  # preview.py reads shots/ relative to its own folder
    sys.path.insert(0, pipeline)
    import preview  # noqa: E402
    os.chdir(here)
    folder = os.path.join(OUT, "python_line")
    os.makedirs(folder, exist_ok=True)
    for mo in moments:
        img = preview.render(mo["t"])
        cv2.imwrite(os.path.join(folder, mo["shot"] + ".jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("python_line:", len(moments), "renders in", folder)


def load_cell(folder, shot):
    path = os.path.join(OUT, folder, shot + ".jpg")
    img = cv2.imread(path) if os.path.exists(path) else None
    if img is None:
        img = np.full((390, 520, 3), 60, np.uint8)
        cv2.putText(img, f"{folder}/{shot}: NOT CAPTURED", (14, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        print("missing:", os.path.join(OUT, folder, shot + ".jpg"))
        return img
    return tw.fit(img)


def build_sheet(rows, path):
    grid = []
    for mo in rows:
        shot, t, frame = mo["shot"], mo["t"], mo["frame"]
        movie = load_cell("real", shot)
        wire = load_cell("python_line", shot)
        studio = load_cell("roblox", shot)
        h = min(movie.shape[0], wire.shape[0], studio.shape[0])
        cells = [tw.label(c[:h], lbl) for c, lbl in (
            (movie, f"MOVIE  shot {shot}  t={t:.2f}  f{frame}"),
            (wire, f"PYTHON LINE  shot {shot}"),
            (studio, f"ROBLOX STUDIO  shot {shot}"))]
        sep = np.full((h, 6, 3), 255, np.uint8)
        grid.append(np.hstack([cells[0], sep, cells[1], sep, cells[2]]))
        grid.append(np.full((6, grid[-1].shape[1], 3), 255, np.uint8))
    sheet = np.vstack(grid)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("sheet:", os.path.relpath(path, m.ROOT), sheet.shape[:2], "shots", " ".join(r["shot"] for r in rows))


def make_sheets(moments):
    by_chunk = {}
    for mo in moments:
        by_chunk.setdefault(chunk_of(mo["shot"]), []).append(mo)
    for (num, name), rows in sorted(by_chunk.items()):
        parts = -(-len(rows) // ROWS_PER_SHEET)      # ceil: how many sheets this chunk needs
        size = -(-len(rows) // parts)                # balanced rows per sheet
        for p in range(parts):
            fname = f"chunk_{num}_{name}.jpg" if parts == 1 else f"chunk_{num}_{name}_part{p + 1}.jpg"
            build_sheet(rows[p * size:(p + 1) * size], os.path.join(OUT, "chunk_sheets", fname))


def main():
    steps = set(sys.argv[1:]) or {"real", "python", "sheets"}
    moments = load_moments()
    if "real" in steps:
        make_real(moments)
    if "python" in steps:
        make_python(moments)
    if "sheets" in steps:
        make_sheets(moments)


if __name__ == "__main__":
    main()
