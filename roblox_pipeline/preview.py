"""
preview.py — render the timeline as stick figures / HUD previews through the planned cameras, side by side with
the reference movie frames. Checks framing/timing without opening Studio.

    python preview.py <reference.mp4> <out_dir> [times...]
"""
import os, sys
import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R

import scene
from rbxmx_io import read_shot

W_IMG, H_IMG = 960, int(960 / scene.FRAME_ASPECT)
COLORS = {"Thanos": (200, 80, 160), "IronMan": (40, 40, 220)}
BONES = [  # (part, rest point a, rest point b)
    ("LowerTorso", (0, 2.0, 0), (0, 2.4, 0)), ("LowerTorso", (-0.5, 2.0, 0), (0.5, 2.0, 0)),
    ("UpperTorso", (0, 2.4, 0), (0, 4.0, 0)), ("UpperTorso", (-1.5, 3.75, 0), (1.5, 3.75, 0)),
    ("Head", (0, 4.0, 0), (0, 5.1, 0)),
    ("LeftUpperArm", (-1.5, 3.75, 0), (-1.5, 2.95, 0)), ("LeftLowerArm", (-1.5, 2.95, 0), (-1.5, 2.15, 0)),
    ("LeftHand", (-1.5, 2.15, 0), (-1.5, 1.75, 0)),
    ("RightUpperArm", (1.5, 3.75, 0), (1.5, 2.95, 0)), ("RightLowerArm", (1.5, 2.95, 0), (1.5, 2.15, 0)),
    ("RightHand", (1.5, 2.15, 0), (1.5, 1.75, 0)),
    ("LeftUpperLeg", (-0.5, 2.0, 0), (-0.5, 1.15, 0)), ("LeftLowerLeg", (-0.5, 1.15, 0), (-0.5, 0.3, 0)),
    ("LeftFoot", (-0.5, 0.3, 0), (-0.5, 0.0, -0.5)),
    ("RightUpperLeg", (0.5, 2.0, 0), (0.5, 1.15, 0)), ("RightLowerLeg", (0.5, 1.15, 0), (0.5, 0.3, 0)),
    ("RightFoot", (0.5, 0.3, 0), (0.5, 0.0, -0.5)),
]

ANIMS = {f[:-6]: read_shot(os.path.join(scene.SHOTS, f)) for f in os.listdir(scene.SHOTS) if f.endswith(".rbxmx")}


def rig_frame(rig, tau):
    """Which animation + frame a rig shows at movie time tau (holds the last pose between shots)."""
    anim, local = scene.PREROLL[rig], 0.0
    for sh in scene.TIMELINE:
        if rig in sh["play"] and sh["start"] <= tau:
            anim, local = sh["play"][rig], tau - sh["start"]
    t, T = ANIMS[anim]
    i = min(int(round(local * scene.FPS)), len(t) - 1)
    return T, i


def to_world(rig, p):
    r = scene.RIGS[rig]
    return np.array(r["pos"], float) + R.from_euler("y", r["yaw"], degrees=True).apply(r["scale"] * np.asarray(p))


def target(tp, tau):
    name, off = tp
    if name == "World":
        return np.array(off, float)
    rig, part = name.split(".")
    T, i = rig_frame(rig, tau)
    W, P = scene.fk(T, i)
    c = scene.CENTER[part]
    local = np.array(c, float) if part == "HumanoidRootPart" else scene.local_point(W, P, part, c)
    return to_world(rig, local) + np.asarray(off, float)


def camera(tau):
    sh = [s for s in scene.TIMELINE if s["start"] <= tau][-1]
    lt, keys = tau - sh["start"], sh["cam"]
    k0 = [k for k in keys if k["t"] <= lt][-1]
    k1 = next((k for k in keys if k["t"] > lt), k0)
    u = 0 if k1 is k0 else scene.ease((lt - k0["t"]) / (k1["t"] - k0["t"]))
    pos = (1 - u) * target(k0["pos"], tau) + u * target(k1["pos"], tau)
    look = (1 - u) * target(k0["look"], tau) + u * target(k1["look"], tau)
    pos = look + (pos - look) * getattr(scene, "PULLBACK", 1.0)
    roll = (1 - u) * k0.get("roll", 0) + u * k1.get("roll", 0)
    return sh, pos, look, (1 - u) * k0["fov"] + u * k1["fov"], roll


