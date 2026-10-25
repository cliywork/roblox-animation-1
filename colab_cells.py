# =====================================================================================
# CELL 1 — SETUP. Run this first in EVERY Colab session (Runtime -> Change runtime type -> T4 GPU).
# First run: ~15 min (downloads ~6 GB, saves it to Google Drive). After a reset: ~5-8 min.
# =====================================================================================
import os, subprocess, shutil, zipfile, getpass, requests, time

def sh(cmd):
    r = subprocess.run(cmd, shell=True, executable="/bin/bash")
    if r.returncode:
        raise SystemExit(f"❌ step failed (send me the output above): {cmd.splitlines()[0][:90]}")

if subprocess.run("nvidia-smi", shell=True, capture_output=True).returncode:
    raise SystemExit("❌ No GPU. Runtime -> Change runtime type -> T4 GPU -> Save, then run this cell again.")

from google.colab import drive, files
drive.mount("/content/drive")
CACHE = "/content/drive/MyDrive/gvhmr_cache"          # survives Colab resets
G, CK = "/content/GVHMR", "/content/GVHMR/inputs/checkpoints"
os.makedirs(f"{CACHE}/checkpoints", exist_ok=True)

# ---- 1. GVHMR code (check .git, not just the folder) --------------------------------
if not os.path.isdir(f"{G}/.git"):
    print(">>> downloading GVHMR code")
    sh("rm -rf /content/GVHMR_src && git clone -q --recursive https://github.com/zju3dv/GVHMR.git /content/GVHMR_src"
       " && mkdir -p /content/GVHMR && cp -rn /content/GVHMR_src/. /content/GVHMR/ 2>/dev/null; rm -rf /content/GVHMR_src")

# ---- 2. Python 3.10 environment -------------------------------------------------------
if not os.path.exists("/content/gvenv/.ready"):
    print(">>> installing the Python 3.10 environment (5-8 min)")
    sh(r"""
set -euo pipefail
cd /content/GVHMR
pip install -q uv
[ -x /content/gvenv/bin/python ] || uv venv -q /content/gvenv --python 3.10 --seed
PY=/content/gvenv/bin/python
printf "numpy==1.23.5\nsetuptools<70\n" > /content/constraints.txt
grep -v -E '^(jupyter|ipdb|black|chumpy|cython_bbox)([ =#]|$)' requirements.txt > /content/req_colab.txt
uv pip install -q --python $PY --index-strategy unsafe-best-match -c /content/constraints.txt -r /content/req_colab.txt "pytorch-lightning==2.3.0"
uv pip install -q --python $PY -c /content/constraints.txt cython "setuptools<70" wheel
uv pip install -q --python $PY --no-build-isolation -c /content/constraints.txt chumpy cython_bbox
uv pip install -q --python $PY --no-deps -e .
uv pip install -q --python $PY "numpy==1.23.5" "setuptools>=68,<70"
touch /content/gvenv/.ready
""")

# ---- 3. Checkpoints + body models: Drive cache first, then download -----------------
NEED = {"gvhmr/gvhmr_siga24_release.ckpt": 150e6, "hmr2/epoch=10-step=25000.ckpt": 2.0e9,
        "vitpose/vitpose-h-multi-coco.pth": 2.0e9, "yolo/yolov8x.pt": 100e6,
        "body_models/smpl/SMPL_NEUTRAL.pkl": 200e6, "body_models/smplx/SMPLX_NEUTRAL.npz": 100e6}
def have(p, root=CK):
    f = f"{root}/{p}"; return os.path.exists(f) and os.path.getsize(f) > NEED[p]

for p in NEED:
    if not have(p) and have(p, f"{CACHE}/checkpoints"):
        print(">>> restoring from Drive:", p)
        os.makedirs(os.path.dirname(f"{CK}/{p}"), exist_ok=True)
        shutil.copy(f"{CACHE}/checkpoints/{p}", f"{CK}/{p}")

from huggingface_hub import hf_hub_download
for p in NEED:
    if not p.startswith("body_models") and not have(p):
        print(">>> downloading", p); hf_hub_download("camenduru/GVHMR", p, local_dir=CK)

def mpi_extract(domain, sfile, inner, p, login):
    """Download an MPI zip with the given login, extract one file. Returns False on bad login."""
    z = f"/content/{sfile}"
    url = f"https://download.is.tue.mpg.de/download.php?domain={domain}&sfile={sfile}&resume=1"
    with requests.post(url, data=dict(zip(("username", "password"), login)), stream=True, timeout=60) as r:
        if "text/html" in r.headers.get("content-type", ""):
            return False
        total, done, t = int(r.headers.get("content-length", 0)), 0, time.time()
        print(f">>> downloading {sfile} ({total // 1_000_000} MB)")
        with open(z + ".part", "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk); done += len(chunk)
                if time.time() - t > 10:
                    print(f"  {done // 1_000_000} / {total // 1_000_000} MB"); t = time.time()
    os.replace(z + ".part", z)
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(inner)][0]
        os.makedirs(os.path.dirname(f"{CK}/{p}"), exist_ok=True)
        with zf.open(name) as s, open(f"{CK}/{p}", "wb") as d: shutil.copyfileobj(s, d)
    os.remove(z); print("ok ", p); return True

