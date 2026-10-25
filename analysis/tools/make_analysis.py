"""
make_analysis.py - builds the reference and comparison images that the Antigravity agent reads.

Run from the project root:
    python analysis/tools/make_analysis.py

Writes (all under analysis/):
  chunk_445_460_review/  our last preview render vs the movie, side by side
  chunk_465_480_next/    the next chunk's reference: cut list, cut plot, frame sheets, shot checkpoints

Movie time t maps to reference frame round((t - 15.856) * 23.976).
Our preview videos: frame 0 = chunk start (the shot's start time).
"""
import glob
import os

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "analysis")
REF = glob.glob(os.path.join(ROOT, "reference", "*full video*"))[0]
OFF, REF_FPS = 15.856, 23.976
W = 960                                   # width of every image written here


def ref_cap():
    return cv2.VideoCapture(REF)


def ref_frame(cap, t):
    cap.set(cv2.CAP_PROP_POS_FRAMES, round((t - OFF) * REF_FPS))
    ok, fr = cap.read()
    return fr if ok else None


def active_rows(cap):
    """Letterbox: the rows that hold picture (the reference has black bars)."""
    fr = ref_frame(cap, 65.0)
    rows = np.where(fr.mean(axis=(1, 2)) > 8)[0]
    return rows.min(), rows.max() + 1


def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(out, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    return out


def fit(img, w=W):
    return cv2.resize(img, (w, int(img.shape[0] * w / img.shape[1])), interpolation=cv2.INTER_AREA)


def save(path, img):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 92])


def contact(frames, cols, cell_w=480):
    """frames: list of labelled images, same size. Returns one grid image."""
    h = int(frames[0].shape[0] * cell_w / frames[0].shape[1])
    cells = [cv2.resize(f, (cell_w, h)) for f in frames]
    while len(cells) % cols:
        cells.append(np.zeros_like(cells[0]))
    rows = [np.hstack(cells[i:i + cols]) for i in range(0, len(cells), cols)]
    return np.vstack(rows)


# ---------------------------------------------------------------- 1. previous chunk: 445-460
def review_previous_chunk(cap, top, bot):
    start, dur = 63.404, 4.379
    prev = cv2.VideoCapture(os.path.join(ROOT, "chunk_445_460_preview.mp4"))
    fps = prev.get(cv2.CAP_PROP_FPS)
    n = int(prev.get(cv2.CAP_PROP_FRAME_COUNT))
    pairs = []
    t = start + 0.05
    while t < start + dur - 0.05:
        r = ref_frame(cap, t)
        r = fit(r[top:bot])
        idx = min(n - 1, int(round((t - start) * fps)))
        prev.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, ours = prev.read()
        ours = fit(ours) if ok else np.zeros_like(r)
        pair = np.vstack([label(r, f"MOVIE  t={t:.2f}  frame {round((t - OFF) * REF_FPS)}"),
                          label(ours, f"OURS (preview)  frame {idx}")])
        save(os.path.join(OUT, "chunk_445_460_review", "pairs", f"pair_{t:.2f}.jpg"), pair)
        pairs.append(pair)
        t += 0.5
    save(os.path.join(OUT, "chunk_445_460_review", "overview_pairs.jpg"), contact(pairs, 2, 640))
    print("review: wrote", len(pairs), "movie/ours pairs")


