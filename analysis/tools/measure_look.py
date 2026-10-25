"""measure_look.py - colour stats of Studio captures against the reference at the same movie times.
    python analysis/tools/measure_look.py t1:capture1 t2:capture2 ...
Prints brightness (L*), contrast (L* std), saturation, shadows (p5) and highlights (p95), movie vs Roblox."""
import glob, os, sys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_analysis as m

def stats(img):
    img = img[60:-20]
    L = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[..., 0].astype(float) * 100 / 255
    S = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 1].mean() / 2.55
    return np.array([L.mean(), L.std(), S, np.percentile(L, 5), np.percentile(L, 95)])

def ref_at(t, full, clip, fps):
    if t < m.OFF:
        clip.set(cv2.CAP_PROP_POS_FRAMES, round(t * fps)); return clip.read()[1]
    return m.ref_frame(full, t)

full = m.ref_cap()
clip = cv2.VideoCapture(glob.glob(os.path.join(m.ROOT, "reference", "*5.88sec clip*"))[0]); fps = clip.get(cv2.CAP_PROP_FPS)
R, B = [], []
names = ["bright", "contrast", "sat", "shadow", "highl"]
print(f"{'t':>6} " + " ".join(f"{n:>13}" for n in names) + "   (movie/roblox)")
for arg in sys.argv[1:]:
    t, p = arg.split(":", 1); t = float(t)
    r, b = stats(ref_at(t, full, clip, fps)), stats(cv2.imread(p))
    R.append(r); B.append(b)
    print(f"{t:6.2f} " + " ".join(f"{x:6.1f}/{y:6.1f}" for x, y in zip(r, b)))
R, B = np.array(R), np.array(B)
print("  mean " + " ".join(f"{x:6.1f}/{y:6.1f}" for x, y in zip(R.mean(0), B.mean(0))))
