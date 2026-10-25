"""Try COMEON arm values: patch scene.py, rebuild, print the overlay numbers. Restores nothing; the last try stays."""
import re, subprocess, sys
PIPE = "roblox_pipeline"
def try_pose(L_up, L_lo, L_palm, R_up, R_lo):
    s = open(f"{PIPE}/scene.py", encoding="utf-8").read()
    new = (f"COMEON = dict(L_up={L_up}, L_lo={L_lo}, L_palm={L_palm},\n"
           f"              R_up={R_up}, R_lo={R_lo}, R_palm=(-1, 0, 0.2), stance=0.12)")
    s2, n = re.subn(r"COMEON = dict\(.*?stance=0\.12\)", new, s, flags=re.S)
    assert n == 1, n
    open(f"{PIPE}/scene.py", "w", encoding="utf-8").write(s2)
    subprocess.run([sys.executable, "scene.py"], cwd=PIPE, capture_output=True, timeout=170)
    out = subprocess.run([sys.executable, "../analysis/tools/overlay_pose.py", "20.85"], capture_output=True, text=True, timeout=170)
    print(f"try L_up={L_up} L_lo={L_lo} L_palm={L_palm} R_up={R_up} R_lo={R_lo}")
    print("
".join(l for l in out.stdout.splitlines() if "fist" in l or "stone" in l))