def render_hud(sh, tau):
    """Dedicated Inside HUD renderer (Shots 395, 405, 415): upright head, expressions, cyan HUD interfaces."""
    img = np.full((H_IMG, W_IMG, 3), 12, np.uint8)
    cx, cy = W_IMG // 2, H_IMG // 2

    # Draw dark cockpit vignette oval
    cv2.ellipse(img, (cx, cy), (int(W_IMG * 0.44), int(H_IMG * 0.48)), 0, 0, 360, (22, 18, 14), -1)
    cv2.ellipse(img, (cx, cy), (int(W_IMG * 0.38), int(H_IMG * 0.44)), 0, 0, 360, (30, 24, 18), -1)

    # Cyan holographic HUD borders & telemetry
    CYAN = (255, 220, 70)       # BGR cyan
    ICE = (255, 245, 200)       # BGR light ice-blue
    RED = (50, 50, 255)         # BGR red warning

    # Left & Right HUD arcs
    cv2.ellipse(img, (cx - 280, cy), (120, 180), 0, -60, 60, CYAN, 2, cv2.LINE_AA)
    cv2.ellipse(img, (cx + 280, cy), (120, 180), 0, 120, 240, CYAN, 2, cv2.LINE_AA)

    # Telemetry bars on left
    for idx, y_off in enumerate(range(-120, 140, 25)):
        w_bar = int(40 + np.sin(idx * 1.5 + tau) * 20)
        cv2.rectangle(img, (cx - 360, cy + y_off), (cx - 360 + w_bar, cy + y_off + 4), CYAN, -1)
        cv2.putText(img, f"ARC_{idx*12}%", (cx - 430, cy + y_off + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, ICE, 1)

    # Telemetry graphs & readouts on right
    for idx, y_off in enumerate(range(-120, 140, 25)):
        w_bar = int(45 + np.cos(idx * 1.2 + tau) * 25)
        cv2.rectangle(img, (cx + 360 - w_bar, cy + y_off), (cx + 360, cy + y_off + 4), CYAN, -1)
        cv2.putText(img, f"SYS_{idx*8:02d}", (cx + 375, cy + y_off + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, ICE, 1)

    # Targeting reticle
    cv2.circle(img, (cx - 160, cy + 90), 28, CYAN, 1, cv2.LINE_AA)
    cv2.circle(img, (cx - 160, cy + 90), 8, ICE, -1)
    cv2.line(img, (cx - 200, cy + 90), (cx - 120, cy + 90), CYAN, 1)

    # Specific shot variations
    shot_id = sh.get("shot", "")
    if shot_id in ("060", "080"):
        # Centered serious/focused face (Row 7: Tony Stark locked-in close-up inside HUD)
        cv2.ellipse(img, (cx, cy + 15), (100, 135), 0, 0, 360, (75, 60, 48), -1)   # head base
        # Focused level eyes looking straight ahead
        cv2.ellipse(img, (cx - 32, cy - 10), (16, 11), 0, 0, 360, (230, 230, 230), -1)
        cv2.ellipse(img, (cx + 32, cy - 10), (16, 11), 0, 0, 360, (230, 230, 230), -1)
        cv2.circle(img, (cx - 32, cy - 10), 6, (20, 20, 20), -1)
        cv2.circle(img, (cx + 32, cy - 10), 6, (20, 20, 20), -1)
        # Serious straight eyebrows
        cv2.line(img, (cx - 52, cy - 25), (cx - 15, cy - 23), (25, 20, 15), 3, cv2.LINE_AA)
        cv2.line(img, (cx + 15, cy - 23), (cx + 52, cy - 25), (25, 20, 15), 3, cv2.LINE_AA)
        # Serious mouth (straight line, determined, no smile!)
        cv2.line(img, (cx - 24, cy + 62), (cx + 24, cy + 62), (35, 25, 25), 3, cv2.LINE_AA)
        # Stark goatee / beard
        cv2.polylines(img, [np.array([[cx - 22, cy + 70], [cx, cy + 115], [cx + 22, cy + 70]])], False, (25, 20, 20), 2)
        cv2.putText(img, "HUD: TONY STARK FOCUSED CLOSE-UP (LOCKED-IN)", (cx - 210, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, CYAN, 1)

    elif shot_id == "100":
        # Fierce intense defiance: "My only curse is you" (Row 11)
        cv2.ellipse(img, (cx, cy + 15), (100, 135), 0, 0, 360, (75, 60, 48), -1)
        # Narrowed glaring eyes
        cv2.ellipse(img, (cx - 32, cy - 10), (16, 9), 5, 0, 360, (230, 230, 230), -1)
        cv2.ellipse(img, (cx + 32, cy - 10), (16, 9), -5, 0, 360, (230, 230, 230), -1)
        cv2.circle(img, (cx - 32, cy - 10), 6, (20, 20, 20), -1)
        cv2.circle(img, (cx + 32, cy - 10), 6, (20, 20, 20), -1)
        # Furrowed angry eyebrows angled down into nose
        cv2.line(img, (cx - 52, cy - 22), (cx - 15, cy - 30), (25, 20, 15), 4, cv2.LINE_AA)
        cv2.line(img, (cx + 15, cy - 30), (cx + 52, cy - 22), (25, 20, 15), 4, cv2.LINE_AA)
        # Fierce speaking / gritted mouth
        cv2.ellipse(img, (cx, cy + 62), (18, 9), 0, 0, 360, (30, 20, 20), -1)
        cv2.line(img, (cx - 15, cy + 62), (cx + 15, cy + 62), (220, 220, 220), 2, cv2.LINE_AA)
        # Stark goatee / beard
        cv2.polylines(img, [np.array([[cx - 22, cy + 70], [cx, cy + 115], [cx + 22, cy + 70]])], False, (25, 20, 20), 2)
        cv2.putText(img, "HUD: 'MY ONLY CURSE IS YOU' (INTENSE DEFIANCE)", (cx - 220, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, CYAN, 1)

    elif shot_id == "395":
        # Upright, centered alarmed face (wide eyes, raised brows, open mouth)
        cv2.ellipse(img, (cx, cy + 10), (95, 125), 0, 0, 360, (75, 60, 48), -1)   # head base
        # Wide alarmed eyes
        cv2.circle(img, (cx - 32, cy - 15), 18, (230, 230, 230), -1)
        cv2.circle(img, (cx + 32, cy - 15), 18, (230, 230, 230), -1)
        cv2.circle(img, (cx - 32, cy - 15), 9, (20, 20, 20), -1)
        cv2.circle(img, (cx + 32, cy - 15), 9, (20, 20, 20), -1)
        # Raised arched eyebrows
        cv2.ellipse(img, (cx - 34, cy - 38), (22, 10), -10, 190, 350, (30, 20, 15), 3, cv2.LINE_AA)
        cv2.ellipse(img, (cx + 34, cy - 38), (22, 10), 10, 190, 350, (30, 20, 15), 3, cv2.LINE_AA)
        # Shocked / parted mouth
        cv2.ellipse(img, (cx, cy + 55), (18, 12), 0, 0, 360, (35, 20, 25), -1)
        # Stark goatee / beard
        cv2.polylines(img, [np.array([[cx - 20, cy + 65], [cx, cy + 105], [cx + 20, cy + 65]])], False, (25, 20, 20), 2)
        cv2.putText(img, "HUD: WIDE-EYED ALARM / THREAT LOCK", (cx - 160, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, CYAN, 1)

    elif shot_id == "405":
        # Three-quarter profile facing right (~48° yaw), brow cut, bright cyan glow on left
        # Left-side intense cyan flare / wash
        for r_bloom in range(160, 10, -20):
            cv2.circle(img, (cx - 180, cy - 20), r_bloom, (255, 180 + r_bloom // 3, 40), -1)
        # Head in 3/4 profile
        pts_head = np.array([[cx - 40, cy - 100], [cx + 60, cy - 90], [cx + 90, cy - 20], [cx + 80, cy + 60],
                             [cx + 30, cy + 110], [cx - 20, cy + 90], [cx - 60, cy + 20]])
        cv2.fillPoly(img, [pts_head], (75, 60, 48))
        # 3/4 Eye facing right
        cv2.ellipse(img, (cx + 40, cy - 15), (14, 10), 5, 0, 360, (230, 230, 230), -1)
        cv2.circle(img, (cx + 44, cy - 15), 6, (20, 20, 20), -1)
        # Brow cut with blood
        cv2.line(img, (cx + 28, cy - 36), (cx + 48, cy - 28), (20, 20, 180), 3, cv2.LINE_AA)
        cv2.circle(img, (cx + 44, cy - 22), 3, (20, 20, 200), -1)
        # Strained jawline
        cv2.line(img, (cx + 15, cy + 50), (cx + 45, cy + 50), (40, 25, 25), 2)
        cv2.putText(img, "HUD: THREE-QUARTER PROFILE + CYAN ENERGY BLOOM", (cx - 220, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, CYAN, 1)

    elif shot_id == "415":
        # Impact shake & wincing/grimace, blood on forehead, red/cyan warning border
        # Flashing warning borders
        cv2.rectangle(img, (15, 15), (W_IMG - 15, H_IMG - 15), RED, 4)
        cv2.rectangle(img, (22, 22), (W_IMG - 22, H_IMG - 22), CYAN, 2)
        # Head with pain grimace
        cv2.ellipse(img, (cx, cy + 10), (95, 125), 0, 0, 360, (75, 60, 48), -1)
        # Clenched wincing eyes (slits)
        cv2.line(img, (cx - 48, cy - 15), (cx - 18, cy - 12), (25, 20, 20), 4, cv2.LINE_AA)
        cv2.line(img, (cx + 18, cy - 12), (cx + 48, cy - 15), (25, 20, 20), 4, cv2.LINE_AA)
        # Furrowed brows
        cv2.line(img, (cx - 45, cy - 30), (cx - 15, cy - 22), (20, 15, 15), 4, cv2.LINE_AA)
        cv2.line(img, (cx + 15, cy - 22), (cx + 45, cy - 30), (20, 15, 15), 4, cv2.LINE_AA)
        # Blood streak down forehead & nose
        cv2.line(img, (cx - 10, cy - 50), (cx - 5, cy - 20), (20, 20, 200), 3, cv2.LINE_AA)
        cv2.line(img, (cx - 5, cy - 20), (cx - 3, cy + 15), (20, 20, 200), 3, cv2.LINE_AA)
        # Gritted teeth / pain grimace mouth
        cv2.line(img, (cx - 30, cy + 50), (cx + 30, cy + 52), (30, 20, 20), 4, cv2.LINE_AA)
        for tx in range(cx - 24, cx + 25, 8):
            cv2.line(img, (tx, cy + 46), (tx, cy + 56), (220, 220, 220), 1)
        cv2.putText(img, "HUD: IMPACT SHAKE / PAIN GRIMACE / WARNING BORDER", (cx - 240, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, RED, 1)

    cv2.putText(img, f"shot {sh['shot']}  t={tau:.2f}s  [HUD_MODE]", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return img


def render_ecu(sh, tau, shattered=False):
    """Dedicated ECU renderer (Shots 420, 430): red shoulder on left, cracked/shattered gold helmet on right."""
    img = np.full((H_IMG, W_IMG, 3), 32, np.uint8)

    # Dirt / rocky ground texture lines
    for gy in range(int(H_IMG * 0.4), H_IMG, 35):
        cv2.line(img, (0, gy), (W_IMG, gy + 15), (48, 42, 36), 2)
    # Red shoulder armor filling left third
    pts_shoulder = np.array([[0, 0], [int(W_IMG * 0.34), 0], [int(W_IMG * 0.38), H_IMG], [0, H_IMG]])
    cv2.fillPoly(img, [pts_shoulder], (30, 30, 180))   # BGR Iron Man red
    # Gold trim on shoulder
    cv2.polylines(img, [np.array([[int(W_IMG * 0.30), 0], [int(W_IMG * 0.34), H_IMG]])], False, (40, 170, 220), 4)

    # Gold/red helmet turned sideways in dirt on right
    hcx, hcy = int(W_IMG * 0.65), int(H_IMG * 0.58)
    cv2.ellipse(img, (hcx, hcy), (170, 120), -25, 0, 360, (30, 30, 180), -1)   # red base
    cv2.ellipse(img, (hcx + 15, hcy), (135, 95), -25, 0, 360, (40, 180, 230), -1) # gold faceplate

    if not shattered:
        # Shot 420: Punch 1 — Cracked battle-damaged faceplate
        cv2.line(img, (hcx - 40, hcy - 30), (hcx + 20, hcy + 10), (20, 20, 20), 3, cv2.LINE_AA)
        cv2.line(img, (hcx + 20, hcy + 10), (hcx + 70, hcy - 10), (20, 20, 20), 2, cv2.LINE_AA)
        cv2.line(img, (hcx + 10, hcy + 5), (hcx + 25, hcy + 45), (20, 20, 20), 2, cv2.LINE_AA)
        # Slit eye lit
        cv2.line(img, (hcx + 10, hcy - 20), (hcx + 55, hcy - 35), (255, 255, 230), 4, cv2.LINE_AA)
        cv2.putText(img, "ECU: PUNCH 1 — HELMET SLAMMED IN DIRT (CRACKED MASK)", (int(W_IMG * 0.28), H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    else:
        # Shot 430: Punch 2 — Shattered helmet (upper-left faceplate ripped off, exposing Tony's bruised forehead & eye)
        # Torn faceplate edge
        pts_shattered = np.array([[hcx - 50, hcy - 70], [hcx + 30, hcy - 60], [hcx + 10, hcy + 5], [hcx - 60, hcy - 10]])
        cv2.fillPoly(img, [pts_shattered], (65, 52, 42))  # exposed skin underneath
        # Bruised right eye & forehead
        cv2.ellipse(img, (hcx - 15, hcy - 30), (14, 10), -15, 0, 360, (140, 80, 110), -1) # purple bruise
        cv2.circle(img, (hcx - 15, hcy - 30), 4, (20, 20, 20), -1)   # pupil
        # Blood marks
        cv2.line(img, (hcx - 30, hcy - 50), (hcx - 20, hcy - 20), (20, 20, 190), 3, cv2.LINE_AA)
        # Jagged torn metal jagged border
        pts_jagged = np.array([[hcx - 60, hcy - 10], [hcx - 30, hcy], [hcx + 10, hcy + 5], [hcx + 20, hcy - 25], [hcx + 30, hcy - 60]])
        cv2.polylines(img, [pts_jagged], False, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.putText(img, "ECU: PUNCH 2 — SHATTERED HELMET (EXPOSED EYE & BROW)", (int(W_IMG * 0.26), H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)

    cv2.putText(img, f"shot {sh['shot']}  t={tau:.2f}s  [ECU_HELMET]", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return img


def render(tau):
    sh = [s for s in scene.TIMELINE if s["start"] <= tau][-1]
    shot_id = sh.get("shot", "")

    # Intercept Interior HUD shots
    if sh.get("hud") in ("mask", "lock") or shot_id in ("060", "080", "100", "395", "405", "415"):
        return render_hud(sh, tau)

    # Intercept Extreme Close-Ups (ECU)
    if shot_id == "420":
        return render_ecu(sh, tau, shattered=False)
    if shot_id == "430":
        return render_ecu(sh, tau, shattered=True)

    sh, pos, look, fov, roll = camera(tau)
    img = np.full((H_IMG, W_IMG, 3), 40, np.uint8)
    f = (look - pos) / np.linalg.norm(look - pos)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    if roll != 0:
        rot = R.from_rotvec(np.radians(roll) * f)
        r = rot.apply(r)
        u = rot.apply(u)
    k = (H_IMG / 2) / np.tan(np.radians(fov) / 2)

    def proj(p):
        d = p - pos; z = d @ f
        return None if z < 0.05 else (int(W_IMG / 2 + (d @ r) / z * k), int(H_IMG / 2 - (d @ u) / z * k))

    for gx in range(-60, 61, 5):                      # ground grid
        for a, b in (((gx, 0, -80), (gx, 0, 40)), ((-60, 0, gx - 20), (60, 0, gx - 20))):
            pa, pb = proj(np.array(a, float)), proj(np.array(b, float))
            if pa and pb:
                cv2.line(img, pa, pb, (70, 70, 70), 1)

    hidden_rig = sh.get("hide")
    for rig in scene.RIGS:
        if rig == hidden_rig:
            continue
        T, i = rig_frame(rig, tau)
        W, P = scene.fk(T, i)
        for part, a, b in BONES:
            pa = proj(to_world(rig, scene.local_point(W, P, part, a)))
            pb = proj(to_world(rig, scene.local_point(W, P, part, b)))
            if pa and pb:
                cv2.line(img, pa, pb, COLORS[rig], max(2, int(6 * scene.RIGS[rig]["scale"])), cv2.LINE_AA)
        for hand, axis in scene.PALM_AXIS.items():     # yellow arrow = which way the palm faces
            c = scene.local_point(W, P, hand, scene.CENTER[hand])
            pa, pb = proj(to_world(rig, c)), proj(to_world(rig, c + 0.6 * W[hand] @ axis))
            if pa and pb:
                cv2.arrowedLine(img, pa, pb, (0, 230, 255), 2, cv2.LINE_AA, tipLength=0.3)

    # Shot-specific wireframe event overlays:
    if shot_id == "010" and tau >= 0.55:
        # Row 2: Orange-red energy streak / projectile swat
        p_head = proj(to_world("Thanos", (0, 4.6, 0)))
        if p_head:
            flare_start = (p_head[0] + 160, p_head[1] - 8)
            flare_end = (p_head[0] - 60, p_head[1] - 8)
            cv2.line(img, flare_start, flare_end, (20, 120, 255), 6, cv2.LINE_AA)
            cv2.line(img, flare_start, flare_end, (180, 230, 255), 2, cv2.LINE_AA)
            cv2.circle(img, (p_head[0] + 30, p_head[1] - 8), 10, (50, 180, 255), -1)
            cv2.putText(img, "FX: ENERGY FLARE DEFLECTION", (flare_end[0] - 90, flare_end[1] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (30, 160, 255), 1)

    elif shot_id == "020":
        # Row 3: Gauntlet palm glowing core + sunburst
        p_hand = proj(to_world("Thanos", scene.local_point(W, P, "LeftHand", scene.CENTER["LeftHand"])))
        if p_hand:
            cv2.circle(img, p_hand, 20, (200, 230, 255), -1)
            cv2.circle(img, p_hand, 35, (50, 160, 255), 2, cv2.LINE_AA)
            cv2.putText(img, "GAUNTLET PALM CORE (WHITE-ORANGE GLOW)", (p_hand[0] - 80, p_hand[1] + 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 255), 1)
        sun_pt = (int(W_IMG * 0.88), int(H_IMG * 0.85))
        for r_s in range(50, 5, -10):
            cv2.circle(img, sun_pt, r_s, (40, 180, 255), -1)

    elif shot_id == "040":
        # Row 4: Iron Man streaking across upper-left sky (fallback trajectory tracker)
        pt_streak_start = (int(W_IMG * 0.18), int(H_IMG * 0.22))
        pt_streak_end = (int(W_IMG * 0.42), int(H_IMG * 0.32))
        cv2.line(img, pt_streak_start, pt_streak_end, (40, 180, 255), 4, cv2.LINE_AA)
        cv2.line(img, pt_streak_start, pt_streak_end, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.arrowedLine(img, pt_streak_start, pt_streak_end, (30, 30, 220), 4, cv2.LINE_AA, tipLength=0.15)
        cv2.circle(img, pt_streak_end, 7, (40, 40, 230), -1)
        cv2.putText(img, "TRAJECTORY: IRON MAN AERIAL FLIGHT VECTOR", (pt_streak_start[0], pt_streak_start[1] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (40, 200, 255), 1)

    elif shot_id == "090":
        if tau < 13.0:
            cv2.putText(img, "DIALOGUE: 'You're not the only one cursed with knowledge' (HEAD NOD)",
                        (W_IMG // 2 - 280, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 230, 100), 1)
        else:
            cv2.putText(img, "DIALOGUE: STERN PUSH-IN / LINE FINISH",
                        (W_IMG // 2 - 180, H_IMG - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 230, 100), 1)

    elif shot_id == "110":
        # Row 1 (Shot 110): Twin open shoulder missile pods firing forward with orange flame/smoke
        p_lsho = proj(to_world("IronMan", (0.55, 3.8, 0.1)))
        p_rsho = proj(to_world("IronMan", (-0.55, 3.8, 0.1)))
        for p_sho, sign in [(p_lsho, 1), (p_rsho, -1)]:
            if p_sho:
                # Open shoulder pod box
                cv2.rectangle(img, (p_sho[0] - 22, p_sho[1] - 14), (p_sho[0] + 22, p_sho[1] + 14), (100, 110, 120), -1)
                cv2.rectangle(img, (p_sho[0] - 22, p_sho[1] - 14), (p_sho[0] + 22, p_sho[1] + 14), (200, 220, 240), 2)
                # Rocket tube bores
                for ox in [-12, 0, 12]:
                    cv2.circle(img, (p_sho[0] + ox, p_sho[1]), 5, (30, 30, 30), -1)
                    cv2.circle(img, (p_sho[0] + ox, p_sho[1]), 5, (80, 180, 255), 1)
                # Firing flames & smoke vector forward toward camera
                flame_end = (p_sho[0] + sign * 15, p_sho[1] + 45)
                cv2.line(img, p_sho, flame_end, (30, 140, 255), 6, cv2.LINE_AA)
                cv2.line(img, p_sho, flame_end, (100, 220, 255), 2, cv2.LINE_AA)
                cv2.circle(img, flame_end, 8, (40, 160, 255), -1)
        cv2.putText(img, "TWIN SHOULDER MISSILE PODS (IGNITION FLARES)", (int(W_IMG * 0.18), int(H_IMG * 0.90)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (50, 180, 255), 1)

    elif shot_id == "115":
        # Row 2 (Shot 115): Projectile trajectory vectors curving from Iron Man (bottom-center) up toward mid-left sky
        im_pt = proj(to_world("IronMan", (0, 1.5, 0))) or (int(W_IMG * 0.50), int(H_IMG * 0.78))
        # Bright launch glow around Iron Man
        cv2.circle(img, im_pt, 22, (40, 140, 255), -1)
        cv2.circle(img, im_pt, 36, (20, 180, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "LAUNCH SILHOUETTE GLOW", (im_pt[0] - 80, im_pt[1] + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (80, 190, 255), 1)
        # 8 curving missile trajectory vectors up toward mid-left sky
        for idx, (targ_x, targ_y, ctrl_x, ctrl_y) in enumerate([
            (int(W_IMG * 0.18), int(H_IMG * 0.20), int(W_IMG * 0.30), int(H_IMG * 0.40)),
            (int(W_IMG * 0.24), int(H_IMG * 0.15), int(W_IMG * 0.35), int(H_IMG * 0.36)),
            (int(W_IMG * 0.32), int(H_IMG * 0.12), int(W_IMG * 0.40), int(H_IMG * 0.32)),
            (int(W_IMG * 0.12), int(H_IMG * 0.28), int(W_IMG * 0.26), int(H_IMG * 0.48)),
            (int(W_IMG * 0.38), int(H_IMG * 0.18), int(W_IMG * 0.44), int(H_IMG * 0.38)),
            (int(W_IMG * 0.28), int(H_IMG * 0.25), int(W_IMG * 0.38), int(H_IMG * 0.45)),
            (int(W_IMG * 0.20), int(H_IMG * 0.32), int(W_IMG * 0.32), int(H_IMG * 0.52)),
            (int(W_IMG * 0.42), int(H_IMG * 0.14), int(W_IMG * 0.46), int(H_IMG * 0.34)),
        ]):
            # Draw quadratic bezier curve for smoke trail
            curve_pts = []
            for s_step in np.linspace(0, 1, 18):
                u = 1 - s_step
                px = int(u * u * im_pt[0] + 2 * u * s_step * ctrl_x + s_step * s_step * targ_x)
                py = int(u * u * im_pt[1] + 2 * u * s_step * ctrl_y + s_step * s_step * targ_y)
                curve_pts.append([px, py])
            pts_arr = np.array(curve_pts, np.int32).reshape((-1, 1, 2))
            cv2.polylines(img, [pts_arr], False, (220, 220, 220), 2, cv2.LINE_AA)
            # Orange detonation / rocket head
            cv2.circle(img, (targ_x, targ_y), 5, (40, 150, 255), -1)
            cv2.circle(img, (targ_x, targ_y), 2, (255, 255, 255), -1)
        cv2.putText(img, "MISSILE TRAJECTORY VECTORS (ARCS TO SKY)", (int(W_IMG * 0.12), int(H_IMG * 0.10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (230, 230, 230), 1)

    elif shot_id == "120":
        # Row 3 (Shot 120): Incoming smoking missiles from upper-right sky
        for mx, my in [((int(W_IMG * 0.90), int(H_IMG * 0.10)), (int(W_IMG * 0.62), int(H_IMG * 0.40))),
                       ((int(W_IMG * 0.95), int(H_IMG * 0.16)), (int(W_IMG * 0.70), int(H_IMG * 0.46))),
                       ((int(W_IMG * 0.84), int(H_IMG * 0.06)), (int(W_IMG * 0.54), int(H_IMG * 0.36)))]:
            cv2.line(img, mx, my, (220, 220, 220), 4, cv2.LINE_AA)
            cv2.line(img, mx, my, (50, 160, 255), 2, cv2.LINE_AA)
            cv2.circle(img, my, 6, (40, 160, 255), -1)
            cv2.circle(img, my, 3, (255, 255, 255), -1)
        cv2.putText(img, "INCOMING MISSILES BARRAGE (SMOKE + IGNITION)", (int(W_IMG * 0.52), int(H_IMG * 0.08)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)

    elif shot_id == "130":
        # Row 4 (Shot 130): Massive orange-yellow fireball & billowing smoke engulfing Thanos on left-center; Iron Man entry
        p_th = proj(to_world("Thanos", (0, 2.5, 0))) or (int(W_IMG * 0.38), int(H_IMG * 0.55))
        # Layered fireball bloom
        for r_fb, col_fb in [(75, (25, 25, 30)), (55, (30, 80, 160)), (40, (30, 140, 255)), (22, (150, 220, 255))]:
            cv2.circle(img, p_th, r_fb, col_fb, -1)
        cv2.circle(img, p_th, 80, (40, 180, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "MASSIVE FIREBALL & SMOKE ENGULFING THANOS", (p_th[0] - 120, p_th[1] + 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (60, 180, 255), 1)
        # Iron Man entry vector from upper right
        im_in_start = (int(W_IMG * 0.88), int(H_IMG * 0.16))
        im_in_end = (int(W_IMG * 0.65), int(H_IMG * 0.36))
        cv2.arrowedLine(img, im_in_start, im_in_end, (40, 40, 220), 4, cv2.LINE_AA, tipLength=0.18)
        cv2.line(img, im_in_start, im_in_end, (50, 180, 255), 2, cv2.LINE_AA)
        cv2.circle(img, im_in_end, 7, (40, 40, 230), -1)
        cv2.putText(img, "IRON MAN JET IN (UPPER-RIGHT)", (im_in_start[0] - 140, im_in_start[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (80, 200, 255), 1)

    elif shot_id == "140":
        # Row 5 (Shot 140): Blazing orange-yellow boot/hip thruster flares and trailing smoke particles
        p_lf = proj(to_world("IronMan", scene.local_point(W, P, "LeftFoot", scene.CENTER["LeftFoot"])))
        p_rf = proj(to_world("IronMan", scene.local_point(W, P, "RightFoot", scene.CENTER["RightFoot"])))
        for p_foot in [p_lf, p_rf]:
            if p_foot:
                flare_back = (p_foot[0], p_foot[1] + 45)
                cv2.line(img, p_foot, flare_back, (30, 120, 255), 6, cv2.LINE_AA)
                cv2.line(img, p_foot, flare_back, (200, 240, 255), 2, cv2.LINE_AA)
                cv2.circle(img, flare_back, 8, (40, 160, 255), -1)
        cv2.putText(img, "BLAZING BOOT THRUSTER FLARES & SMOKE", (int(W_IMG * 0.24), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (40, 180, 255), 1)

    elif shot_id == "150":
        # Row 6 (Shot 150): Upward sky pitch, Iron Man tucked somersault flip in upper-right with cyan back thrusters
        p_ut = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"])))
        if p_ut:
            # Cyan back thrusters
            cv2.circle(img, (p_ut[0] - 18, p_ut[1]), 8, (255, 220, 50), -1)
            cv2.circle(img, (p_ut[0] + 18, p_ut[1]), 8, (255, 220, 50), -1)
            cv2.line(img, (p_ut[0] - 18, p_ut[1]), (p_ut[0] - 25, p_ut[1] + 25), (255, 200, 50), 3, cv2.LINE_AA)
            cv2.line(img, (p_ut[0] + 18, p_ut[1]), (p_ut[0] + 25, p_ut[1] + 25), (255, 200, 50), 3, cv2.LINE_AA)
        cv2.putText(img, "TUCKED MID-AIR SOMERSAULT + CYAN BACK THRUSTERS", (int(W_IMG * 0.32), int(H_IMG * 0.12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 220, 50), 1)

    elif shot_id == "160":
        # Row 7 (Shot 160): Ground impact, boots clamped to ground, heavy landing slide, kicked-up dust
        p_lf = proj(to_world("IronMan", scene.local_point(W, P, "LeftFoot", scene.CENTER["LeftFoot"])))
        p_rf = proj(to_world("IronMan", scene.local_point(W, P, "RightFoot", scene.CENTER["RightFoot"])))
        for p_foot in [p_lf, p_rf]:
            if p_foot:
                # Ground dust kick-up cloud
                for dx in range(-25, 30, 12):
                    cv2.circle(img, (p_foot[0] + dx, p_foot[1] - 4), 10, (70, 90, 110), -1)
                cv2.line(img, (p_foot[0] - 40, p_foot[1] + 2), (p_foot[0] + 40, p_foot[1] + 2), (180, 180, 180), 2)
        cv2.putText(img, "GROUND IMPACT: BOOTS CLAMPED IN DUST SLIDE", (int(W_IMG * 0.18), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (120, 180, 220), 1)

    elif shot_id == "170":
        # Row 8 (Shot 170): Coiled strike stance, oversized silver battering-ram hammers with glowing cyan vents
        p_lh = proj(to_world("IronMan", scene.local_point(W, P, "LeftHand", scene.CENTER["LeftHand"])))
        p_rh = proj(to_world("IronMan", scene.local_point(W, P, "RightHand", scene.CENTER["RightHand"])))
        for p_hand in [p_lh, p_rh]:
            if p_hand:
                cv2.rectangle(img, (p_hand[0] - 25, p_hand[1] - 30), (p_hand[0] + 25, p_hand[1] + 30), (180, 185, 195), -1)
                cv2.rectangle(img, (p_hand[0] - 25, p_hand[1] - 30), (p_hand[0] + 25, p_hand[1] + 30), (255, 230, 80), 2)
                # Cyan vent stripes
                cv2.line(img, (p_hand[0] - 18, p_hand[1]), (p_hand[0] + 18, p_hand[1]), (255, 220, 50), 3)
        cv2.putText(img, "NANOTECH BATTERING-RAM HAMMERS (CYAN VENTS)", (int(W_IMG * 0.32), int(H_IMG * 0.88)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 220, 60), 1)

    elif shot_id == "180":
        # Row 9 (Shot 180): Radial blue-white impact bloom & horizontal blue thruster jet beams streaming from back
        p_hit = proj(to_world("Thanos", (0, 3.5, -1.0))) or (int(W_IMG * 0.42), int(H_IMG * 0.48))
        # Blue-white radial impact bloom
        for r_bloom, col_bloom in [(55, (255, 180, 80)), (35, (255, 220, 150)), (18, (255, 255, 255))]:
            cv2.circle(img, p_hit, r_bloom, col_bloom, -1)
        for ang in range(0, 360, 45):
            rad = np.radians(ang)
            sp_end = (int(p_hit[0] + 70 * np.cos(rad)), int(p_hit[1] + 70 * np.sin(rad)))
            cv2.line(img, p_hit, sp_end, (255, 220, 120), 2, cv2.LINE_AA)
        cv2.putText(img, "RADIAL BLUE-WHITE IMPACT BLOOM & THRUSTER BEAMS", (int(W_IMG * 0.16), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 220, 100), 1)

    elif shot_id == "185":
        # Row 10 (Shot 185): Minimum horizontal separation (4 studs on X) & clash sparks
        p_im = proj(to_world("IronMan", (0, 2.5, 0)))
        p_th = proj(to_world("Thanos", (0, 2.5, 0)))
        if p_im and p_th:
            mid = ((p_im[0] + p_th[0]) // 2, (p_im[1] + p_th[1]) // 2)
            for r_sp, col_sp in [(20, (30, 140, 255)), (10, (150, 220, 255))]:
                cv2.circle(img, mid, r_sp, col_sp, -1)
            for sp_i in range(6):
                ang = sp_i * 60
                sx = int(mid[0] + 28 * np.cos(np.radians(ang)))
                sy = int(mid[1] + 28 * np.sin(np.radians(ang)))
                cv2.line(img, mid, (sx, sy), (200, 240, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "4-STUD HORIZONTAL SEPARATION & THRUSTER CLASH SPARKS", (int(W_IMG * 0.16), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (60, 180, 255), 1)

    elif shot_id == "190":
        # Row 1 (Shot 190): OTS Thanos on left-center gripping Tony's helmet in lower-right
        p_th_rh = proj(to_world("Thanos", scene.local_point(W, P, "RightHand", scene.CENTER["RightHand"])))
        p_im_head = proj(to_world("IronMan", scene.local_point(W, P, "Head", scene.CENTER["Head"])))
        if p_th_rh and p_im_head:
            cv2.line(img, p_th_rh, p_im_head, (255, 200, 100), 2, cv2.LINE_AA)
            cv2.circle(img, p_im_head, 15, (40, 40, 220), 2)
        cv2.putText(img, "OTS: THANOS (LEFT-CENTER) GRIPPING TONY'S HELMET (LOWER-RIGHT)", (int(W_IMG * 0.12), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (200, 140, 255), 1)

    elif shot_id == "200":
        # Row 2 (Shot 200): Unmasked Tony Stark with dark hair, shocked expression
        p_head = proj(to_world("IronMan", scene.local_point(W, P, "Head", scene.CENTER["Head"]))) or (int(W_IMG * 0.5), int(H_IMG * 0.45))
        # Hair bounding ellipse
        cv2.ellipse(img, (p_head[0], p_head[1] - 45), (65, 35), 0, 180, 360, (30, 25, 22), -1)
        cv2.ellipse(img, (p_head[0], p_head[1] - 45), (65, 35), 0, 180, 360, (200, 180, 150), 2, cv2.LINE_AA)
        # Shocked expression eyes & mouth
        cv2.circle(img, (p_head[0] - 22, p_head[1] - 10), 8, (255, 255, 255), -1)
        cv2.circle(img, (p_head[0] + 22, p_head[1] - 10), 8, (255, 255, 255), -1)
        cv2.circle(img, (p_head[0] - 20, p_head[1] - 10), 4, (20, 20, 20), -1)
        cv2.circle(img, (p_head[0] + 24, p_head[1] - 10), 4, (20, 20, 20), -1)
        cv2.ellipse(img, (p_head[0], p_head[1] + 22), (14, 18), 0, 0, 360, (30, 20, 20), -1)
        cv2.putText(img, "UNMASKED TONY STARK: SHOCKED EXPRESSION & EXPOSED HAIR", (int(W_IMG * 0.14), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80, 160, 255), 1)

    elif shot_id == "210":
        # Row 3 (Shot 210): Side-profile headbutt, impact spark between heads
        p_th_head = proj(to_world("Thanos", scene.local_point(W, P, "Head", scene.CENTER["Head"])))
        p_im_head = proj(to_world("IronMan", scene.local_point(W, P, "Head", scene.CENTER["Head"])))
        if p_th_head and p_im_head:
            spark_pos = ((p_th_head[0] + p_im_head[0]) // 2, (p_th_head[1] + p_im_head[1]) // 2)
            for r_sp, col_sp in [(24, (120, 210, 255)), (12, (255, 255, 255))]:
                cv2.circle(img, spark_pos, r_sp, col_sp, -1)
            for sp_i in range(8):
                ang = sp_i * 45
                sx = int(spark_pos[0] + 32 * np.cos(np.radians(ang)))
                sy = int(spark_pos[1] + 32 * np.sin(np.radians(ang)))
                cv2.line(img, spark_pos, (sx, sy), (180, 230, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "SIDE-PROFILE HEADBUTT: THANOS LUNGE & HELMET RECOIL SPARK", (int(W_IMG * 0.12), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (100, 200, 255), 1)

    elif shot_id == "213":
        # Row 4 (Shot 213): Counter-swing windup, chest arc reactor visible
        p_torso = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"])))
        if p_torso:
            # Glowing cyan arc reactor
            cv2.circle(img, (p_torso[0], p_torso[1] + 25), 18, (255, 220, 50), -1)
            cv2.circle(img, (p_torso[0], p_torso[1] + 25), 26, (255, 200, 100), 2, cv2.LINE_AA)
        cv2.putText(img, "COUNTER-SWING WINDUP & CHEST ARC REACTOR", (int(W_IMG * 0.22), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 220, 80), 1)

    elif shot_id == "216":
        # Row 5 (Shot 216): Ground skid, Iron Man flat on dirt, billowing dust plumes
        p_im = proj(to_world("IronMan", scene.local_point(W, P, "LowerTorso", scene.CENTER["LowerTorso"])))
        if p_im:
            for dust_dx in range(-120, 140, 45):
                cv2.ellipse(img, (p_im[0] + dust_dx, p_im[1] + 35), (42, 22), 0, 0, 360, (110, 100, 90), -1)
                cv2.ellipse(img, (p_im[0] + dust_dx, p_im[1] + 35), (42, 22), 0, 0, 360, (160, 150, 140), 1, cv2.LINE_AA)
        cv2.putText(img, "GROUND SKID: IRON MAN HORIZONTAL IN BILLOWING DUST", (int(W_IMG * 0.15), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (140, 180, 220), 1)

    elif shot_id == "220":
        # Row 6 (Shot 220): Medium close Thanos (70% frame height), nanotech discard arc
        p_th = proj(to_world("Thanos", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"])))
        if p_th:
            # Trajectory of flung nanotech piece
            cv2.ellipse(img, (p_th[0] + 120, p_th[1] + 40), (70, 45), -25, 0, 180, (80, 160, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "MEDIUM CLOSE: THANOS (70% HEIGHT) FLINGING NANOTECH PIECE", (int(W_IMG * 0.12), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (120, 200, 255), 1)

    elif shot_id == "230":
        # Row 7 (Shot 230): Low ground crouch, glaring at Thanos, scuffed faceplate
        p_head = proj(to_world("IronMan", scene.local_point(W, P, "Head", scene.CENTER["Head"])))
        p_torso = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"])))
        if p_head:
            # Subtle faceplate battle scuff lines
            cv2.line(img, (p_head[0] - 15, p_head[1] - 8), (p_head[0] + 5, p_head[1] + 12), (30, 30, 30), 2, cv2.LINE_AA)
            cv2.line(img, (p_head[0] - 8, p_head[1] + 6), (p_head[0] + 18, p_head[1] + 20), (30, 30, 30), 2, cv2.LINE_AA)
        if p_torso:
            cv2.circle(img, (p_torso[0], p_torso[1] + 18), 14, (255, 220, 50), -1)
        cv2.putText(img, "GROUND CROUCH: GLARE AT THANOS & SCUFFED FACEPLATE", (int(W_IMG * 0.15), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 180, 100), 1)

    elif shot_id == "240":
        # Row 1 (Shot 240): Thanos on left-third charging Power Stone, Iron Man in lower-right defensive crouch
        p_th_lh = proj(to_world("Thanos", scene.local_point(W, P, "LeftHand", scene.CENTER["LeftHand"])))
        if p_th_lh:
            # Power Stone charge violet glow
            for r_ch, col_ch in [(28, (230, 80, 220)), (14, (255, 180, 255))]:
                cv2.circle(img, p_th_lh, r_ch, col_ch, -1)
            for i in range(8):
                ang = i * 45
                sx = int(p_th_lh[0] + 35 * np.cos(np.radians(ang)))
                sy = int(p_th_lh[1] + 35 * np.sin(np.radians(ang)))
                cv2.line(img, p_th_lh, (sx, sy), (255, 200, 255), 2, cv2.LINE_AA)
        p_im = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"])))
        if p_im:
            cv2.ellipse(img, (p_im[0], p_im[1] + 30), (55, 22), 0, 0, 360, (60, 50, 42), -1)
        cv2.putText(img, "THANOS (LEFT-THIRD) CHARGING POWER STONE vs IRON MAN (LOWER-RIGHT)", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 140, 255), 1)

    elif shot_id == "250":
        # Row 2 (Shot 250): Iron Man deep braced lunge, nanotech tower shield deployed
        p_lh = proj(to_world("IronMan", scene.local_point(W, P, "LeftHand", scene.CENTER["LeftHand"])))
        if p_lh:
            # Curved sloped tower shield polygon
            pts_shield = np.array([
                [p_lh[0] - 25, p_lh[1] - 85], [p_lh[0] + 25, p_lh[1] - 80],
                [p_lh[0] + 35, p_lh[1] + 20], [p_lh[0] + 20, p_lh[1] + 90],
                [p_lh[0] - 20, p_lh[1] + 90], [p_lh[0] - 35, p_lh[1] + 15]
            ], np.int32)
            cv2.fillPoly(img, [pts_shield], (40, 20, 95))
            cv2.polylines(img, [pts_shield], True, (75, 175, 215), 3, cv2.LINE_AA)
        cv2.putText(img, "IRON MAN DEEP BRACED LUNGE: NANOTECH TOWER SHIELD DEPLOYED", (int(W_IMG * 0.12), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80, 180, 255), 1)

    elif shot_id == "255":
        # Row 3 (Shot 255): Beam slams into shield right-of-center detonating massive radial plasma burst
        p_hit = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"]))) or (int(W_IMG * 0.60), int(H_IMG * 0.52))
        # Incoming thick purple beam from left border
        cv2.line(img, (0, p_hit[1]), p_hit, (200, 40, 180), 16, cv2.LINE_AA)
        cv2.line(img, (0, p_hit[1]), p_hit, (255, 200, 255), 6, cv2.LINE_AA)
        # Radial plasma explosion
        for r_exp, col_exp in [(95, (160, 40, 160)), (65, (220, 80, 220)), (35, (255, 220, 255))]:
            cv2.circle(img, p_hit, r_exp, col_exp, -1)
        for ang in range(0, 360, 30):
            rad = np.radians(ang)
            ex = int(p_hit[0] + 120 * np.cos(rad))
            ey = int(p_hit[1] + 120 * np.sin(rad))
            cv2.line(img, p_hit, (ex, ey), (255, 210, 255), 3, cv2.LINE_AA)
        cv2.putText(img, "POWER STONE BEAM DETONATION: RADIAL PLASMA EXPLOSION ON SHIELD", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (240, 160, 255), 1)

    elif shot_id == "260":
        # Row 4 (Shot 260): Energy torrent, deflected upper and lower plasma cones, sliding backward
        p_im = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"]))) or (int(W_IMG * 0.58), int(H_IMG * 0.45))
        # Continuous thick purple beam
        cv2.line(img, (0, p_im[1]), p_im, (220, 40, 200), 20, cv2.LINE_AA)
        cv2.line(img, (0, p_im[1]), p_im, (255, 230, 255), 8, cv2.LINE_AA)
        # Upper deflected plasma cone
        pts_top = np.array([p_im, [p_im[0] + 180, p_im[1] - 140], [p_im[0] + 100, p_im[1] - 160]], np.int32)
        cv2.fillPoly(img, [pts_top], (180, 50, 180))
        # Lower deflected plasma cone
        pts_bot = np.array([p_im, [p_im[0] + 160, p_im[1] + 120], [p_im[0] + 80, p_im[1] + 140]], np.int32)
        cv2.fillPoly(img, [pts_bot], (180, 50, 180))
        cv2.putText(img, "ENERGY TORRENT: DEFLECTED PLASMA CONES & BACKWARD SLIDE", (int(W_IMG * 0.12), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (220, 120, 255), 1)

    elif shot_id == "262":
        # Row 5 (Shot 262): Tight OTS behind Iron Man right shoulder, plasma storm washing over frame
        # Shield on left third
        cv2.rectangle(img, (0, 0), (int(W_IMG * 0.35), H_IMG), (60, 25, 90), -1)
        # Violent plasma waves washing over borders
        for x_wave in range(0, W_IMG, 60):
            cv2.ellipse(img, (x_wave, 30), (50, 40), 0, 0, 360, (200, 60, 200), -1)
            cv2.ellipse(img, (x_wave, H_IMG - 30), (50, 40), 0, 0, 360, (200, 60, 200), -1)
        cv2.putText(img, "TIGHT OTS: BLINDING PURPLE PLASMA STORM ACROSS SHIELD", (int(W_IMG * 0.14), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (240, 180, 255), 1)

    elif shot_id == "265":
        # Row 6 (Shot 265): Iron Man (RED) sprinting right-to-left under horizontal beam, thrusters firing
        p_im = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"]))) or (int(W_IMG * 0.55), int(H_IMG * 0.55))
        # Horizontal purple beam streaking across top-left
        cv2.line(img, (0, int(H_IMG * 0.32)), (int(W_IMG * 0.65), int(H_IMG * 0.32)), (220, 50, 200), 12, cv2.LINE_AA)
        cv2.line(img, (0, int(H_IMG * 0.32)), (int(W_IMG * 0.65), int(H_IMG * 0.32)), (255, 230, 255), 4, cv2.LINE_AA)
        # Golden-orange thruster jet flare on back
        for r_th, col_th in [(28, (30, 140, 255)), (14, (120, 220, 255))]:
            cv2.circle(img, (p_im[0] + 45, p_im[1] - 15), r_th, col_th, -1)
        cv2.putText(img, "BEAM DUCK & JET CHARGE: IRON MAN (RED) SPRINTING UNDER BEAM", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80, 200, 255), 1)

    elif shot_id == "270":
        # Row 7 (Shot 270): Medium-wide airborne thruster lunge/barrel-roll (~35 deg) against sky
        p_im = proj(to_world("IronMan", scene.local_point(W, P, "UpperTorso", scene.CENTER["UpperTorso"]))) or (int(W_IMG * 0.50), int(H_IMG * 0.50))
        # Conical orange-white thruster flame
        pts_flame = np.array([
            [p_im[0] + 25, p_im[1] + 15],
            [p_im[0] + 95, p_im[1] + 45],
            [p_im[0] + 80, p_im[1] + 65],
            [p_im[0] + 20, p_im[1] + 30]
        ], np.int32)
        cv2.fillPoly(img, [pts_flame], (30, 150, 255))
        cv2.polylines(img, [pts_flame], True, (150, 225, 255), 2, cv2.LINE_AA)
        cv2.putText(img, "AIRBORNE THRUSTER LUNGE: 35-DEG DIAGONAL BARREL ROLL", (int(W_IMG * 0.14), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80, 210, 255), 1)

    elif shot_id == "275":
        # Row 1 (Shot 275): ECU Boot Thruster Insert skimming dirt diagonally across frame
        # Draw high-speed directional streak and boot nozzle flame
        pt_streak_s = (int(W_IMG * 0.15), int(H_IMG * 0.25))
        pt_streak_e = (int(W_IMG * 0.55), int(H_IMG * 0.65))
        for off_y in [-15, 0, 15]:
            cv2.line(img, (pt_streak_s[0], pt_streak_s[1] + off_y), (pt_streak_e[0], pt_streak_e[1] + off_y), (40, 140, 255), 3, cv2.LINE_AA)
            cv2.line(img, (pt_streak_s[0], pt_streak_s[1] + off_y), (pt_streak_e[0], pt_streak_e[1] + off_y), (200, 230, 255), 1, cv2.LINE_AA)
        cv2.circle(img, pt_streak_e, 14, (30, 160, 255), -1)
        cv2.circle(img, pt_streak_e, 7, (255, 255, 255), -1)
        cv2.putText(img, "ECU INSERT: LOWER LEG & BOOT THRUSTER DIAGONAL PROPULSION", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80, 200, 255), 1)

    elif shot_id == "280":
        # Row 2 (Shot 280): Melee Side-Profile Two-Shot: Thanos Punch (Left) vs Iron Man Guard (Right)
        p_th = proj(to_world("Thanos", (0, 3.2, 0))) or (int(W_IMG * 0.28), int(H_IMG * 0.52))
        p_im = proj(to_world("IronMan", (0, 3.2, 0))) or (int(W_IMG * 0.72), int(H_IMG * 0.48))
        # Thanos punch vector extending horizontally toward Iron Man
        p_punch_mid = (int((p_th[0] + p_im[0]) * 0.5), int((p_th[1] + p_im[1]) * 0.5))
        cv2.arrowedLine(img, p_th, p_punch_mid, (180, 60, 160), 5, cv2.LINE_AA, tipLength=0.2)
        # Impact spark flare
        for r_sp, col_sp in [(24, (40, 140, 255)), (12, (200, 240, 255))]:
            cv2.circle(img, p_punch_mid, r_sp, col_sp, -1)
        cv2.putText(img, "MELEE TWO-SHOT: THANOS PUNCH (LEFT) vs IRON MAN DEFENSIVE GUARD (RIGHT)", (int(W_IMG * 0.08), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (240, 180, 100), 1)

    elif shot_id == "290":
        # Row 3 (Shot 290): Ground Level Close-Up: Boot Slams Pinned Gauntlet, Claws Bite Soil
        p_soil = (int(W_IMG * 0.55), int(H_IMG * 0.65))
        # 45-degree diagonal leg vector pinning gauntlet
        cv2.line(img, (int(W_IMG * 0.25), int(H_IMG * 0.25)), p_soil, (40, 40, 220), 8, cv2.LINE_AA)
        # Ground anchor claws
        for dx_c, dy_c in [(-25, 12), (0, 18), (25, 12)]:
            cv2.line(img, p_soil, (p_soil[0] + dx_c, p_soil[1] + dy_c), (180, 180, 180), 4, cv2.LINE_AA)
        # Ground dust kick-up cloud
        for dx in range(-40, 45, 15):
            cv2.circle(img, (p_soil[0] + dx, p_soil[1] + 5), 14, (70, 90, 110), -1)
        cv2.putText(img, "GROUND LEVEL: BOOT SLAMS PINNED GAUNTLET, ANCHORS BITE INTO SOIL", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (140, 200, 240), 1)

    elif shot_id == "295":
        # Row 4 (Shot 295): Wide Full-Body Standoff: Action on Left 40%, Smoky Negative Space on Right
        # Negative space atmospheric indicator
        cv2.putText(img, "[TITAN BATTLEFIELD NEGATIVE SPACE]", (int(W_IMG * 0.52), int(H_IMG * 0.35)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (120, 120, 140), 1)
        cv2.putText(img, "WIDE STANDOFF: THANOS ON KNEE (LEFT), IRON MAN OVERHEAD WINDUP (RIGHT)", (int(W_IMG * 0.08), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (180, 220, 255), 1)

    elif shot_id == "300":
        # Row 5 (Shot 300): Tight Close-Up: Nanotech Battering Ram Formation with Cyan Energy Seams
        p_rh = proj(to_world("IronMan", scene.local_point(W, P, "RightHand", scene.CENTER["RightHand"]))) or (int(W_IMG * 0.50), int(H_IMG * 0.50))
        # Oversized stepped battering ram geometry
        cv2.rectangle(img, (p_rh[0] - 45, p_rh[1] - 40), (p_rh[0] + 45, p_rh[1] + 40), (120, 20, 26), -1)
        cv2.rectangle(img, (p_rh[0] - 45, p_rh[1] - 40), (p_rh[0] + 45, p_rh[1] + 40), (60, 180, 255), 3)
        # Pulsing cyan neon stripes
        for y_s in [-20, 0, 20]:
            cv2.line(img, (p_rh[0] - 35, p_rh[1] + y_s), (p_rh[0] + 35, p_rh[1] + y_s), (255, 230, 50), 3, cv2.LINE_AA)
        cv2.putText(img, "CLOSE-UP: NANOTECH BATTERING RAM WITH PULSING CYAN ENERGY SEAMS", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 220, 50), 1)

    elif shot_id == "310":
        # Row 6 (Shot 310): Whip-Slam: Battering Ram Smashes Downward into Thanos Face in Bottom-Right
        p_hit = (int(W_IMG * 0.65), int(H_IMG * 0.62))
        # Downward whip arc from upper-left
        pts_arc = np.array([
            [int(W_IMG * 0.20), int(H_IMG * 0.15)],
            [int(W_IMG * 0.40), int(H_IMG * 0.32)],
            [p_hit[0], p_hit[1]]
        ], np.int32)
        cv2.polylines(img, [pts_arc], False, (40, 180, 255), 4, cv2.LINE_AA)
        # Radial impact detonation
        for r_det, col_det in [(45, (255, 180, 60)), (25, (255, 230, 140)), (12, (255, 255, 255))]:
            cv2.circle(img, p_hit, r_det, col_det, -1)
        cv2.putText(img, "WHIP-SLAM: BATTERING RAM SMASHES INTO THANOS FACE (BOTTOM-RIGHT)", (int(W_IMG * 0.10), int(H_IMG * 0.92)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 210, 80), 1)

    cv2.putText(img, f"shot {sh['shot']}  t={tau:.2f}s  fov {fov:.0f}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return img


if __name__ == "__main__":
    ref, out = sys.argv[1], sys.argv[2]
    offset = float(next((a.split("=")[1] for a in sys.argv[3:] if a.startswith("--offset=")), 0))  # movie time of the clip's first frame
    times = [float(x) for x in sys.argv[3:] if not x.startswith("--")] or [0.1, 0.6, 1.0, 2.0, 2.4, 2.75, 3.05, 3.4, 3.9, 4.8, 5.8]
    cap = cv2.VideoCapture(ref); fps = cap.get(cv2.CAP_PROP_FPS)
    rows = []
    for tau in times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round((tau - offset) * fps)))
        ok, fr = cap.read()
        fr = cv2.resize(fr, (W_IMG, H_IMG)) if ok else np.zeros((H_IMG, W_IMG, 3), np.uint8)
        cv2.putText(fr, f"MOVIE t={tau:.2f}s", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        rows.append(np.hstack([fr, render(tau)]))
    os.makedirs(out, exist_ok=True)
    for s in range(0, len(rows), 4):
        cv2.imwrite(os.path.join(out, f"compare_{s // 4}.jpg"), np.vstack(rows[s:s + 4]))
    print("wrote", (len(rows) + 3) // 4, "sheets to", out)