login = None
if not have("body_models/smplx/SMPLX_NEUTRAL.npz"):
    login = (input("smpl-x.is.tue.mpg.de email: "), getpass.getpass("password: "))
    if not mpi_extract("smplx", "models_smplx_v1_1.zip", "SMPLX_NEUTRAL.npz", "body_models/smplx/SMPLX_NEUTRAL.npz", login):
        raise SystemExit("❌ SMPL-X login failed (or license not accepted on smpl-x.is.tue.mpg.de)")
if not have("body_models/smpl/SMPL_NEUTRAL.pkl"):
    args = ("smpl", "SMPL_python_v.1.1.0.zip", "basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl", "body_models/smpl/SMPL_NEUTRAL.pkl")
    if not (login and mpi_extract(*args, login)):
        login = (input("smpl.is.tue.mpg.de email: "), getpass.getpass("password: "))
        if not mpi_extract(*args, login):
            raise SystemExit("❌ SMPL login failed (or license not accepted on smpl.is.tue.mpg.de)")
login = None

for p in NEED:                                         # save anything new to Drive for next time
    if have(p) and not have(p, f"{CACHE}/checkpoints"):
        print(">>> saving to Drive:", p)
        os.makedirs(os.path.dirname(f"{CACHE}/checkpoints/{p}"), exist_ok=True)
        shutil.copy(f"{CK}/{p}", f"{CACHE}/checkpoints/{p}")

# ---- 4. Roblox converter (uploaded once, then kept on Drive) ---------------------------
if not os.path.exists(f"{CACHE}/smpl_to_r15.py"):
    print(">>> pick smpl_to_r15.py from Desktop\\3d Animation\\roblox_pipeline (only asked once)")
    up = files.upload(); shutil.move(list(up.keys())[0], f"{CACHE}/smpl_to_r15.py")
shutil.copy(f"{CACHE}/smpl_to_r15.py", "/content/smpl_to_r15.py")

# ---- 5. Check everything -------------------------------------------------------------------
ENV = {**os.environ, "MPLBACKEND": "Agg", "PYTHONPATH": G}
check = """
import importlib, numpy, torch
for m in ["pytorch3d","pytorch_lightning","ultralytics","chumpy","smplx","hmr4d"]: importlib.import_module(m)
from hmr4d.utils.smplx_utils import make_smplx
make_smplx("supermotion"); make_smplx("smpl")
assert numpy.__version__.startswith("1.23") and torch.cuda.is_available()
print("environment, body models, GPU: ok")
"""
r = subprocess.run(["/content/gvenv/bin/python", "-c", check], cwd=G, env=ENV, capture_output=True, text=True)
missing = [p for p in NEED if not have(p)]
print(r.stdout, r.stderr[-1500:] if r.returncode else "", "missing:", missing or "none")
print("\n✅ ALL READY — run the SHOT cell" if r.returncode == 0 and not missing else "\n❌ send me this output")


# =====================================================================================
# CELL 2 — SHOT. Upload one clip -> GVHMR -> preview -> Roblox .rbxmx download.
# Give every clip a different file name: GVHMR reuses old results for a name it has seen.
# =====================================================================================
import os, re, shutil, subprocess
from google.colab import files
from IPython.display import Video, display

STATIC_CAMERA = True        # False if the camera moves in this shot

up = files.upload()
src = list(up.keys())[0]
SHOT = re.sub(r"[^A-Za-z0-9_]", "_", os.path.splitext(src)[0])
os.makedirs(f"{G}/inputs/videos", exist_ok=True)

# GVHMR re-writes every video at 30 fps frame-for-frame, so a 24 fps movie clip would play 25% fast.
# Resample to 30 fps first (repeats frames, keeps real-time speed). Audio dropped; not needed.
fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                      "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
print(f"source frame rate: {fps}  -> converting to 30 fps")
r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", "fps=30", "-an",
                    "-c:v", "libx264", "-crf", "17", f"{G}/inputs/videos/{SHOT}.mp4"], capture_output=True, text=True)
if r.returncode:
    raise SystemExit("❌ ffmpeg could not read this clip:\n" + r.stderr[-1500:])
os.remove(src)

cmd = ["/content/gvenv/bin/python", "tools/demo/demo.py", f"--video=inputs/videos/{SHOT}.mp4"] + (["-s"] if STATIC_CAMERA else [])
r = subprocess.run(cmd, cwd=G, env=ENV, capture_output=True, text=True)
print("\n".join(l for l in r.stdout.splitlines() if "[INFO]" in l)[-3000:])
OUT = f"{G}/outputs/demo/{SHOT}"
if r.returncode or not os.path.exists(f"{OUT}/hmr4d_results.pt"):
    raise SystemExit("❌ GVHMR failed:\n" + r.stderr[-3000:])

display(Video(f"{OUT}/{SHOT}_3_incam_global_horiz.mp4", embed=True, width=900))

r = subprocess.run(["/content/gvenv/bin/python", "/content/smpl_to_r15.py", f"{OUT}/hmr4d_results.pt",
                    f"/content/{SHOT}.rbxmx", "--name", SHOT], cwd=G, env=ENV, capture_output=True, text=True)
print(r.stdout, r.stderr[-1500:])
files.download(f"/content/{SHOT}.rbxmx")
print(f"✅ {SHOT}.rbxmx downloaded — in Studio: Workspace > Insert from File, then Play (it gets its own button)")