# ---------------------------------------------------------------- 2. next chunk: 465-480
def diff_curve(cap, t0, t1):
    """Histogram L1 difference between consecutive reference frames (cut detector)."""
    cap.set(cv2.CAP_PROP_POS_FRAMES, round((t0 - OFF) * REF_FPS))
    prev, times, vals = None, [], []
    for i in range(round((t0 - OFF) * REF_FPS), round((t1 - OFF) * REF_FPS)):
        ok, fr = cap.read()
        if not ok:
            break
        th = cv2.resize(fr, (160, 84))
        h = cv2.calcHist([th], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        h = h / h.sum()
        if prev is not None:
            times.append(OFF + i / REF_FPS)
            vals.append(float(np.abs(h - prev).sum()))
        prev = h
    return np.array(times), np.array(vals)


def next_chunk(cap, top, bot):
    base = os.path.join(OUT, "chunk_465_480_next")
    t0, t1 = 67.60, 72.90
    times, vals = diff_curve(cap, t0, t1)

    # planned shot starts from scene.py TIMELINE (keep this list in sync if the timeline changes)
    planned = [("465", 67.783), ("470", 68.534), ("475", 70.536), ("480", 71.662)]
    # local peaks above 0.2: soft cuts between similar-coloured shots score ~0.25-0.35, so 0.5 misses them.
    # The pixel column (mean grey difference between the two frames) confirms: a hard cut is > 12.
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    cuts = []
    for k in range(1, len(vals) - 1):
        if vals[k] > 0.2 and vals[k] >= vals[k - 1] and vals[k] >= vals[k + 1]:
            a = ref_frame(cap, times[k] - 1.5 / REF_FPS)
            b = ref_frame(cap, times[k] + 0.5 / REF_FPS)
            px = float(np.abs(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(int) - cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(int)).mean()) if a is not None and b is not None else -1
            cuts.append((times[k], vals[k], px))
    lines = ["Reference cut list, movie 67.60-72.90 s (histogram peaks > 0.2; pixel = mean grey difference across the cut).",
             "pixel > 12 = hard cut. Soft cuts (similar colours) score low on hist. Motion blur and flashes can also peak: check each visually.",
             "", f"{'movie t':>9}  {'frame':>6}  {'hist':>6}  {'pixel':>6}   nearest planned shot start (ms off)"]
    for t, v, px in cuts:
        near = min(planned, key=lambda p: abs(p[1] - t))
        lines.append(f"{t:9.3f}  {round((t - OFF) * REF_FPS):6d}  {v:6.2f}  {px:6.1f}   shot {near[0]} at {near[1]:.3f}"
                     f" ({(t - near[1]) * 1000:+.0f} ms)")
    lines += ["", "Planned shot starts in scene.py (465-480) and whether a reference cut sits on them:"]
    for name, ts in planned:
        hit = [t for t, _, _ in cuts if abs(t - ts) < 0.06]
        lines.append(f"  shot {name} at {ts:.3f}: " + (f"cut found at {hit[0]:.3f}" if hit else "NO cut within 60 ms"))
    save_text(os.path.join(base, "cuts.txt"), "\n".join(lines) + "\n")

    fig, ax = plt.subplots(figsize=(12, 3.6), dpi=110)
    ax.plot(times, vals, lw=1)
    ax.axhline(0.2, color="r", ls="--", lw=0.8, label="candidate threshold 0.2")
    for name, ts in planned:
        ax.axvline(ts, color="g", lw=1)
        ax.text(ts + 0.03, ax.get_ylim()[1] * 0.9, f"shot {name}", color="g", fontsize=8)
    ax.set_xlabel("movie time (s)")
    ax.set_ylabel("histogram difference")
    ax.set_title("Reference cut detector, 67.6-72.9 s (green = planned shot starts)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    os.makedirs(base, exist_ok=True)
    fig.savefig(os.path.join(base, "cut_plot.png"))
    plt.close(fig)

    # every 0.25 s from 67.5 to 73.0, labelled, in sheets of 12
    tiles = []
    t = 67.50
    while t <= 73.001:
        fr = fit(ref_frame(cap, t)[top:bot], 480)
        tiles.append(label(fr, f"t={t:.2f} f{round((t - OFF) * REF_FPS)}"))
        t += 0.25
    for s in range(0, len(tiles), 12):
        save(os.path.join(base, "sheets", f"sheet_{s // 12 + 1}.jpg"), contact(tiles[s:s + 12], 3, 480))

    # the four planned shots: first, middle, last frame, full size
    for name, ts in planned:
        dur = {"465": 0.751, "470": 2.002, "475": 1.126, "480": 1.209}[name]
        shots = []
        for tt in (ts + 0.04, ts + dur / 2, ts + dur - 0.04):
            shots.append(label(fit(ref_frame(cap, tt)[top:bot]), f"SHOT {name}  t={tt:.2f}  f{round((tt - OFF) * REF_FPS)}"))
        save(os.path.join(base, "shots", f"shot_{name}_ref.jpg"), np.vstack(shots))
    print("next: cut candidates", len(cuts), "-> ", os.path.join(base, "cuts.txt"))


def save_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    cap = ref_cap()
    top, bot = active_rows(cap)
    print("letterbox picture rows:", top, bot)
    review_previous_chunk(cap, top, bot)
    next_chunk(cap, top, bot)
