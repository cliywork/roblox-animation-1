"""
scene.py — the edit. Turns raw captures (captures/) into final per-shot animations (shots/) and
writes the timeline + camera plan for Roblox (SceneData.lua).

    python scene.py            # rebuild everything; Rojo syncs the results into Studio

Timeline times are MOVIE times (seconds) from the reference clip, frame-accurate (23.976 fps cuts).
Stage: Thanos stands at the origin facing -Z; Iron Man stands 40 studs away facing +Z (toward him).
"""
import os
import numpy as np
from scipy.spatial.transform import Rotation as R

from rbxmx_io import read_shot, resample, write_shot
from smpl_to_r15 import R15, face_forward

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURES, SHOTS = os.path.join(HERE, "captures"), os.path.join(HERE, "shots")
FPS = 30.0
HOLD_PAD = 0.3            # extra seconds of the last pose appended to every shot (absorbs timing jitter)

# ------------------------------------------------------------------------------------ stage
STAGE_Y = 1.95     # height of the Titan terrain surface along the fight line (titan_set.lua); feet stand on it
RIGS = {
    # camScale: the camera framing factor the shots were tuned with on the plain dummies
    "Thanos":  dict(pos=(0, STAGE_Y, 0),   yaw=0,   scale=1.35, camScale=0.776),   # faces -Z
    "IronMan": dict(pos=(0, STAGE_Y, -40), yaw=180, scale=1.0,  camScale=1.0),     # faces +Z, toward Thanos
}
REF_HEIGHT = 5.2   # height of the rig the cameras were planned on; real rigs are measured and offsets scale

# ------------------------------------------------------------------- approximate R15 geometry
# Rest-pose joint pivots (rig-local studs, ground at y=0, rig faces -Z, character's left is -X).
# Only used for ground locking and the preview render, so ~0.1 stud accuracy is enough.
PIVOT = {
    "LowerTorso": (0, 2.0, 0), "UpperTorso": (0, 2.4, 0), "Head": (0, 4.0, 0),
    "LeftUpperArm": (-1.5, 3.75, 0), "LeftLowerArm": (-1.5, 2.95, 0), "LeftHand": (-1.5, 2.15, 0),
    "RightUpperArm": (1.5, 3.75, 0), "RightLowerArm": (1.5, 2.95, 0), "RightHand": (1.5, 2.15, 0),
    "LeftUpperLeg": (-0.5, 2.0, 0), "LeftLowerLeg": (-0.5, 1.15, 0), "LeftFoot": (-0.5, 0.3, 0),
    "RightUpperLeg": (0.5, 2.0, 0), "RightLowerLeg": (0.5, 1.15, 0), "RightFoot": (0.5, 0.3, 0),
}
CENTER = {  # part centres (what BasePart.Position reports), used as camera targets
    "HumanoidRootPart": (0, 3.0, 0), "LowerTorso": (0, 2.2, 0), "UpperTorso": (0, 3.2, 0),
    "Head": (0, 4.55, 0),
    "LeftUpperArm": (-1.5, 3.35, 0), "LeftLowerArm": (-1.5, 2.55, 0), "LeftHand": (-1.5, 1.95, 0),
    "RightUpperArm": (1.5, 3.35, 0), "RightLowerArm": (1.5, 2.55, 0), "RightHand": (1.5, 1.95, 0),
    "LeftUpperLeg": (-0.5, 1.575, 0), "LeftLowerLeg": (-0.5, 0.725, 0), "LeftFoot": (-0.5, 0.15, -0.1),
    "RightUpperLeg": (0.5, 1.575, 0), "RightLowerLeg": (0.5, 0.725, 0), "RightFoot": (0.5, 0.15, -0.1),
}
SOLE = {"LeftFoot": [(-0.5, 0, 0.3), (-0.5, 0, -0.5)], "RightFoot": [(0.5, 0, 0.3), (0.5, 0, -0.5)]}
PIVOT = {k: np.array(v, float) for k, v in PIVOT.items()}


def fk(T, i):
    """World rotation + joint pivot of every part at frame i (rig-local)."""
    W, P = {"HumanoidRootPart": np.eye(3)}, {}
    for part, (parent, _) in R15.items():
        W[part] = W[parent] @ T[part][i, :3, :3]
        if parent == "HumanoidRootPart":
            P[part] = PIVOT[part] + T[part][i, :3, 3]
        else:
            P[part] = P[parent] + W[parent] @ (PIVOT[part] - PIVOT[parent])
    return W, P


def local_point(W, P, part, rest_point):
    return P[part] + W[part] @ (np.asarray(rest_point, float) - PIVOT[part])


def sole_height(T, i):
    W, P = fk(T, i)
    return min(local_point(W, P, f, p)[1] for f, pts in SOLE.items() for p in pts)


# ------------------------------------------------------------------------------- shot edits
def n_frames(dur):
    return int(round(dur * FPS)) + 1


def frame_times(dur):
    return np.arange(n_frames(dur)) / FPS


def from_capture(name, dur, src_in=0.0, hold_after=None, ground="lock", lock_xz=False):
    """Cut [src_in, ...) out of a capture at real-time speed for `dur` seconds.
    hold_after: capture time after which the pose is frozen (cuts off tracking glitches).
    ground: "lock" keeps the lowest foot on the floor every frame, "min" shifts the whole
            shot once, None leaves GVHMR's height. lock_xz removes horizontal root drift."""
    t, T = read_shot(os.path.join(CAPTURES, name))
    end = min(t[-1], hold_after if hold_after is not None else t[-1])
    S = resample(t, T, np.minimum(src_in + frame_times(dur), end))
    S["LowerTorso"][:, [0, 2], 3] -= S["LowerTorso"][0, [0, 2], 3]   # start at the rig's spot
    S = face_forward(S)
    if lock_xz:
        S["LowerTorso"][:, [0, 2], 3] = 0
    return ground_fix(S, ground)


def ground_fix(S, mode):
    if mode is None:
        return S
    n = len(S["LowerTorso"])
    y = np.array([sole_height(S, i) for i in range(n)])
    if mode == "lock":
        k = np.ones(5) / 5                                   # light smoothing of the correction
        off = -np.convolve(np.pad(y, 2, mode="edge"), k, mode="valid")
    else:
        off = np.full(n, -y.min())
    S["LowerTorso"][:, 1, 3] += off
    return S


def pose_of(S, i):
    return {p: m[i].copy() for p, m in S.items()}


def blend(a, b, w):
    """Per-part slerp between two poses (w=0 -> a, w=1 -> b)."""
    out = {}
    for p in a:
        rots = R.from_matrix(np.stack([a[p][:3, :3], b[p][:3, :3]]))
        rel = (rots[0].inv() * rots[1]).as_rotvec()
        m = np.eye(4)
        m[:3, :3] = (rots[0] * R.from_rotvec(rel * w)).as_matrix()
        m[:3, 3] = (1 - w) * a[p][:3, 3] + w * b[p][:3, 3]
        out[p] = m
    return out


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def stack(poses):
    return {p: np.stack([q[p] for q in poses]) for p in poses[0]}


def aim(pose, part, direction, roll=0.0):
    """Point a limb part (rest direction -Y) along `direction` (rig-local), keeping its parent.
    roll spins it about its own length (degrees)."""
    q = {p: m.copy() for p, m in pose.items()}
    d = np.asarray(direction, float); d /= np.linalg.norm(d)
    world_rot, _ = R.align_vectors([d], [[0, -1, 0]])
    world_rot = world_rot * R.from_euler("y", roll, degrees=True)
    W, _ = fk(stack([q]), 0)
    q[part][:3, :3] = W[R15[part][0]].T @ world_rot.as_matrix()
    return q


def twist(pose, part, deg):
    """Rotate one part about its own long (Y) axis."""
    q = {p: m.copy() for p, m in pose.items()}
    q[part][:3, :3] = q[part][:3, :3] @ R.from_euler("y", deg, degrees=True).as_matrix()
    return q


# ------------------------------------------------------------------------- key-pose authoring
# Hand-keyed poses are written as DIRECTIONS in rig space (rig faces -Z, his left is -X, up +Y):
# which way each limb points, which way each palm faces, where the head looks. No guessing.
PALM_AXIS = {"LeftHand": np.array([1.0, 0, 0]), "RightHand": np.array([-1.0, 0, 0])}  # rest palm normal
RELAXED_R = dict(R_up=(0.14, -0.99, 0.05), R_lo=(0.10, -0.99, 0.05), R_palm=(-1, 0, 0.2))


def set_world(q, part, world):
    W, _ = fk(stack([q]), 0)
    q[part][:3, :3] = W[R15[part][0]].T @ world


def orient(q, part, direction, palm=None):
    """Limb points along `direction`; for a hand, its palm faces `palm`."""
    y = -np.asarray(direction, float); y /= np.linalg.norm(y)        # part's local +Y = up the limb
    if palm is None:
        world, _ = R.align_vectors([-y], [[0, -1, 0]])
        set_world(q, part, world.as_matrix())
        return
    side = PALM_AXIS[part]                                            # local axis the palm faces
    p = np.asarray(palm, float); p = p - (p @ y) * y; p /= np.linalg.norm(p)
    x = p * side[0]                                                   # local +X in world
    z = np.cross(x, y)
    set_world(q, part, np.stack([x, y, z], 1))


def set_head(q, pitch=0.0, yaw=0.0, roll=0.0):
    """Head look in rig space (deg): pitch up, yaw to his left, roll = ear toward his right shoulder."""
    set_world(q, "Head", R.from_euler("YXZ", [yaw, pitch, -roll], degrees=True).as_matrix())
    return q


def with_head(pose, pitch=0.0, yaw=0.0, roll=0.0):
    """Copy of an existing pose (e.g. a capture frame) with a new head look."""
    return set_head({p: m.copy() for p, m in pose.items()}, pitch, yaw, roll)


def make_pose(torso=(0, 0), head=(0, 0), L_up=(-0.12, -0.99, 0), L_lo=None, L_hand=None, L_palm=(1, 0, 0),
              R_up=(0.12, -0.99, 0), R_lo=None, R_hand=None, R_palm=(-1, 0, 0), stance=0.06, roll=0):
    """torso=(yaw, forward lean) deg; roll = side tilt of the torso (deg); head=(pitch up, yaw to his left) deg, world-relative."""
    q = {p: np.eye(4) for p in R15}
    set_world(q, "UpperTorso", R.from_euler("YXZ", [torso[0], -torso[1], roll], degrees=True).as_matrix())
    set_head(q, *head)
    for side, up, lo, hand, palm in (("Left", L_up, L_lo, L_hand, L_palm), ("Right", R_up, R_lo, R_hand, R_palm)):
        lo = lo if lo is not None else up
        orient(q, f"{side}UpperArm", up)
        orient(q, f"{side}LowerArm", lo)
        orient(q, f"{side}Hand", hand if hand is not None else lo, palm)
    orient(q, "LeftUpperLeg", (-stance, -1, 0)); orient(q, "RightUpperLeg", (stance, -1, 0))
    for leg in ("LeftLowerLeg", "RightLowerLeg"):
        orient(q, leg, (0, -1, 0))
    for foot in ("LeftFoot", "RightFoot"):
        set_world(q, foot, np.eye(3))
    return q


def keyed(keys, dur, smooth=7):
    """keys: [(t, pose)] -> frames. Eased slerp between keys, then a short moving average so the
    motion flows through keys instead of stopping at each one."""
    t = frame_times(dur)
    frames = []
    for ti in t:
        i = max(j for j, (tk, _) in enumerate(keys) if tk <= ti + 1e-9)
        if i == len(keys) - 1:
            frames.append(keys[-1][1]); continue
        (t0, a), (t1, b) = keys[i], keys[i + 1]
        frames.append(blend(a, b, ease((ti - t0) / (t1 - t0))))
    S = stack(frames)
    if smooth > 1:
        h = smooth // 2
        for p, m in S.items():
            q = R.from_matrix(m[:, :3, :3]).as_quat()
            for k in range(1, len(q)):                     # keep quaternions on one hemisphere
                if q[k] @ q[k - 1] < 0:
                    q[k] = -q[k]
            qp = np.pad(q, ((h, h), (0, 0)), mode="edge")
            avg = np.stack([qp[k:k + len(q)] for k in range(smooth)]).mean(0)
            m[:, :3, :3] = R.from_quat(avg / np.linalg.norm(avg, axis=1, keepdims=True)).as_matrix()
            pos = np.pad(m[:, :3, 3], ((h, h), (0, 0)), mode="edge")
            m[:, :3, 3] = np.stack([pos[k:k + len(q)] for k in range(smooth)]).mean(0)
    return S


# ------------------------------------------------------------------ hit reactions (physics layer)
# A fast hit kicks the struck part, and the kick travels up the body: every joint from the hit part
# to the chest (plus the head, which whips the other way) gets a damped-spring rotation about the
# torque axis (lever x hit direction). Joints further up react later, smaller and slower, so the
# impact reads as weight and speed instead of a keyed pose change. Added on top of the animation.
CHAIN_UP = {"LeftHand": "LeftLowerArm", "LeftLowerArm": "LeftUpperArm", "LeftUpperArm": "UpperTorso",
            "RightHand": "RightLowerArm", "RightLowerArm": "RightUpperArm", "RightUpperArm": "UpperTorso",
            "LeftFoot": "LeftLowerLeg", "LeftLowerLeg": "LeftUpperLeg", "LeftUpperLeg": "LowerTorso",
            "RightFoot": "RightLowerLeg", "RightLowerLeg": "RightUpperLeg", "RightUpperLeg": "LowerTorso",
            "Head": "UpperTorso", "UpperTorso": "LowerTorso"}
# per link up the chain: (share of the kick, delay s, frequency Hz, damping ratio)
RESPONSE = [(1.0, 0.0, 4.5, 0.32), (0.6, 0.02, 4.0, 0.34), (0.35, 0.04, 3.2, 0.36),
            (0.18, 0.07, 2.4, 0.4), (0.1, 0.1, 2.0, 0.45)]


def spring(tau, freq, zeta):
    """Impulse response of a damped spring, peak = 1 (0 before the hit)."""
    if tau <= 0:
        return 0.0
    w = 2 * np.pi * freq
    wd = w * np.sqrt(1 - zeta ** 2)
    tp = np.arctan2(wd, zeta * w) / wd                      # time of the first peak
    peak = np.exp(-zeta * w * tp) * np.sin(wd * tp)
    return np.exp(-zeta * w * tau) * np.sin(wd * tau) / peak


def react(S, t_hit, part, direction, degrees, head_whip=0.5):
    """Add a hit at shot-local time t_hit (may be < 0: the hit happened in the previous shot) on
    `part`, pushing along `direction` (rig space), first peak `degrees` at the struck joint."""
    S = {p: m.copy() for p, m in S.items()}
    v = np.asarray(direction, float); v /= np.linalg.norm(v)
    t = np.arange(len(S["LowerTorso"])) / FPS
    i_hit = int(np.clip(round(t_hit * FPS), 0, len(t) - 1))
    W, P = fk(S, i_hit)
    hit_point = local_point(W, P, part, CENTER.get(part, PIVOT[part]))
    links, p = [], part
    while p in CHAIN_UP and len(links) < len(RESPONSE):
        links.append(p)
        p = CHAIN_UP[p] if p != "UpperTorso" else None
        if p is None:
            break
    for k, link in enumerate(links):
        share, delay, freq, zeta = RESPONSE[k]
        axis = np.cross(hit_point - P[link], v)
        if np.linalg.norm(axis) < 1e-6:
            continue
        axis /= np.linalg.norm(axis)
        for i in range(len(t)):
            a = degrees * share * spring(t[i] - t_hit - delay, freq, zeta)
            if a:
                Wf, _ = fk(S, i)
                parent = Wf[R15[link][0]]
                rot = R.from_rotvec(parent.T @ axis * np.radians(a)).as_matrix()   # about the joint, in parent space
                S[link][i, :3, :3] = rot @ S[link][i, :3, :3]
    if head_whip:                                           # the head lags the chest: small opposite nod
        Wh, Ph = fk(S, i_hit)
        axis = np.cross(np.array([0, 1.0, 0]), v)
        if np.linalg.norm(axis) > 1e-6:
            axis /= np.linalg.norm(axis)
            for i in range(len(t)):
                a = -degrees * 0.12 * head_whip * spring(t[i] - t_hit - 0.09, 2.2, 0.42)
                if a:
                    Wf, _ = fk(S, i)
                    rot = R.from_rotvec(Wf["UpperTorso"].T @ axis * np.radians(a)).as_matrix()
                    S["Head"][i, :3, :3] = rot @ S["Head"][i, :3, :3]
    return S


# Thanos key poses, read off the reference frames (movie time in comments).
TH_010 = [
    (0.00, make_pose(torso=(20, 2), head=(-4, -12), L_up=(-0.25, -0.9, -0.3), L_lo=(0.65, 0.25, -0.72), L_palm=(0.3, 0.2, 0.9), **RELAXED_R)),   # torso yawed 20°, gauntlet tucked across abdomen
    (0.25, make_pose(torso=(20, 2), head=(-4, -12), L_up=(-0.25, -0.9, -0.3), L_lo=(0.65, 0.25, -0.72), L_palm=(0.3, 0.2, 0.9), **RELAXED_R)),   # holds stance
    (0.45, make_pose(torso=(20, 2), head=(-4, -10), L_up=(-0.35, -0.7, -0.5), L_lo=(0.35, 0.8, -0.4), L_palm=(0.4, 0.1, 0.9), **RELAXED_R)),     # brings gauntlet up
    (0.68, make_pose(torso=(20, 2), head=(-4, -8), L_up=(-0.45, -0.35, -0.82), L_lo=(0.15, 0.95, -0.25), L_palm=(0.4, 0.1, 0.9), **RELAXED_R)),   # raises gauntlet beside head/shoulder to swat
    (0.75, make_pose(torso=(18, 1), head=(-5, -5), L_up=(-0.65, -0.4, -0.6), L_lo=(-0.45, 0.1, -0.85), L_palm=(0.5, 0.2, -0.8), **RELAXED_R)),   # swats projectile
    (0.834, make_pose(torso=(16, 1), head=(-6, -3), L_up=(-0.7, -0.3, -0.65), L_lo=(-0.6, 0.05, -0.8), L_palm=(0.5, 0.2, -0.8), **RELAXED_R)),
]
# arm out to his left-front sloping down a little from the shoulder; wrist bent back so the
# fingers point up and the palm (holding the nanotech piece) faces the camera
REACH = dict(L_up=(-0.72, -0.2, -0.66), L_lo=(-0.7, -0.08, -0.71), L_hand=(-0.45, 0.7, -0.55))
TH_020 = [
    (0.00, TH_010[-1][1]),
    (0.18, make_pose(torso=(10, 2), head=(-12, 38), L_palm=(0.62, 0.15, -0.77), **REACH, **RELAXED_R)),  # arm out, palm to camera
    (0.70, make_pose(torso=(10, 2), head=(-13, 40), L_palm=(0.45, 0.35, -0.82), **REACH, **RELAXED_R)),  # tilts the hand, studying it
    (1.418, make_pose(torso=(10, 2), head=(-12, 40), L_palm=(0.7, 0.1, -0.7), **REACH, **RELAXED_R)),
]
HOLD_030 = dict(torso=(8, 0), L_up=(-0.62, -0.62, -0.45), L_lo=(-0.35, 0.08, -0.93), L_hand=(-0.3, 0.15, -0.94), L_palm=(0, 1, 0), **RELAXED_R)
TH_030 = [
    (0.00, make_pose(head=(-2, -12), **HOLD_030)),    # hand out, palm up, holding the piece
    (0.06, make_pose(head=(7, -13), **HOLD_030)),     # 2.30: his chin starts to lift as he looks up at Tony
    (0.20, make_pose(head=(13, -15), **HOLD_030)),
    (0.376, make_pose(head=(20, -16), **HOLD_030)),   # chin up: looks into the sky
]
# Dialogue (070/090): close-ups, only head/shoulders visible. Arms relaxed, gauntlet hand low.
# Dialogue (070/090): close-ups, only head/shoulders visible. Torso/head angled ~18-24° right, chin down.
TALK = dict(L_up=(-0.15, -0.98, -0.05), L_lo=(-0.1, -0.9, -0.4), L_palm=(1, 0.3, 0),
            R_up=(0.18, -0.98, 0.05), R_lo=(0.12, -0.98, 0.05), R_palm=(-1, 0, 0))
TH_070 = [                                            # "Stark." — head/torso angled right, chin drop on word
    (0.00, make_pose(torso=(18, 2), head=(-6, 24, 0), **TALK)),
    (0.45, make_pose(torso=(18, 2.5), head=(-9, 25, 1), **TALK)),
    (1.335, make_pose(torso=(18, 2), head=(-6, 24, 0), **TALK)),
]
TH_090 = [                                            # long line: "You're not the only one cursed with knowledge"
    (0.00, make_pose(torso=(18, 2), head=(-6, 24, 0), **TALK)),
    (1.07, make_pose(torso=(18, 2.5), head=(-10, 25, 3), **TALK)),      # 11.50: head nod (-4° pitch down, +3° roll)
    (2.40, make_pose(torso=(18, 2.2), head=(-7, 24, -1), **TALK)),
    (3.60, make_pose(torso=(18, 2.0), head=(-5, 26, 1), **TALK)),
    (4.07, make_pose(torso=(19, 2.0), head=(-7, 27, 1), **TALK)),       # 14.50: stern finish (+3° additional rightward yaw)
    (5.422, make_pose(torso=(19, 2.0), head=(-6, 27, 0), **TALK)),
]
TH_040 = [                                            # background of 040: eyes follow Iron Man down
    (0.00, TH_030[-1][1]),
    (0.30, make_pose(head=(16, -10), **HOLD_030)),
    (0.62, make_pose(head=(-3, 0), **HOLD_030)),      # he has landed: Thanos looks straight at him
    (1.167, make_pose(head=(-3, 0), **HOLD_030)),
]
# 120 "Come on" (movie 20.85): gauntlet is raised to lower-right foreground, bare right arm tucked back behind right hip
COMEON = dict(L_up=(-0.2, -0.15, -0.95), L_lo=(0.5, -0.1, -0.85), L_palm=(0.6, -0.2, 0.7),
              R_up=(0.08, -0.99, 0.1), R_lo=(0.05, -0.99, 0.12), R_palm=(-1, 0, 0), stance=0.12)
TH_120 = [
    (0.00, make_pose(torso=(25, 3), head=(-2, 35), roll=-14, **COMEON)),     # torso angled 25° right, bare right arm behind hip
    (0.35, make_pose(torso=(25, 3.5), head=(-6, 35), roll=-14, **COMEON)),   # "Come on"
    (0.834, make_pose(torso=(25, 3), head=(-4, 35), roll=-14, **COMEON)),
]
# 130 the missiles come in: he raises the gauntlet forearm across his face and hunches behind it.
GUARD = dict(L_up=(-0.3, -0.25, -0.92), L_lo=(0.55, 0.75, -0.35), L_palm=(0.2, 0, 1),
             R_up=(0.45, -0.5, -0.75), R_lo=(0.1, -0.15, -1), R_palm=(-0.6, 0.6, 0), stance=0.15)
TH_130 = [
    (0.00, TH_120[-1][1]),
    (0.35, make_pose(torso=(10, 24), head=(-4, 14), **COMEON)),    # sees them coming: leans toward the blue arcs
    (0.75, make_pose(torso=(14, 34), head=(-12, 4), **GUARD)),     # guard up, forearm forward (movie c158): already leaning by 22.0 s
    (1.20, make_pose(torso=(18, 34), head=(-18, 2), **GUARD)),     # leaning INTO the incoming missiles, arm in front
    (3.086, make_pose(torso=(18, 34), head=(-18, 2), **GUARD)),
]


# ------------------------------------------------------- 140-185: kick, backflip, cannon charge
# Movie 24.531-29.411 is one continuous action, so it is written as functions of MOVIE time and
# each shot plays its slice: no pose jumps at the cuts. Directions are in body space (forward -Z,
# his left -X, up +Y); the whole body is then pitched/moved through LowerTorso.
def chan(t, keys):
    """Eased piecewise value of [(time, value)] at t."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0))
    return keys[-1][1]


def at_keys(t, keys):
    """Blend between key poses [(time, pose)] at t (eased slerp, like keyed())."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return blend(a, b, ease((t - t0) / (t1 - t0)))
    return keys[-1][1]


def limbs(base, arms=None, legs=None, palm=(1, 0, 0)):
    """Copy of base with mirrored arm / leg directions given for the LEFT side
    (arms = (upper, lower), legs = (thigh, shin)); the right side mirrors X."""
    q = {p: m.copy() for p, m in base.items()}
    for side, sx in (("Left", 1), ("Right", -1)):
        mir = lambda v: (v[0] * sx, v[1], v[2])
        if arms:
            orient(q, f"{side}UpperArm", mir(arms[0]))
            orient(q, f"{side}LowerArm", mir(arms[1]))
            orient(q, f"{side}Hand", mir(arms[1]), mir(palm))
        if legs:
            orient(q, f"{side}UpperLeg", mir(legs[0]))
            orient(q, f"{side}LowerLeg", mir(legs[1]))
    return q


def moved(pose, d=0.0, h=0.0, pitch=0.0, x=0.0, yaw=0.0):
    """Whole body: d studs forward (rig -Z), h up, x to his right (rig +X), pitched back by `pitch`
    deg about the hips, then turned by `yaw` deg (positive turns his front toward his left, -X)."""
    q = {p: m.copy() for p, m in pose.items()}
    q["LowerTorso"][:3, :3] = (R.from_euler("y", yaw, degrees=True).as_matrix()
                               @ R.from_euler("x", pitch, degrees=True).as_matrix() @ q["LowerTorso"][:3, :3])
    q["LowerTorso"][:3, 3] += (x, h, -d)
    return q


def arm(pose, side, up, lo, hand=None, palm=None):
    """Copy of pose with one arm re-aimed (side = "Left" / "Right"; directions in rig space)."""
    q = {p: m.copy() for p, m in pose.items()}
    orient(q, f"{side}UpperArm", up)
    orient(q, f"{side}LowerArm", lo)
    orient(q, f"{side}Hand", hand if hand is not None else lo, palm)
    return q


def world_point(rig, pose, part, rest_point=None):
    """World position of a part's centre (or a rest-space point) for a rig in a pose."""
    W, P = fk(stack([pose]), 0)
    c = rest_point if rest_point is not None else CENTER.get(part, tuple(PIVOT[part]))
    r = RIGS[rig]
    local = local_point(W, P, part, c)
    return np.array(r["pos"], float) + R.from_euler("y", r["yaw"], degrees=True).apply(r["scale"] * local)


def to_rig(rig, world):
    r = RIGS[rig]
    return R.from_euler("y", r["yaw"], degrees=True).inv().apply((np.asarray(world, float) - r["pos"]) / r["scale"])


ARM_UP, ARM_LO = 0.8, 1.0           # shoulder->elbow, elbow->fist centre (rig studs)


def reach(pose, rig, side, target_world, pole=(0, -1, 0), palm=None):
    """Two-bone IK: aim one arm so the fist centre lands on target_world (bent toward `pole`,
    rig space). Returns (new pose, shortfall in world studs: >0 means the target is out of reach)."""
    q = {p: m.copy() for p, m in pose.items()}
    W, P = fk(stack([q]), 0)
    s = P[f"{side}UpperArm"]
    t = to_rig(rig, target_world)
    v = t - s
    dist = np.linalg.norm(v)
    u = v / dist
    d = min(dist, ARM_UP + ARM_LO - 1e-3)
    cos_a = np.clip((ARM_UP ** 2 + d ** 2 - ARM_LO ** 2) / (2 * ARM_UP * d), -1, 1)   # shoulder angle
    pole = np.asarray(pole, float)
    bend = pole - (pole @ u) * u
    bend = bend / np.linalg.norm(bend) if np.linalg.norm(bend) > 1e-6 else np.array([0, -1.0, 0])
    elbow = s + ARM_UP * (cos_a * u + np.sqrt(1 - cos_a ** 2) * bend)
    fist = s + d * u
    orient(q, f"{side}UpperArm", elbow - s)
    orient(q, f"{side}LowerArm", fist - elbow)
    orient(q, f"{side}Hand", fist - elbow, palm)
    return q, (dist - d) * RIGS[rig]["scale"]


def kneel(pose):
    """Down on his right knee: left foot planted forward, right shin on the ground behind."""
    q = {p_: m.copy() for p_, m in pose.items()}
    orient(q, "LeftUpperLeg", (-0.12, -0.2, -0.97))                   # front thigh near level
    orient(q, "LeftLowerLeg", (-0.05, -0.9, -0.43))                   # front shin angled forward, foot flat
    orient(q, "RightUpperLeg", (0.12, -1, 0.05))
    orient(q, "RightLowerLeg", (0.05, -0.08, 1))
    return q


def low_crouch(pose):
    """Both knees bent, thighs forward, feet under him: the low hold of shot 220 (movie 34.0 s, Thanos ~70% height)."""
    return limbs(pose, legs=((-0.15, -0.85, -0.5), (-0.1, -0.95, 0.3)))


def slice_of(fn, start, dur):
    return stack([fn(start + t) for t in frame_times(dur)])


# ----------------------------------------------------------------------------- the shots
# 140-185 come from one continuous movie-time action (see im_fight / th_fight): (shot, start, dur)
FIGHT_SHOTS = [("140", 24.524, 0.959), ("150", 25.484, 1.043), ("160", 26.526, 0.834), ("170", 27.361, 0.626), ("180", 27.986, 0.626), ("185", 28.612, 0.792),
               ("190", 29.404, 1.084), ("200", 30.489, 0.626), ("210", 31.114, 0.459), ("213", 31.573, 0.334), ("216", 31.907, 0.918), ("220", 32.824, 2.419),
               ("230", 35.244, 0.626), ("240", 35.869, 1.460), ("250", 37.329, 0.542), ("255", 37.871, 0.667), ("260", 38.538, 1.210), ("262", 39.748, 1.335),
               ("265", 41.083, 0.709), ("270", 41.792, 0.542), ("275", 42.334, 0.459), ("280", 42.793, 0.584), ("290", 43.377, 0.709), ("295", 44.086, 0.459),
               ("300", 44.544, 0.459), ("310", 45.003, 0.542), ("320", 45.545, 3.212), ("340", 48.757, 0.834), ("350", 49.591, 2.669), ("360", 52.261, 0.500),
               ("370", 52.761, 0.292), ("375", 53.053, 0.959), ("380", 54.012, 0.667), ("390", 54.680, 0.459), ("395", 55.138, 0.375), ("400", 55.514, 0.626),
               ("405", 56.139, 0.459), ("410", 56.598, 1.126), ("415", 57.724, 0.375), ("420", 58.100, 0.667), ("425", 58.767, 0.584), ("430", 59.351, 0.959),
               ("435", 60.310, 1.919), ("440", 62.229, 1.168), ("445", 63.397, 1.335), ("450", 64.731, 0.709), ("455", 65.440, 0.918), ("460", 66.358, 1.418),
               ("465", 67.776, 0.751), ("470", 68.527, 2.002), ("475", 70.529, 1.126), ("480", 71.655, 1.210), ("485", 72.864, 0.542), ("490", 73.407, 0.959),
               ("505", 74.366, 0.626), ("520", 74.992, 0.959), ("525", 75.951, 0.542), ("530", 76.493, 0.918), ("535", 77.411, 0.417), ("540", 77.828, 1.376),
               ("545", 79.204, 0.667), ("550", 79.871, 0.667), ("555", 80.539, 0.500), ("560", 81.039, 1.554)]

def build_shots():
    s = {}
    # Thanos 010/020/030 are HAND-KEYED from the reference. The movie shots are medium/close
    # (legs out of frame), so GVHMR had to guess his legs and tilt -> he floated and leaned.
    # captures/010_* and 030_* are kept for reference only.
    # the nanotech piece slams into his raised hand at 0.74 (FX nanoshot): the hand is knocked along
    # its flight, the arm and chest absorb it; the recoil carries on into the 020 close-up
    NANO_HIT = (0.74, "LeftHand", (-0.81, -0.31, 0.54), 28)
    s["010_thanos"] = react(keyed(TH_010, 0.834), *NANO_HIT)
    s["020_thanos"] = react(keyed(TH_020, 1.418), NANO_HIT[0] - 0.834, *NANO_HIT[1:])
    s["030_thanos"] = keyed(TH_030, 0.376, smooth=5)
    s["040_thanos"] = keyed(TH_040, 1.167)

    # 050 Iron Man rises. Camera dollies in, so GVHMR's forward drift is fake -> lock_xz.
    s["050_ironman"] = from_capture("050_ironman_stand.rbxmx", 2.086, lock_xz=True)
    im = {p: m.copy() for p, m in pose_of(s["050_ironman"], -1).items()}
    for side, x in (("Left", -1), ("Right", 1)):
        orient(im, f"{side}UpperArm", (0.22 * x, -0.97, 0.02))
        orient(im, f"{side}LowerArm", (0.12 * x, -0.98, -0.1))
        orient(im, f"{side}Hand", (0.1 * x, -0.99, -0.05), (-x, 0, 0.2))
    # Blend arms down into relaxed 20° power stance as he rises
    n50 = len(s["050_ironman"]["LowerTorso"])
    blend_start = int(n50 * 0.45)
    for i in range(blend_start, n50):
        w = ease((i - blend_start) / max(1, n50 - 1 - blend_start))
        p_now = pose_of(s["050_ironman"], i)
        p_blended = blend(p_now, im, w)
        for part in ("LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand"):
            s["050_ironman"][part][i] = p_blended[part]

    # Dialogue close-ups (hand-keyed): bodies hold, only the head acts.
    s["070_thanos"] = keyed(TH_070, 1.335)
    s["090_thanos"] = keyed(TH_090, 5.422, smooth=11)
    s["060_ironman"] = keyed([(0.0, with_head(im, 0, 0)), (1.0, with_head(im, -2, 3)),
                              (1.967, with_head(im, -1, 2, 1))], 1.967)
    s["080_ironman"] = keyed([(0.0, with_head(im, -1, 2)), (0.45, with_head(im, -5, 2)),     # "You know me" — a nod
                              (0.8, with_head(im, -1, 1)), (1.251, with_head(im, -2, 0))], 1.251)
    s["100_ironman"] = keyed([(0.0, with_head(im, -2, 0)), (0.9, with_head(im, -6, 0, 3)),   # leans into "curse"
                              (2.244, with_head(im, -4, 0, 2))], 2.244)

    # 110/115 the launch: pods grow on his shoulders (FX), he pitches torso forward 18 deg and braces, then watches missiles climb.
    P_110 = make_pose(torso=(0, 18), head=(-7, 0, 1), L_up=(-0.25, -0.92, 0.15), R_up=(0.25, -0.92, 0.15))
    s["110_ironman"] = keyed([(0.0, P_110), (0.6, with_head(P_110, -10, 0)),
                              (1.21, with_head(P_110, -8, 0))], 1.21)
    s["115_ironman"] = keyed([(0.0, with_head(im, -4, 0)), (0.45, with_head(im, 14, -2)),
                              (1.293, with_head(im, 24, -6))], 1.293)
    s["120_thanos"] = keyed(TH_120, 0.834)
    s["130_thanos"] = keyed(TH_130, 3.086)
    s["130a_thanos"] = stack([at_keys(t, TH_130) for t in frame_times(1.084)])
    s["130b_thanos"] = stack([at_keys(1.084 + t, TH_130) for t in frame_times(2.002)])

    # Iron Man 140-185 (movie time). Body-space limb sets read off the reference frames.
    FLY = limbs(im, arms=((-0.35, -0.85, 0.4), (-0.3, -0.8, 0.5)), legs=((-0.08, -0.95, -0.3), (-0.05, -0.95, 0.3)),
                palm=(0, -0.6, 0.8))                                    # hand thrusters push down-back
    KICK = limbs(im, arms=((-0.4, -0.9, 0.15), (-0.35, -0.9, 0.2)), legs=((-0.03, -1, 0), (-0.03, -1, 0)))
    TUCK = limbs(im, arms=((-0.4, -0.3, -0.85), (-0.3, 0.2, -0.93)), legs=((-0.1, -0.2, -0.97), (-0.05, -0.95, 0.2)))
    CROUCH = limbs(im, arms=((-0.8, -0.55, -0.1), (-0.85, -0.45, -0.2)), legs=((-0.15, -0.85, -0.5), (-0.1, -0.95, 0.3)))
    SPREAD = limbs(im, arms=((-0.97, -0.2, -0.05), (-0.97, -0.1, -0.2)), palm=(0, -1, 0))   # cannons forming
    COILED_RAM = with_head(arm(arm(im, "Left", (-0.45, 0.25, -0.85), (0.15, 0.65, -0.75), palm=(0, 0, -1)),
                               "Right", (0.5, -0.15, -0.85), (-0.25, 0.55, -0.8), palm=(-1, 0, 0)), 4, -15)
    PUNCH = limbs(im, arms=((-0.18, -0.1, -0.98), (-0.1, 0, -1)), legs=((-0.08, -0.97, 0.2), (-0.05, -0.9, 0.4)))
    # 190-220 (movie 29.4-35.25): Thanos' hook at 29.95, he grabs and crushes the helmet, rips it off
    # at 30.55; the face; his punch at 31.50; the mask re-forms at 31.58; Iron Man swings, Thanos
    # hammers him down at 32.04, he flies off and skids to a stop face down by 32.6.
    GUARD_IM = limbs(im, arms=((-0.35, -0.55, -0.75), (-0.05, 0.55, -0.83)))
    GRIP_IM = with_head(limbs(im, arms=((-0.15, 0.55, -0.82), (0.2, 0.85, -0.48)),
                              legs=((-0.1, -0.95, -0.2), (-0.05, -0.95, 0.25))), -18, 0)   # hands on Thanos' wrist
    SHOCK_IM = with_head(limbs(im, arms=((-0.18, -0.98, -0.05), (-0.14, -0.98, 0.05))), 8, 20)  # arms down naturally, head up-left
    LOOK_UP_IM = with_head(SHOCK_IM, 8, 20)
    SWING_IM = arm(arm(with_head(GUARD_IM, 15, -25), "Right", (0.35, -0.2, -0.9), (-0.7, 0.45, -0.55)), "Left", (-0.18, -0.95, -0.15), (-0.14, -0.95, 0.05)) # right arm counter-swing across chest, left down
    THROWN = limbs(im, arms=((-0.9, 0.3, 0.3), (-0.8, 0.6, 0.1)), legs=((-0.2, -0.8, -0.55), (-0.1, -0.9, 0.4)))
    LYING = with_head(limbs(im, arms=((-0.4, -0.2, 0.9), (0.4, -0.2, 0.9)),
                            legs=((-0.1, 0, -1), (-0.05, 0, -1))), 20, 10)                        # legs and body flat along ground
    KNEEL_IM = with_head(limbs(CROUCH, arms=((-0.22, -0.92, -0.2), (0.22, -0.92, -0.2))), 10, 22) # shoulders lowered, glaring up-left
    # Deep braced athletic lunge: front left knee bent ~65 deg, back right leg extended ~45 deg, torso forward
    SHIELD_IM = arm(arm(limbs(im, legs=((-0.25, -0.65, -0.7), (0.2, -0.7, 0.7))), "Left",
                        (-0.35, -0.2, -0.9), (0.3, 0.75, -0.6), palm=(0, 0, -1)),
                    "Right", (0.3, -0.25, -0.92), (-0.5, 0.35, -0.8), palm=(-1, 0, 0))
    # Low aerodynamic charge sprinting/jetting forward-left under the beam
    JUMP_IM = with_head(limbs(im, arms=((-0.45, -0.4, 0.8), (0.45, -0.4, 0.8)), legs=((-0.15, -0.35, -0.92), (0.1, -0.45, 0.88))), 25, -15)
    # Airborne thruster lunge/barrel-roll angled 35 deg diagonally upward
    DIVE_IM = with_head(limbs(im, arms=((-0.2, -0.85, 0.48), (0.35, 0.8, 0.48)), legs=((-0.1, -0.5, 0.85), (0.1, -0.5, 0.85))), 20, 10)
    PIN_IM = with_head(CROUCH, -18, 0)                                     # crouched on Thanos' hand, looking down at him
    WIND_IM = arm(arm(PIN_IM, "Right", (0.75, -0.15, 0.64), (0.55, 0.05, 0.83)), "Left", (-0.5, -0.5, -0.7), (-0.2, 0.2, -0.95))
    PUNCH_IM = arm(PIN_IM, "Right", (0.1, 0.05, -0.99), (0.05, 0.05, -1))  # re-aimed onto Thanos' face below (IK)
    CROUCH_LAND_IM = with_head(limbs(im, arms=((-0.4, -0.65, -0.5), (0.4, -0.65, -0.5)),
                                      legs=((-0.2, -0.4, -0.9), (0.2, -0.9, 0.4))), 10, 0)
    FLIP_IM = limbs(im, arms=((-0.8, 0.4, 0.4), (0.8, 0.4, 0.4)),
                    legs=((-0.1, 0.8, -0.5), (0.3, -0.8, 0.5)))
    SKID_IM = with_head(limbs(im, arms=((-0.6, -0.6, 0.3), (-0.5, -0.6, 0.4)),
                              legs=((-0.15, -0.75, -0.5), (-0.1, -0.8, 0.4))), 22, 10)
    SCRAMBLE_IM = with_head(limbs(im, arms=((-0.35, -0.7, -0.55), (0.35, -0.7, -0.55)),
                                  legs=((-0.25, -0.7, 0.6), (0.25, -0.7, 0.6))), 35, 12)
    PROPPED_IM = with_head(limbs(im, arms=((-0.45, -0.55, 0.65), (0.45, -0.55, 0.65)),
                                 legs=((-0.18, -0.92, -0.2), (-0.08, -0.95, 0.25))), 26, -10)
    SWEPT_IM = limbs(im, arms=((-0.8, 0.2, -0.55), (-0.6, 0.6, -0.5)), legs=((-0.1, -0.5, -0.85), (-0.05, -0.85, 0.5)))
    FLAT_IM = with_head(limbs(im, arms=((-0.55, -0.8, 0.2), (-0.5, -0.7, 0.5)), legs=((-0.12, -1, 0.05), (-0.08, -1, 0.1))), 18, 8)
    BLOCK_IM = with_head(limbs(im, arms=((-0.3, 0.15, -0.94), (0.6, 0.45, -0.66)), legs=((-0.2, -0.85, -0.45), (-0.1, -0.95, 0.3))), 20, 0)
    HIT_IM = with_head(limbs(im, arms=((-0.75, -0.2, -0.6), (-0.6, 0.3, -0.75)), legs=((-0.2, -0.85, -0.45), (-0.1, -0.95, 0.3))), 24, 18)
    RECOIL_IM = with_head(limbs(im, arms=((-0.25, -0.4, -0.88), (0.15, 0.6, -0.75)), legs=((-0.2, -0.85, -0.45), (-0.1, -0.95, 0.3))), 15, -25)
    HANG_IM = with_head(limbs(GRIP_IM, legs=((-0.08, -1, 0.1), (-0.05, -0.97, 0.2))), -10, 0)
    AIM_IM = arm(KNEEL_IM, "Right", (0.1, 0.15, -0.98), (0.05, 0.05, -1.0), palm=(0, 1, 0))
    AIM_DUAL_IM = arm(arm(KNEEL_IM, "Right", (0.08, 0.15, -0.98), (0.04, 0.05, -1.0), palm=(0, 1, 0)),
                      "Left", (-0.08, 0.15, -0.98), (-0.04, 0.05, -1.0), palm=(0, 1, 0))
    STRAIN_DUAL_IM = with_head(limbs(AIM_DUAL_IM, arms=((-0.1, 0.2, -0.97), (0.1, 0.2, -0.97))), 16, 0)
    REGEN_IM = arm(arm(KNEEL_IM, "Left", (-0.15, -0.25, -0.96), (0.1, 0.45, -0.88), palm=(0, -1, 0)),
                   "Right", (0.2, -0.75, -0.6), (0.15, -0.85, -0.4))
    BRACED_IM = with_head(limbs(arm(arm(im, "Left", (-0.35, -0.2, -0.9), (0.3, 0.75, -0.6), palm=(0, 0, -1)),
                                    "Right", (0.3, -0.25, -0.92), (-0.5, 0.35, -0.8), palm=(-1, 0, 0)),
                                legs=((-0.25, -0.6, -0.75), (0.22, -0.65, 0.72))), -6, 0)
    IM_POSES = [(24.40, FLY), (25.15, FLY), (25.45, KICK), (25.75, KICK), (25.95, TUCK), (26.45, TUCK),
                (26.62, CROUCH), (26.9, CROUCH), (27.3, im), (27.6, COILED_RAM), (27.99, COILED_RAM), (28.12, PUNCH), (29.5, PUNCH),
                (29.75, GUARD_IM), (29.95, GUARD_IM), (30.12, GRIP_IM), (30.50, GRIP_IM), (30.62, SHOCK_IM),
                (30.85, LOOK_UP_IM), (31.12, LOOK_UP_IM), (31.36, with_head(limbs(im, arms=((-0.25, -0.6, 0.7), (0.25, -0.6, 0.7)), legs=((-0.15, -0.9, -0.3), (-0.1, -0.9, 0.3))), 25, -15)), (31.50, GUARD_IM), (31.62, GUARD_IM), (31.86, SWING_IM), (32.02, SWING_IM),
                (32.12, THROWN), (32.25, LYING), (34.9, LYING),
                (35.20, KNEEL_IM), (35.85, KNEEL_IM), (36.6, with_head(CROUCH, 6, 0)), (37.30, SHIELD_IM), (38.50, SHIELD_IM),
                (38.62, BRACED_IM), (41.09, BRACED_IM),
                (41.30, JUMP_IM), (41.62, JUMP_IM), (41.85, DIVE_IM), (42.80, GUARD_IM), (43.15, GUARD_IM), (43.35, PIN_IM), (44.10, PIN_IM),
                (44.55, WIND_IM), (45.05, WIND_IM), (45.39, PUNCH_IM), (45.80, PUNCH_IM),
                (46.6, GUARD_IM), (52.70, GUARD_IM), (52.768, CROUCH_LAND_IM), (52.95, CROUCH_LAND_IM),
                (53.15, FLIP_IM), (53.50, FLIP_IM), (53.80, FLIP_IM),
                (54.02, SKID_IM), (54.50, SKID_IM), (55.00, FLAT_IM), (55.30, FLAT_IM),
                (55.521, SCRAMBLE_IM), (56.13, SCRAMBLE_IM),
                (56.30, HIT_IM), (56.605, PROPPED_IM), (57.25, PROPPED_IM),
                (57.35, HIT_IM), (58.20, HIT_IM), (58.40, with_head(HIT_IM, 20, -40)),
                (58.85, with_head(HIT_IM, 20, -40)),
                (59.10, with_head(BLOCK_IM, 20, -20)),
                (59.40, BLOCK_IM),
                (59.50, with_head(HIT_IM, 20, 45)),
                (60.30, with_head(HIT_IM, 20, 45)),
                (60.60, HANG_IM), (61.00, HANG_IM), (61.30, HANG_IM), (61.60, HANG_IM),
                (61.70, THROWN), (62.25, THROWN), (62.40, TUCK), (62.75, FLAT_IM), (63.40, FLAT_IM),
                (64.74, FLAT_IM), (64.95, with_head(CROUCH, 12, 0)), (65.20, KNEEL_IM),
                (65.35, AIM_IM), (65.53, AIM_IM), (65.85, AIM_IM), (66.15, AIM_IM), (66.45, AIM_IM),
                (66.70, REGEN_IM), (67.783, AIM_IM),
                (68.20, AIM_DUAL_IM), (68.534, AIM_DUAL_IM), (69.50, AIM_DUAL_IM), (70.536, AIM_DUAL_IM),
                (71.00, STRAIN_DUAL_IM), (71.662, STRAIN_DUAL_IM), (72.00, AIM_DUAL_IM), (72.40, AIM_DUAL_IM), (72.871, AIM_DUAL_IM), (73.35, STRAIN_DUAL_IM),
                (73.41, with_head(RECOIL_IM, 10, -10)),
                (73.75, with_head(RECOIL_IM, 26, -36)),
                (74.10, with_head(RECOIL_IM, 16, -20)),
                (74.37, with_head(RECOIL_IM, 18, -25)),
                (74.65, with_head(BLOCK_IM, 12, -10)),
                (75.00, BLOCK_IM), (76.50, BRACED_IM), (77.42, BRACED_IM),
                (78.00, arm(BRACED_IM, "Left", (-0.4, -0.5, -0.76), (0.2, 0.5, -0.84), palm=(0, 0, -1))),
                (79.21, arm(BRACED_IM, "Left", (-0.2, 0.6, -0.78), (0.1, 0.95, -0.3), palm=(0, 0, -1))),
                (79.88, BRACED_IM), (80.55, BRACED_IM), (80.90, with_head(BRACED_IM, -6, 0)),
                (81.05, with_head(BRACED_IM, -12, 0)), (82.60, with_head(BRACED_IM, -16, 0))]
    IM_D = [(24.40, 2), (25.35, 20), (25.49, 24), (25.70, 36.8), (26.62, 30), (26.95, 29.3), (27.99, 29.3),
            (28.33, 35.8), (29.5, 40.5), (32.04, 40.5), (32.40, 37.2), (32.70, 36.6)]   # studs toward Thanos
    # 230-262: up again, he turns to face Thanos (yaw 55: Thanos is at his front-left) and is driven
    # back along that line by the beam: PUSH studs from 38.55, decelerating
    PUSH = [(38.55, 0), (39.4, 4.2), (40.3, 7.4), (41.09, 9.4)]
    U = np.array([0.82, 0.57])                                          # beam direction in his rig XZ (+X, +Z)
    IM_X = [(28.619, 4.0), (29.40, 4.0), (30.10, 1.2), (30.496, -2.6), (31.121, -2.4), (31.58, -2.4), (31.914, 0.0), (32.04, 0), (32.40, 6.2), (32.70, 7.0), (41.09, 7.0), (41.55, 8.69), (41.80, 8.69), (42.95, -8.11), (45.8, -8.11)]
    IM_YAW = [(27.3, 0), (27.68, 35), (27.99, 35), (28.15, 0), (29.411, 60), (30.496, 80), (31.121, 130), (31.58, 120), (31.914, 0), (34.9, 0), (35.2, 55), (41.09, 55), (41.40, 62), (44.10, 62), (44.60, 240), (45.05, 255), (45.39, 418), (45.8, 422)]   # full spin into the blow
    IM_D2 = [(41.09, 0), (41.55, 2.46), (41.80, 2.46), (42.95, 11.0), (45.8, 11.0)]   # extra forward on top of IM_D (world +Z)
    IM_H = [(24.40, 2.2), (25.01, 2.3), (25.3, 2.5), (25.49, 3.4), (25.70, 4.0), (26.01, 7.5), (26.15, 7.8), (26.62, 0), (27.99, 0), (28.15, 0.4), (29.5, 0.4),
            (29.75, 0), (30.12, -0.25), (30.50, -0.25), (30.7, 0), (32.04, 0), (32.12, 0.4), (32.24, -0.95), (34.9, -0.95), (35.2, -0.55), (35.85, -0.55), (36.6, -0.25), (37.3, -0.35), (41.09, -0.45),
            (41.35, 1.6), (41.62, 0.4), (41.85, 1.0), (42.6, 0.9), (42.95, 1.6), (43.30, 0.8), (45.8, 0.8)]
    IM_PITCH = [(24.40, 310), (25.01, 305), (25.2, 315), (25.49, 60), (25.60, 80), (25.70, 80), (26.01, 105), (26.62, 360), (27.3, 360), (27.68, 340), (27.99, 360),
                (28.15, 360), (29.5, 360), (29.75, 360), (30.12, 352), (30.50, 352), (30.7, 360), (32.04, 360),
                (32.15, 300), (32.25, 270), (34.9, 270), (35.2, 360), (38.5, 360), (38.62, 350), (41.09, 335),
                (41.45, 330), (41.70, 340), (41.85, 325), (42.40, 325), (42.80, 332), (43.15, 332), (43.35, 360), (45.8, 360)]
    IM_DROP = [(26.55, 0), (26.66, 0.06), (27.0, 0), (27.3, 0)]      # landing compression
    # lying on his back (54.02 -> the lift at 60.55): measured in Studio, his lowest part floated 1.96 studs
    # above the ground (the owner's model rides higher than the planning rig). Lowers him in that span only.
    IM_FLOOR = [(53.95, 0), (54.10, 1.6), (60.55, 1.6), (61.00, 0)]   # eases out during the lift (60.55-61.0)

    IM_WX, IM_WZ = [(0, 0)], [(0, 0)]                                   # extra world offset (Iron Man rig: world x = -rig x)

    def im_fight(t):
        push = chan(t, PUSH)
        return moved(at_keys(t, IM_POSES), chan(t, IM_D) - U[1] * push + chan(t, IM_D2) + chan(t, IM_WZ),
                     chan(t, IM_H) - chan(t, IM_DROP) - chan(t, IM_FLOOR), chan(t, IM_PITCH), chan(t, IM_X) + U[0] * push - chan(t, IM_WX),
                     chan(t, IM_YAW))

    # Thanos: lowers his guard, takes the kick in the chest, recovers, is driven back by the cannons.
    READY = dict(L_up=(-0.4, -0.7, -0.6), L_lo=(-0.1, 0.3, -0.95), L_palm=(0.6, 0, 0.8),
                 R_up=(0.4, -0.75, -0.5), R_lo=(0.15, 0.1, -0.98), R_palm=(-0.6, 0, 0.8), stance=0.15)
    # hit guard: the gauntlet arm goes up in front of his face, the right arm crosses his chest with the fist up
    # (defending and pushing back, not hanging limp); both forearms face forward so the hits land on the guard
    STRUCK = dict(L_up=(-0.35, 0.55, -0.75), L_lo=(-0.1, 0.95, -0.3), L_palm=(0, 0, -1),
                  R_up=(-0.2, 0.3, -0.93), R_lo=(-0.7, 0.6, -0.4), R_palm=(-1, 0, 0), stance=0.22)
    REACH_ARM = dict(L_up=(-0.25, 0.45, -0.85), L_lo=(-0.1, 0.2, -0.98), L_palm=(0.3, -0.2, 0.9),
                     R_up=(0.12, -0.95, 0.15), R_lo=(0.1, -0.95, 0.2), R_palm=(-1, 0, 0), stance=0.20)
    BRACE = dict(L_up=(-0.3, 0.45, -0.84), L_lo=(-0.15, 0.9, -0.4), L_palm=(0, 0, -1),
                 R_up=(0.12, -0.95, 0.15), R_lo=(0.1, -0.95, 0.2), R_palm=(-1, 0, 0), stance=0.24)
    TH_POSES = [(24.40, TH_130[-1][1]), (24.95, make_pose(torso=(4, 6), head=(-4, 0), **READY)),
                (25.68, make_pose(torso=(4, 6), head=(-4, 0), **READY)),
                (25.80, make_pose(torso=(-4, -16), head=(14, -4), **STRUCK)),     # kick to the chest
                (26.15, make_pose(torso=(-2, -8), head=(4, 0), **STRUCK)),
                (26.70, make_pose(torso=(2, 6), head=(-4, 0), **READY)),
                (27.35, make_pose(torso=(2, 6), head=(-4, 0), **READY)),
                (27.68, make_pose(torso=(10, 4), head=(-4, -8), **REACH_ARM)),
                (28.00, make_pose(torso=(2, 6), head=(-4, 0), **READY)),
                (28.28, make_pose(torso=(2, 6), head=(-4, 0), **READY)),
                (28.42, make_pose(torso=(0, -10), head=(4, 0), **BRACE)),         # cannons slam in
                (29.5, make_pose(torso=(0, -12), head=(2, 0), **BRACE))]
    # 190-220
    G_L = dict(L_up=(-0.4, -0.7, -0.6), L_lo=(-0.1, 0.3, -0.95), L_palm=(0.6, 0, 0.8))     # gauntlet up in guard
    LOW_L = dict(L_up=(-0.2, -0.95, 0.1), L_lo=(-0.1, -0.95, -0.25), L_palm=(1, 0, 0))
    GRIP_L = dict(L_up=(-0.15, -0.25, -0.96), L_lo=(0, -0.1, -1), L_palm=(0.3, -0.9, 0))    # gauntlet on his shoulder
    REL_R = dict(R_up=(0.18, -0.98, -0.02), R_lo=(0.12, -0.98, -0.12), R_palm=(-1, 0, 0.2))
    REL_L = dict(L_up=(-0.15, -0.98, -0.05), L_lo=(-0.1, -0.9, -0.4), L_palm=(1, 0.3, 0))
    LOOK_L = dict(L_up=(-0.12, -0.9, -0.42), L_lo=(0.35, 0.05, -0.94), L_palm=(0, 1, 0))      # palm up, studying it
    TH_WALK_R = make_pose(torso=(0, 3), head=(-4, 0), stance=0.22,
                          R_up=(0.2, -0.9, -0.25), R_lo=(0.1, -0.95, -0.15), R_palm=(-1, 0, 0),
                          L_up=(-0.2, -0.9, 0.25), L_lo=(-0.1, -0.95, 0.15), L_palm=(1, 0, 0))
    orient(TH_WALK_R, "RightUpperLeg", (0.15, -0.92, -0.35))
    orient(TH_WALK_R, "RightLowerLeg", (0.05, -0.98, -0.15))
    orient(TH_WALK_R, "LeftUpperLeg", (-0.15, -0.92, 0.35))
    orient(TH_WALK_R, "LeftLowerLeg", (-0.05, -0.98, 0.15))

    TH_WALK_L = make_pose(torso=(0, 3), head=(-4, 0), stance=0.22,
                          R_up=(0.2, -0.9, 0.25), R_lo=(0.1, -0.95, 0.15), R_palm=(-1, 0, 0),
                          L_up=(-0.2, -0.9, -0.25), L_lo=(-0.1, -0.95, -0.15), L_palm=(1, 0, 0))
    orient(TH_WALK_L, "LeftUpperLeg", (-0.15, -0.92, -0.35))
    orient(TH_WALK_L, "LeftLowerLeg", (-0.05, -0.98, -0.15))
    orient(TH_WALK_L, "RightUpperLeg", (0.15, -0.92, 0.35))
    orient(TH_WALK_L, "RightLowerLeg", (0.05, -0.98, 0.15))

    TH_BLOCK_WALK_R = make_pose(torso=(0, 2), head=(-4, 0), stance=0.24,
                                R_up=(0.2, -0.9, -0.2), R_lo=(0.1, -0.95, -0.1), R_palm=(-1, 0, 0),
                                L_up=(-0.15, 0.1, -0.98), L_lo=(0.25, 0.15, -0.95), L_palm=(0, 0, -1))
    orient(TH_BLOCK_WALK_R, "RightUpperLeg", (0.15, -0.92, -0.35))
    orient(TH_BLOCK_WALK_R, "RightLowerLeg", (0.05, -0.98, -0.15))
    orient(TH_BLOCK_WALK_R, "LeftUpperLeg", (-0.15, -0.92, 0.35))
    orient(TH_BLOCK_WALK_R, "LeftLowerLeg", (-0.05, -0.98, 0.15))

    TH_BLOCK_WALK_L = make_pose(torso=(0, 2), head=(-4, 0), stance=0.24,
                                R_up=(0.2, -0.9, 0.2), R_lo=(0.1, -0.95, 0.1), R_palm=(-1, 0, 0),
                                L_up=(-0.15, 0.1, -0.98), L_lo=(0.25, 0.15, -0.95), L_palm=(0, 0, -1))
    orient(TH_BLOCK_WALK_L, "LeftUpperLeg", (-0.15, -0.92, -0.35))
    orient(TH_BLOCK_WALK_L, "LeftLowerLeg", (-0.05, -0.98, -0.15))
    orient(TH_BLOCK_WALK_L, "RightUpperLeg", (0.15, -0.92, 0.35))
    orient(TH_BLOCK_WALK_L, "RightLowerLeg", (0.05, -0.98, 0.15))


    TH_POSES += [
        (29.75, make_pose(torso=(35, 8), head=(-12, -15), R_up=(0.2, 0.1, -0.98), R_lo=(0.1, -0.35, -0.94), R_hand=(0.1, -0.8, -0.5), R_palm=(0, -1, 0.2), stance=0.2, **LOW_L)),
        (29.95, make_pose(torso=(35, 12), head=(-14, -16), R_up=(0.2, -0.1, -0.98), R_lo=(0.1, -0.45, -0.9), R_hand=(0.1, -0.85, -0.5), R_palm=(0, -1, 0.2), stance=0.2, **LOW_L)), # gripping & wrenching helmet
        (30.15, make_pose(torso=(35, 14), head=(-14, -14), R_up=(0.2, -0.1, -0.98), R_lo=(0.1, -0.45, -0.9), R_hand=(0.1, -0.85, -0.5), R_palm=(0, -1, 0.2), stance=0.2, **LOW_L)),
        (30.45, make_pose(torso=(35, 16), head=(-16, -12), R_up=(0.2, -0.1, -0.98), R_lo=(0.1, -0.45, -0.9), R_hand=(0.1, -0.85, -0.5), R_palm=(0, -1, 0.2), stance=0.2, **LOW_L)),  # crushing
        (30.60, make_pose(torso=(38, 8), head=(-8, -10), R_up=(-0.6, 0, -0.8), R_lo=(-0.95, 0.1, -0.3), R_palm=(1, 0, 0), stance=0.2, **LOW_L)),       # rips it off
        (31.12, make_pose(torso=(40, 10), head=(-15, 0), R_up=(0.2, -0.85, -0.4), R_lo=(0.1, -0.95, -0.2), R_palm=(-1, 0, 0), stance=0.22, **LOW_L)),
        (31.36, make_pose(torso=(45, -30), head=(-25, 0), R_up=(0.2, -0.8, -0.55), R_lo=(0.1, -0.9, -0.4), R_palm=(-1, 0, 0), stance=0.24, L_up=(-0.2, -0.8, -0.55), L_lo=(-0.1, -0.9, -0.4), L_palm=(1, 0, 0))), # heavy headbutt lunge
        (31.50, make_pose(torso=(20, 10), head=(-8, -6), R_up=(0.1, 0.1, -0.99), R_lo=(0.0, 0.05, -1), R_palm=(0, -1, 0), stance=0.2, **GRIP_L)),       # punch
        (31.92, make_pose(torso=(-6, 4), head=(6, 0), R_up=(0.25, 0.9, 0.35), R_lo=(0.05, 0.95, 0.3), R_palm=(-1, 0, 0), stance=0.22, **G_L)),
        (32.06, make_pose(torso=(10, 32), head=(-20, 0), R_up=(0.1, -0.5, -0.86), R_lo=(0.05, -0.85, -0.5), R_palm=(-1, 0, 0), stance=0.22,
                          L_up=(-0.5, -0.7, -0.5), L_lo=(-0.3, -0.4, -0.85), L_palm=(1, 0, 0))),                                                         # hammer
        (32.60, make_pose(torso=(0, 4), head=(-6, 0), stance=0.15, **REL_L, **REL_R)),
        (33.30, low_crouch(make_pose(torso=(35, 6), head=(-15, 10), stance=0.20, L_up=(-0.25, -0.85, -0.45), L_lo=(0.15, -0.4, -0.9), R_up=(0.25, -0.85, -0.45), R_lo=(-0.15, -0.4, -0.9), R_palm=(-1, 0, 0), L_palm=(1, 0, 0)))),
        (34.00, low_crouch(make_pose(torso=(40, 6), head=(-15, 12), stance=0.22, L_up=(-0.25, -0.85, -0.45), L_lo=(0.15, -0.4, -0.9), R_up=(0.25, -0.85, -0.45), R_lo=(-0.15, -0.4, -0.9), R_palm=(-1, 0, 0), L_palm=(1, 0, 0)))), # crouched 3/4 stance, fists near waist (movie 34.0)
        (34.50, make_pose(torso=(2, 12), head=(-30, 10), stance=0.15, R_up=(0.2, -0.85, -0.5), R_lo=(-0.6, 0.05, -0.8), R_palm=(-0.3, 0, -0.9), **LOOK_L)),
        (34.80, make_pose(torso=(-8, 6), head=(-20, -10), stance=0.15, R_up=(0.5, -0.6, -0.6), R_lo=(0.85, 0.35, -0.4), R_palm=(0, 0, -1), **LOOK_L)),  # pulls it out
        (35.15, make_pose(torso=(-4, -4), head=(18, -4), stance=0.15, R_up=(0.7, -0.4, -0.55), R_lo=(0.95, 0.2, 0.2), R_palm=(0, -1, 0), **LOOK_L)),   # laughs
        (35.40, make_pose(torso=(-4, -4), head=(18, -4), stance=0.15, R_up=(0.7, -0.4, -0.55), R_lo=(0.95, 0.2, 0.2), R_palm=(0, -1, 0), **LOOK_L)),
        # 240-262: turns to Iron Man (yaw 55), gauntlet arm up, fires the purple beam at 37.0 and holds it
        (35.90, make_pose(torso=(0, 4), head=(-4, 0), stance=0.18, **REL_R, L_up=(-0.3, -0.85, -0.4), L_lo=(-0.1, -0.4, -0.9), L_palm=(1, 0, 0))),
        (36.60, make_pose(torso=(-8, 6), head=(-2, 4), stance=0.22, **REL_R, L_up=(-0.15, -0.1, -0.98), L_lo=(-0.05, 0.05, -1), L_palm=(0, 0.3, -0.95))),
        (37.00, make_pose(torso=(-12, 10), head=(-4, 6), stance=0.24, R_up=(0.6, -0.55, 0.55), R_lo=(0.3, -0.5, 0.8), R_palm=(-1, 0, 0),
                          L_up=(-0.12, 0.02, -0.99), L_lo=(-0.04, 0.06, -1), L_palm=(0, 0.1, -1))),
        (38.55, make_pose(torso=(-12, 12), head=(-5, 6), stance=0.24, R_up=(0.6, -0.55, 0.55), R_lo=(0.3, -0.5, 0.8), R_palm=(-1, 0, 0),
                          L_up=(-0.12, 0.02, -0.99), L_lo=(-0.04, 0.06, -1), L_palm=(0, 0.1, -1))),
        (41.09, make_pose(torso=(-12, 14), head=(-6, 6), stance=0.24, R_up=(0.6, -0.55, 0.55), R_lo=(0.3, -0.5, 0.8), R_palm=(-1, 0, 0),
                          L_up=(-0.12, 0.02, -0.99), L_lo=(-0.04, 0.06, -1), L_palm=(0, 0.1, -1))),
    ]
    REACH_L = dict(L_up=(-0.1, -0.35, -0.93), L_lo=(-0.05, -0.3, -0.95), L_palm=(0, -1, 0))
    TH_POSES += [
        (41.60, make_pose(torso=(-6, 10), head=(-4, 4), stance=0.24, **REL_R, L_up=(-0.2, -0.4, -0.9), L_lo=(-0.1, -0.2, -0.97), L_palm=(1, 0, 0))),
        (42.80, make_pose(torso=(16, 6), head=(2, 0), stance=0.26, R_up=(0.15, 0.05, -0.98), R_lo=(0.05, 0.05, -1.0), R_palm=(-1, 0, 0), L_up=(-0.35, -0.3, -0.88), L_lo=(-0.1, 0.2, -0.98), L_palm=(1, 0, 0))), # heavy forward punch
        (43.15, make_pose(torso=(16, 6), head=(2, 0), stance=0.26, R_up=(0.15, 0.05, -0.98), R_lo=(0.05, 0.05, -1.0), R_palm=(-1, 0, 0), L_up=(-0.35, -0.3, -0.88), L_lo=(-0.1, 0.2, -0.98), L_palm=(1, 0, 0))),
        (43.35, kneel(make_pose(torso=(-2, 50), head=(-8, 0), **REL_R, **REACH_L))),               # hand slammed into the ground
        (44.10, kneel(make_pose(torso=(-2, 46), head=(16, 0), **REL_R, **REACH_L))),               # looks up at him
        (45.36, kneel(make_pose(torso=(-2, 44), head=(22, 4), **REL_R, **REACH_L))),
        (45.80, kneel(make_pose(torso=(-10, 34), head=(-10, -30), **REL_R, **REACH_L))),          # the blow snaps his head away
        (46.60, kneel(make_pose(torso=(-6, 42), head=(-30, -18), **REL_R, **REACH_L))),          # head hangs, stunned
        (47.30, kneel(make_pose(torso=(-4, 42), head=(-28, -14), **REL_R, **REACH_L))),
        (47.70, kneel(make_pose(torso=(-4, 42), head=(-26, -12), **REACH_L, R_up=(0.3, -0.4, -0.85), R_lo=(-0.2, 0.9, -0.4), R_palm=(-0.5, 0, -0.85)))),   # fingers to his brow
        (48.55, kneel(make_pose(torso=(-4, 42), head=(-24, -10), **REACH_L, R_up=(0.3, -0.4, -0.85), R_lo=(-0.2, 0.9, -0.4), R_palm=(-0.5, 0, -0.85)))),
        (48.85, kneel(make_pose(torso=(-4, 40), head=(-34, 6), **REACH_L, R_up=(0.25, -0.75, -0.6), R_lo=(-0.1, 0.25, -0.96), R_palm=(0, 1, 0)))),   # looks at his fingers
        (49.55, kneel(make_pose(torso=(-4, 40), head=(-36, 8), **REACH_L, R_up=(0.25, -0.75, -0.6), R_lo=(-0.1, 0.25, -0.96), R_palm=(0, 1, 0)))),
        (50.30, kneel(make_pose(torso=(-2, 36), head=(-12, 2), **REL_R, **REACH_L))),            # raises his eyes
        (51.60, kneel(make_pose(torso=(-2, 34), head=(2, 4), **REL_R, **REACH_L))),              # looks at Iron Man, half a smile
        (52.90, kneel(make_pose(torso=(-2, 34), head=(4, 4), **REL_R, **REACH_L))),
        (53.00, kneel(make_pose(torso=(20, 34), head=(0, 0), **REACH_L,
                                R_up=(0.15, -0.6, -0.8), R_lo=(0.1, -0.7, -0.7), R_palm=(-1, 0, 0)))),             # sweeps his legs
        (53.80, make_pose(torso=(0, 10), head=(-6, 0), stance=0.2, **REL_R, **REL_L)),                  # rises
        (54.69, make_pose(torso=(-25, 12), head=(-10, 0), stance=0.24,
                          R_up=(0.4, -0.7, 0.3), R_lo=(0.2, -0.8, 0.5), R_palm=(-1, 0, 0),
                          L_up=(-0.25, 0.25, -0.93), L_lo=(0.1, 0.15, -0.98), L_palm=(0, 0, -1))),          # charges, left Gauntlet extended forward
        (55.40, kneel(make_pose(torso=(0, 34), head=(-30, 0), stance=0.3, **REL_L,
                          R_up=(0.4, 0.6, 0.7), R_lo=(0.1, 0.95, 0.3), R_palm=(-1, 0, 0)))),                 # over him, fist high
        (56.15, kneel(make_pose(torso=(0, 56), head=(-40, 0), stance=0.3, **REL_L, R_up=(0.1, -0.6, -0.8), R_lo=(0, -0.9, -0.4), R_palm=(-1, 0, 0)))),  # punch 1
        (56.80, kneel(make_pose(torso=(0, 34), head=(-30, 0), stance=0.3, **REL_L,
                          R_up=(0.4, 0.6, 0.7), R_lo=(0.1, 0.95, 0.3), R_palm=(-1, 0, 0)))),
        (57.33, kneel(make_pose(torso=(-8, 68), head=(-46, 0), stance=0.3, **REL_L, R_up=(0.1, -0.6, -0.8), R_lo=(0, -0.9, -0.4), R_palm=(-1, 0, 0)))),  # punch 2
        (57.90, kneel(make_pose(torso=(0, 34), head=(-30, 0), stance=0.3, **REL_L,
                          R_up=(0.4, 0.6, 0.7), R_lo=(0.1, 0.95, 0.3), R_palm=(-1, 0, 0)))),
        (58.35, kneel(make_pose(torso=(-8, 68), head=(-46, 0), stance=0.3, **REL_L, R_up=(0.1, -0.6, -0.8), R_lo=(0, -0.9, -0.4), R_palm=(-1, 0, 0)))),  # punch 3, the face
        (58.60, kneel(make_pose(torso=(0, 34), head=(-30, 0), stance=0.3, **REL_L,
                          R_up=(0.4, 0.6, 0.7), R_lo=(0.1, 0.95, 0.3), R_palm=(-1, 0, 0)))),
        (58.85, kneel(make_pose(torso=(0, 70), head=(-48, 0), stance=0.3, **REL_L,
                          R_up=(0.1, -0.6, -0.8), R_lo=(0, -0.9, -0.4), R_palm=(-1, 0, 0)))),  # punch 4
        (59.15, kneel(make_pose(torso=(-10, 40), head=(-30, 0), stance=0.3, **REL_L,
                          R_up=(-0.3, 0.4, -0.85), R_lo=(-0.2, 0.8, -0.55), R_palm=(-1, 0, 0)))),
        (59.45, kneel(make_pose(torso=(15, 68), head=(-45, 10), stance=0.3, **REL_L,
                          R_up=(0.2, -0.5, -0.85), R_lo=(-0.3, -0.7, -0.65), R_palm=(-1, 0, 0)))),  # punch 5
        (59.90, kneel(make_pose(torso=(5, 38), head=(-25, 0), stance=0.3, **REL_L,
                          R_up=(0.2, -0.8, -0.5), R_lo=(0.1, -0.9, -0.3), R_palm=(-1, 0, 0)))),
        (60.30, kneel(make_pose(torso=(0, 50), head=(-35, 0), stance=0.3, **REL_L,
                          R_up=(0.1, -0.6, -0.8), R_lo=(0, -0.85, -0.5), R_palm=(0, -1, 0)))),   # reaching down
        (60.55, kneel(make_pose(torso=(0, 52), head=(-36, 0), stance=0.3, **REL_L,
                          R_up=(0.1, -0.5, -0.85), R_lo=(0, -0.85, -0.5), R_palm=(0, -1, 0)))),  # grab collar
        (61.00, make_pose(torso=(0, 6), head=(-12, 0), stance=0.24, **REL_L,
                          R_up=(0.15, -0.1, -0.98), R_lo=(0.1, 0.1, -0.99), R_palm=(0, -1, 0))),  # standing, holds him
        (61.45, make_pose(torso=(0, 4), head=(-10, 0), stance=0.24,
                          R_up=(0.15, -0.1, -0.98), R_lo=(0.1, 0.1, -0.99), R_palm=(0, -1, 0),
                          L_up=(0.2, -0.2, -0.96), L_lo=(0.1, 0.1, -0.99), L_palm=(0, 0, -1))),   # gauntlet to chest
        (61.62, make_pose(torso=(0, 2), head=(-8, 0), stance=0.28,
                          R_up=(0.15, -0.1, -0.98), R_lo=(0.1, 0.1, -0.99), R_palm=(0, -1, 0),
                          L_up=(0.2, -0.1, -0.98), L_lo=(0.1, 0.1, -0.99), L_palm=(0, 0, -1))),   # bracing
        (61.70, make_pose(torso=(4, -8), head=(-6, 0), stance=0.3,
                          R_up=(0.2, -0.7, 0.6), R_lo=(0.1, -0.8, 0.5), R_palm=(0, -1, 0),
                          L_up=(0.1, -0.05, -0.99), L_lo=(0.05, 0.05, -1.0), L_palm=(0, 0, -1))), # blast recoil
        (62.20, make_pose(torso=(2, -2), head=(-8, 0), stance=0.26, **REL_R,
                          L_up=(-0.1, -0.6, -0.8), L_lo=(-0.1, -0.8, -0.5), L_palm=(0, -1, 0))),
        (63.40, make_pose(torso=(0, 2), head=(-6, 0), stance=0.24, **REL_R, **REL_L)),
        (63.75, make_pose(torso=(0, 2), head=(-6, 0), stance=0.24, **REL_R, **REL_L)),              # standing, talking (reference 63.4-64.7: close-up, no walk)
        (64.10, make_pose(torso=(-2, 3), head=(-10, -4), stance=0.24, **REL_R, **REL_L)),           # head moves as he speaks
        (64.45, make_pose(torso=(0, 2), head=(-6, 0), stance=0.24, **REL_R, **REL_L)),
        (64.74, make_pose(torso=(-2, 3), head=(-10, -4), stance=0.24, **REL_R, **REL_L)),
        (65.10, TH_WALK_R),
        (65.53, TH_BLOCK_WALK_L),
        (65.85, TH_BLOCK_WALK_R),
        (66.15, TH_BLOCK_WALK_L),
        (66.45, TH_BLOCK_WALK_R),
        (67.00, TH_WALK_L),
        (67.45, TH_WALK_R),
        (67.783, TH_WALK_L),
        (68.20, TH_WALK_R),
        (68.60, TH_WALK_L),
        (69.00, TH_WALK_R),
        (69.40, TH_WALK_L),
        (69.80, TH_WALK_R),
        (70.20, TH_WALK_L),
        (70.60, TH_WALK_R),
        (71.00, TH_WALK_L),
        (71.40, TH_WALK_R),
        (71.662, TH_BLOCK_WALK_L),
        (72.00, TH_BLOCK_WALK_R),
        (72.40, TH_BLOCK_WALK_L),
        (72.871, TH_BLOCK_WALK_R),
    ]
    FIST_FWD = dict(R_up=(0.3, -0.4, -0.85), R_lo=(0.05, -0.2, -0.98), R_palm=(-1, 0, 0),
                    L_up=(-0.3, -0.4, -0.85), L_lo=(-0.05, -0.2, -0.98), L_palm=(1, 0, 0))
    TH_POSES += [
        (73.00, TH_BLOCK_WALK_L),
        (73.30, make_pose(torso=(-2, 8), head=(-6, 0), stance=0.26, **FIST_FWD)),                 # fists on the beams
        (73.60, make_pose(torso=(8, -6), head=(-6, 4), stance=0.26,
                          L_up=(-0.45, 0.45, -0.75), L_lo=(-0.1, 0.75, -0.65), L_palm=(0, 0, -1), **REL_R)), # wind up left gauntlet
        (73.75, make_pose(torso=(-4, 18), head=(-6, 0), stance=0.26,
                          L_up=(0.1, 0.1, -0.99), L_lo=(0, 0.05, -1), L_palm=(0, 0, -1), **REL_R)), # punch 1 lands
        (74.37, make_pose(torso=(6, 12), head=(-6, 0), stance=0.26,
                          R_up=(0.6, -0.3, -0.7), R_lo=(0.3, 0.1, -0.95), R_palm=(-1, 0, 0), **REL_L)), # punch 2 swing
        (74.79, make_pose(torso=(-4, 12), head=(-15, 0), stance=0.28,
                          L_up=(0.2, 0.8, 0.55), L_lo=(0.1, 0.95, 0.3), L_palm=(0, 0, -1), **REL_R)), # gauntlet high
        (75.00, make_pose(torso=(6, 26), head=(-12, 0), stance=0.28,
                          L_up=(0.1, -0.5, -0.86), L_lo=(0, -0.8, -0.6), L_palm=(0, 0, -1), **REL_R)), # hammer down
        (75.30, make_pose(torso=(6, 26), head=(-12, 0), stance=0.28,
                          L_up=(0.1, -0.5, -0.86), L_lo=(0, -0.8, -0.6), L_palm=(0, 0, -1), **REL_R)),
        (75.95, make_pose(torso=(4, 24), head=(-12, 0), stance=0.28,
                          L_up=(0.1, -0.5, -0.86), L_lo=(0, -0.8, -0.6), L_palm=(0, 0, -1), **REL_R)), # press
        (76.50, make_pose(torso=(4, 20), head=(-12, 0), stance=0.28,
                          L_up=(0.1, -0.5, -0.86), L_lo=(0, -0.8, -0.6), L_palm=(0, 0, -1), **REL_R)),
        (77.42, make_pose(torso=(4, 20), head=(-14, 0), stance=0.28,
                          L_up=(0.1, -0.5, -0.86), L_lo=(0, -0.8, -0.6), L_palm=(0, 0, -1), **REL_R)),
        (79.21, make_pose(torso=(-2, 16), head=(-10, 0), stance=0.26, R_up=(0.4, 0.3, -0.86), R_lo=(0.1, 0.3, -0.95), R_palm=(-1, 0, 0), **REL_L)),
        (79.88, make_pose(torso=(-4, 14), head=(-10, 0), stance=0.26, R_up=(0.3, 0.1, -0.95), R_lo=(0.1, 0.2, -0.97), R_palm=(-1, 0, 0), **REL_L)),
        (80.55, make_pose(torso=(4, 12), head=(-8, 0), stance=0.26, R_up=(0.6, 0.1, -0.8), R_lo=(0.4, 0.2, -0.9), R_palm=(-1, 0, 0),
                          L_up=(-0.3, -0.4, -0.85), L_lo=(-0.05, -0.2, -0.98), L_palm=(0, -1, 0))),
        (81.05, make_pose(torso=(2, 20), head=(-10, 0), stance=0.26, R_up=(0.4, 0.3, -0.86), R_lo=(0.1, 0.3, -0.95), R_palm=(-1, 0, 0),
                          L_up=(-0.3, 0.5, -0.8), L_lo=(-0.1, 0.8, -0.6), L_palm=(0, -1, 0))),
        (82.60, make_pose(torso=(2, 22), head=(-10, 0), stance=0.26, R_up=(0.4, 0.3, -0.86), R_lo=(0.1, 0.3, -0.95), R_palm=(-1, 0, 0),
                          L_up=(-0.3, 0.5, -0.8), L_lo=(-0.1, 0.8, -0.6), L_palm=(0, -1, 0))),
    ]
    TH_YAW = [(35.4, 0), (35.9, 55), (41.09, 55), (41.6, 60), (45.8, 60), (52.9, 60)]
    TH_STEP = [(35.9, 0), (36.8, -2.2), (42.6, -2.2), (43.30, -1.6), (45.8, -1.6)]   # a step back; lurches in when pinned
    TH_DROP = [(42.9, 0), (43.30, -0.8), (45.8, -0.8), (53.2, -0.8), (53.8, 0), (55.0, 0), (55.40, -0.66), (56.8, -0.66),
               (57.33, -0.85), (57.9, -0.66), (58.35, -0.85), (58.60, -0.66), (58.85, -0.88), (59.15, -0.66), (59.45, -0.85),
               (59.9, -0.7), (60.55, -0.8), (61.0, 0), (63.4, 0), (67.783, 0), (72.871, 0)]
    TH_BACK = [(25.70, 0), (25.95, 0.8), (28.33, 0.8), (28.75, 5.5), (29.1, 8.5), (29.5, 9.0), (29.85, 6.0), (30.95, 2.3), (31.12, 1.7), (31.9, 1.85), (32.06, 1.5)]   # pushed back (rig studs)

    # contacts: Thanos' hand is solved onto the exact spot on Iron Man at that moment (two-bone IK),
    # so every hit and grab connects. (time, side, Iron Man part, offset in world studs, pole, palm)
    # (offsets include ~0.35 studs for the user's Iron Man model standing taller than the reference rig)
    CONTACTS = [(29.95, "Right", "Head", (0.35, 0.35, 0), (0, -1, 0.4), (0, -1, 0)),          # the hook lands on his left cheek
                (30.15, "Right", "Head", (0, 0.85, 0.1), (1, 0.3, 0.5), (0, -1, 0.2)),        # hand closes over the helmet
                (30.45, "Right", "Head", (0, 0.78, 0.1), (1, 0.3, 0.5), (0, -1, 0.2)),
                (31.12, "Left", "UpperTorso", (-0.85, 0.65, 0.25), (-1, -0.5, 0), (0.3, -0.9, 0)),   # gauntlet grips his shoulder
                (31.36, "Left", "UpperTorso", (-0.85, 0.65, 0.25), (-1, -0.5, 0), (0.3, -0.9, 0)),
                (31.50, "Left", "UpperTorso", (-0.85, 0.65, 0.25), (-1, -0.5, 0), (0.3, -0.9, 0)),
                (31.50, "Right", "Head", (0.3, 0.3, 0.35), (1, -1, 0), (0, -1, 0)),             # the punch to the face
                (32.06, "Right", "UpperTorso", (0, 0.75, -0.2), (1, 0.2, -0.5), (-1, 0, 0))]  # the hammer blow
    CONTACTS += [(81.05, "Left", "UpperTorso", (0.2, 0.4, 0), (0, 1, 0.3), (0, -1, 0)),   # the stab
                 (82.60, "Left", "UpperTorso", (0.2, 0.4, 0), (0, 1, 0.3), (0, -1, 0))]
    # 81.05-82.60: Tony is lifted on the blade (1.2 studs up); the contacts below are solved on that lift
    _h = chan(80.90, IM_H)
    IM_H += [(81.05, _h), (81.45, _h + 1.2), (82.60, _h + 1.2)]
    # 32.00-32.20: Thanos's left hand catches Iron Man's leg and holds it while he is thrown (reference 32.05-32.15),
    # then lets go over 32.20-32.45 s instead of snapping off. Keys are copies of the poses around them.
    def _copy_key(t_src, t_new):
        src = next(p for t_, p in TH_POSES if abs(t_ - t_src) < 1e-6)
        return (t_new, {k_: v_.copy() for k_, v_ in src.items()})
    TH_POSES += [_copy_key(32.06, 32.02), _copy_key(32.06, 32.10), _copy_key(32.06, 32.18),
                 _copy_key(32.60, 32.30), _copy_key(32.60, 32.42)]
    TH_POSES.sort(key=lambda kp_: kp_[0])
    CONTACTS += [(32.02, "Left", "LowerTorso", (-0.6, -0.4, 0.2), (0, -1, 0.4), (0, 0, 1)),
                 (32.10, "Left", "LowerTorso", (-0.6, -0.4, 0.2), (0, -1, 0.4), (0, 0, 1)),
                 (32.18, "Left", "LowerTorso", (-0.6, -0.4, 0.2), (0, -1, 0.4), (0, 0, 1))]
    # stab thrust (reference 80.75-81.0): left arm straight forward into Iron Man's belly, held through 81.05
    STAB_L = dict(L_up=(-0.15, 0.05, -0.99), L_lo=(0.0, 0.0, -1.0), L_palm=(0, -1, 0))
    TH_POSES += [(80.80, make_pose(torso=(2, 22), head=(-10, 0), stance=0.26, R_up=(0.4, 0.3, -0.86), R_lo=(0.1, 0.3, -0.95), R_palm=(-1, 0, 0), **STAB_L)),
                 (80.95, make_pose(torso=(2, 24), head=(-10, 0), stance=0.26, R_up=(0.4, 0.3, -0.86), R_lo=(0.1, 0.3, -0.95), R_palm=(-1, 0, 0), **STAB_L))]
    TH_POSES.sort(key=lambda kp_: kp_[0])
    CONTACTS += [(80.80, "Left", "LowerTorso", (0.1, 0.3, 0.2), (0, 1, 0.3), (0, -1, 0)),   # the thrust reaches his belly
                 (80.95, "Left", "LowerTorso", (0.1, 0.3, 0.2), (0, 1, 0.3), (0, -1, 0))]
    keyed_at = {tk: k for k, (tk, _) in enumerate(TH_POSES)}

    def keyed_at_th(tk):
        return next(k for k, (t_, _) in enumerate(TH_POSES) if abs(t_ - tk) < 1e-6)
    for tc, side, part, off, pole, palm in CONTACTS:
        k = keyed_at[tc]
        target = world_point("IronMan", im_fight(tc), part) + np.asarray(off, float)
        base = moved(TH_POSES[k][1], -chan(tc, TH_BACK))
        solved, short = reach(base, "Thanos", side, target, pole, palm)
        solved["LowerTorso"] = TH_POSES[k][1]["LowerTorso"].copy()               # keep the key un-moved
        TH_POSES[k] = (tc, solved)
        if short > 0.05:
            print(f"  contact {tc} {side} -> IronMan.{part}: {short:.2f} studs short")

    TH_WX, TH_WZ = [(0, 0)], [(0, 0)]                                   # extra world offset (Thanos rig: x, -z; scale 1.35)

    # clearance: his kneeling leg must not pass through Iron Man's arm during the punches (56.8-59.2)
    TH_CLEAR = [(56.80, 0), (57.20, -2.2), (58.90, -2.2), (59.20, 0)]

    def th_fight(t):
        step = chan(t, TH_STEP)
        sc = RIGS["Thanos"]["scale"]
        return moved(at_keys(t, TH_POSES), -chan(t, TH_BACK) + 0.57 * step - chan(t, TH_WZ) / sc, chan(t, TH_DROP), 0,
                     -0.82 * step + (chan(t, TH_WX) + chan(t, TH_CLEAR)) / sc, chan(t, TH_YAW))

    # the beam: his gauntlet arm points straight at Iron Man's shield (his left hand) at every aim key
    for tk in (36.60, 37.00, 38.55, 41.09):
        k = keyed_at_th(tk)
        target = world_point("IronMan", im_fight(tk), "LeftHand")
        W, P = fk(stack([th_fight(tk)]), 0)
        shoulder = world_point("Thanos", th_fight(tk), "LeftUpperArm", tuple(PIVOT["LeftUpperArm"]))
        d = target - shoulder
        d = R.from_euler("y", -chan(tk, TH_YAW), degrees=True).apply(d / np.linalg.norm(d))   # into the un-turned pose
        q = {p_: m.copy() for p_, m in TH_POSES[k][1].items()}
        for part in ("LeftUpperArm", "LeftLowerArm"):
            orient(q, part, d)
        orient(q, "LeftHand", d + np.array([0, 0.5, 0]), d)          # wrist bent back, palm toward him
        TH_POSES[k] = (tk, q)

    # 43.30-45.36: his gauntlet pinned flat on the ground, Iron Man standing on it
    # the pin spot: straight down-forward from his left shoulder, at full reach, on the ground
    sh = world_point("Thanos", th_fight(44.10), "LeftUpperArm", tuple(PIVOT["LeftUpperArm"]))
    fwd = np.array([-np.sin(np.radians(60)), 0, -np.cos(np.radians(60))])
    drop = sh[1] - (STAGE_Y + 0.45)
    run = np.sqrt(max((0.80 * (ARM_UP + ARM_LO) * RIGS["Thanos"]["scale"]) ** 2 - drop ** 2, 0.25))
    PIN_AT = np.array([sh[0], STAGE_Y + 0.45, sh[2]]) + fwd * run
    # Iron Man lands on it: his world x/z from 42.95 on (rig: x = -world_x, d = world_z + 40)
    IM_X[-2:] = [(42.95, -PIN_AT[0] - 7.71), (45.8, -PIN_AT[0] - 7.71)]
    IM_D2[-2:] = [(42.95, PIN_AT[2] + 40 - 36.6 + 5.36 - 0.6), (45.8, PIN_AT[2] + 40 - 36.6 + 5.36 - 0.6)]
    # standing ON the hand from the landing; 45.05 -> 45.39 he steps off it into the blow so his hips
    # end 1.7 studs from Thanos' face, turned to face it (yaw from the real direction)
    x0, d0 = IM_X[-1][1], IM_D2[-1][1]
    IM_H[-1:] = [(42.80, 1.2), (43.15, 1.15), (43.35, 0.8), (45.05, 0.8), (45.39, 0.15), (45.8, 0.15)]
    head = world_point("Thanos", th_fight(45.36), "Head")
    here = np.array([-(x0 + 7.71), 0, -40 + 36.6 - 5.36 + d0])           # his world x/z on the hand (rig -> world)
    v = here - head; v[1] = 0; v /= np.linalg.norm(v)
    goal = head + v * 1.7
    gx, gd = -goal[0] - 7.71, goal[2] + 40 - 36.6 + 5.36
    IM_X[-2:] = [(42.80, -3.2), (43.15, -5.0), (43.35, x0), (45.05, x0), (45.39, gx), (45.8, gx)]
    IM_D2[-2:] = [(42.80, 7.5), (43.15, 9.4), (43.35, d0), (45.05, d0), (45.39, gd), (45.8, gd)]
    face_yaw = np.degrees(np.arctan2(-v[0], -v[2])) % 360
    IM_YAW[-5:] = [(44.10, 62), (44.60, face_yaw - 180), (45.05, face_yaw - 165), (45.39, face_yaw + 360), (45.8, face_yaw + 364)]
    IM_PITCH[-1:] = [(45.05, 360), (45.39, 348), (45.8, 350)]
    for tk in (43.35, 44.10, 45.36, 45.80, 46.60, 47.30, 47.70, 48.55, 48.85, 49.55, 50.30, 51.60, 52.90):
        k = keyed_at_th(tk)
        target = PIN_AT + (0)
        solved, short = reach(th_fight(tk), "Thanos", "Left", target, (0, 1, 0.3), (0, -1, 0))
        solved["LowerTorso"] = TH_POSES[k][1]["LowerTorso"].copy()
        TH_POSES[k] = (tk, solved)
        if short > 0.05:
            print(f"  pin {tk}: {short:.2f} studs short")

    # 46.0-47.0: he backs off to 4.2 studs in front of Thanos for the face-off (52.27), facing him
    th_front = np.array([-np.sin(np.radians(60)), 0, -np.cos(np.radians(60))])
    off_goal = head + th_front * 4.2
    fx_, fd_ = -off_goal[0] - 7.71, off_goal[2] + 40 - 36.6 + 5.36
    IM_X += [(46.0, gx), (47.0, fx_), (52.70, fx_), (52.768, fx_ + 1.2), (52.95, fx_ + 1.2), (52.96, fx_)]
    IM_D2 += [(46.0, gd), (47.0, fd_), (52.70, fd_), (52.768, fd_ + 0.6), (52.95, fd_ + 0.6), (52.96, fd_)]
    off_yaw = np.degrees(np.arctan2(-th_front[0], -th_front[2]))
    last = IM_YAW[-1][1]
    off_yaw += 360 * round((last - off_yaw) / 360)
    IM_YAW += [(46.0, last), (47.0, off_yaw), (52.70, off_yaw)]
    IM_PITCH += [(46.4, 360), (52.70, 360)]
    IM_H += [(46.4, 0.0), (52.70, 0.0), (52.768, -2.7), (52.95, -2.7), (53.30, 5.2), (53.60, 4.0), (54.02, -0.25), (55.30, -0.25), (55.521, -0.85), (56.13, -0.85), (56.605, -0.9), (60.55, -0.9)]

    # 52.95-54.02: swept off his feet, he flips back over (pitch +450 = onto his back) and is thrown
    # 7 studs along Thanos' front, landing at 54.02, sliding to a stop by 54.5
    IM_PITCH += [(52.70, 360), (52.95, 360), (53.20, 435), (53.50, 450), (53.80, 450), (54.02, 450), (60.55, 450), (61.00, 360), (61.65, 360),
                 (61.80, 385), (62.28, 450), (63.40, 450), (64.74, 450), (64.95, 410), (65.20, 360), (67.783, 360), (72.871, 360)]
    throw = [(52.95, 0.0), (54.02, 7.0), (54.50, 8.4), (60.55, 8.4)]
    IM_WX += [(t_, th_front[0] * d_) for t_, d_ in throw]
    IM_WZ += [(t_, th_front[2] * d_) for t_, d_ in throw]
    # Thanos follows: from 54.69 he strides in to stand over him (hips 2.4 studs short, toward himself)
    lying_hips = world_point("IronMan", im_fight(55.0), "LowerTorso")
    th_hips0 = world_point("Thanos", th_fight(54.6), "LowerTorso")
    th_right = np.array([np.cos(np.radians(60)), 0, -np.sin(np.radians(60))])
    goal_th = lying_hips + th_front * 1.2 - th_right * 1.3               # knelt at his left side, level with his chest
    dwx, dwz = goal_th[0] - th_hips0[0], goal_th[2] - th_hips0[2]
    lunge = 0.9                                                          # 53.00: lunges into the sweep
    recoil_x, recoil_z = dwx - th_front[0] * 0.5, dwz - th_front[2] * 0.5
    TH_WX += [(52.70, 0), (52.768, th_front[0] * 0.4), (52.90, th_front[0] * 0.6), (53.00, th_front[0] * lunge), (53.60, 0), (54.60, 0), (54.69, dwx * 0.55), (55.40, dwx), (61.62, dwx), (61.75, recoil_x), (63.40, recoil_x),
              (64.74, recoil_x + th_front[0] * 2.2), (65.53, recoil_x + th_front[0] * 3.6),
              (66.365, recoil_x + th_front[0] * 5.2), (67.783, recoil_x + th_front[0] * 7.5),
              (68.534, recoil_x + th_front[0] * 8.4), (70.536, recoil_x + th_front[0] * 10.6),
              (71.662, recoil_x + th_front[0] * 11.8), (72.871, recoil_x + th_front[0] * 13.0),
              (73.30, recoil_x + th_front[0] * 14.6), (73.60, recoil_x + th_front[0] * 15.5),
              (73.75, recoil_x + th_front[0] * 16.2), (74.37, recoil_x + th_front[0] * 16.4),
              (75.00, recoil_x + th_front[0] * 16.5), (78.00, recoil_x + th_front[0] * 16.5)]
    TH_WZ += [(52.70, 0), (52.768, th_front[2] * 0.4), (52.90, th_front[2] * 0.6), (53.00, th_front[2] * lunge), (53.60, 0), (54.60, 0), (54.69, dwz * 0.55), (55.40, dwz), (61.62, dwz), (61.75, recoil_z), (63.40, recoil_z),
              (64.74, recoil_z + th_front[2] * 2.2), (65.53, recoil_z + th_front[2] * 3.6),
              (66.365, recoil_z + th_front[2] * 5.2), (67.783, recoil_z + th_front[2] * 7.5),
              (68.534, recoil_z + th_front[2] * 8.4), (70.536, recoil_z + th_front[2] * 10.6),
              (71.662, recoil_z + th_front[2] * 11.8), (72.871, recoil_z + th_front[2] * 13.0),
              (73.30, recoil_z + th_front[2] * 14.6), (73.60, recoil_z + th_front[2] * 15.5),
              (73.75, recoil_z + th_front[2] * 16.2), (74.37, recoil_z + th_front[2] * 16.4),
              (75.00, recoil_z + th_front[2] * 16.5), (78.00, recoil_z + th_front[2] * 16.5)]
    print(f"  lying at {np.round(lying_hips, 2)}, Thanos steps {dwx:.1f},{dwz:.1f}")

    # 60.55-61.15: Thanos stands up lifting Iron Man off the ground.
    # Solve IM_H and IM_WX/IM_WZ so his UpperTorso sits 0.3 studs below Thanos' RightHand in front of Thanos (th_hips + th_front * 1.5)
    th_hips_61 = world_point("Thanos", th_fight(61.00), "LowerTorso")
    th_hand_61 = world_point("Thanos", th_fight(61.00), "RightHand")
    target_ut = np.array([th_hips_61[0] + th_front[0] * 1.5, th_hand_61[1] - 0.3, th_hips_61[2] + th_front[2] * 1.5])
    cur_ut = world_point("IronMan", im_fight(61.00), "UpperTorso")
    lift_wx = IM_WX[-1][1] + (target_ut[0] - cur_ut[0])
    lift_wz = IM_WZ[-1][1] + (target_ut[2] - cur_ut[2])
    lift_h = IM_H[-1][1] + (target_ut[1] - cur_ut[1])

    IM_H += [(61.00, lift_h), (61.65, lift_h), (61.95, lift_h + 2.5), (62.28, -0.9), (62.42, -0.3), (62.60, -0.9), (63.40, -0.9),
             (64.74, -0.9), (64.95, -0.65), (65.20, -0.35), (67.783, -0.35), (72.871, -0.35), (78.00, -0.35)]
    blast_d = [(61.65, 0.0), (61.95, 9.0), (62.28, 16.0), (62.60, 18.5), (63.40, 18.5)]
    blast_end_wx = lift_wx + th_front[0] * 18.5
    blast_end_wz = lift_wz + th_front[2] * 18.5
    IM_WX += [(61.00, lift_wx)] + [(t_, lift_wx + th_front[0] * d_) for t_, d_ in blast_d] + [(67.783, blast_end_wx), (72.871, blast_end_wx), (78.00, blast_end_wx)]
    IM_WZ += [(61.00, lift_wz)] + [(t_, lift_wz + th_front[2] * d_) for t_, d_ in blast_d] + [(67.783, blast_end_wz), (72.871, blast_end_wz), (78.00, blast_end_wz)]

    # 47.70-48.55: his right fingertips touch his brow where the blow landed (IK onto his own head)
    for tk in (47.70, 48.55):
        k = keyed_at_th(tk)
        brow = world_point("Thanos", th_fight(tk), "Head") + th_front * 0.55 + np.array([0, 0.25, 0]) \
            + np.array([np.cos(np.radians(60)), 0, -np.sin(np.radians(60))]) * -0.3
        solved, short = reach(th_fight(tk), "Thanos", "Right", brow, (1, -1, 0), (-0.5, 0, -0.85))
        solved["LowerTorso"] = TH_POSES[k][1]["LowerTorso"].copy()
        TH_POSES[k] = (tk, solved)
        if short > 0.05:
            print(f"  brow touch {tk}: {short:.2f} studs short")

    # 53.00: his right hand sweeps Iron Man's shins; hammer-punches land; collar grab; lift
    for tk, target_part, off, pole, palm in ((53.00, "LeftUpperLeg", (0, 0.2, 0), (1, 0, 0.5), (-1, 0, 0)),
                                             (56.15, "LeftLowerArm", (0, 0.3, 0), (1, 0, 0.5), (-1, 0, 0)),
                                             (57.33, "UpperTorso", (0, 0.3, 0), (1, 0, 0.5), (-1, 0, 0)),
                                             (58.35, "Head", (0, 0.3, 0), (1, 0, 0.5), (-1, 0, 0)),
                                             (58.85, "Head", (0, 0.35, 0), (1, 0, 0.5), (-1, 0, 0)),
                                             (59.45, "Head", (0.3, 0.2, 0), (1, 0, 0.5), (-1, 0, 0)),
                                             (60.55, "UpperTorso", (0, 0.45, -0.2), (1, 0, 0.5), (0, -1, 0)),
                                             (61.00, "UpperTorso", (0, 0.45, -0.2), (1, 0, 0.5), (0, -1, 0)),
                                             (61.45, "UpperTorso", (0, 0.45, -0.2), (1, 0, 0.5), (0, -1, 0)),
                                             (61.62, "UpperTorso", (0, 0.45, -0.2), (1, 0, 0.5), (0, -1, 0))):
        k = keyed_at_th(tk)
        target = world_point("IronMan", im_fight(tk), target_part) + np.asarray(off, float)
        solved, short = reach(th_fight(tk), "Thanos", "Right", target, pole, palm)
        solved["LowerTorso"] = TH_POSES[k][1]["LowerTorso"].copy()
        TH_POSES[k] = (tk, solved)
        if short > 0.05:
            print(f"  hit {tk} -> IronMan.{target_part}: {short:.2f} studs short")

    # Left-hand (gauntlet) pressed onto IronMan.UpperTorso at 61.45 and 61.62
    for tk in (61.45, 61.62):
        k = keyed_at_th(tk)
        target = world_point("IronMan", im_fight(tk), "UpperTorso") + np.array([0, 0.1, -0.35])
        solved, short = reach(th_fight(tk), "Thanos", "Left", target, (-1, 0, 0.5), (0, 0, -1))
        solved["LowerTorso"] = TH_POSES[k][1]["LowerTorso"].copy()
        TH_POSES[k] = (tk, solved)
        if short > 0.05:
            print(f"  gauntlet {tk} -> IronMan.UpperTorso: {short:.2f} studs short")

    # Iron Man hands gripping Thanos' RightLowerArm at 61.00, 61.30, 61.60
    for tk in (61.00, 61.30, 61.60):
        k = next(i for i, (t_, _) in enumerate(IM_POSES) if abs(t_ - tk) < 1e-6)
        arm_tgt = world_point("Thanos", th_fight(tk), "RightLowerArm")
        solved = {p: m.copy() for p, m in IM_POSES[k][1].items()}
        for side, off in (("Left", (-0.08, 0, 0.05)), ("Right", (0.08, 0, 0.05))):
            target = arm_tgt + np.array(off)
            s_pose, short = reach(im_fight(tk), "IronMan", side, target, (0, -1, 0), (0, 0, -1))
            for p in (f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand"):
                solved[p] = s_pose[p].copy()
            if short > 0.05:
                print(f"  im grip {tk} {side}: {short:.2f} studs short")
        solved["LowerTorso"] = IM_POSES[k][1]["LowerTorso"].copy()
        IM_POSES[k] = (tk, solved)

    # 45.39: Iron Man's spinning right fist lands on Thanos' face (IK onto his head)
    k = next(i for i, (t_, _) in enumerate(IM_POSES) if abs(t_ - 45.39) < 1e-6)
    face = world_point("Thanos", th_fight(45.36), "Head") + np.array([0.0, -0.1, 0.0])
    solved, short = reach(im_fight(45.39), "IronMan", "Right", face, (1, -0.5, 0), (0, 0, -1))
    solved["LowerTorso"] = IM_POSES[k][1]["LowerTorso"].copy()
    IM_POSES[k] = (45.39, solved)
    if short > 0.05:
        print(f"  punch: {short:.2f} studs short")

    # 65.53-66.15: Thanos raises gauntlet to block incoming repulsor beam; Iron Man aims right hand at gauntlet
    for tk in (65.53, 65.85, 66.15):
        k_th = keyed_at_th(tk)
        th_ut = world_point("Thanos", th_fight(tk), "UpperTorso")
        block_tgt = th_ut + th_front * 1.1 + np.array([0, 0.45, 0]) - th_right * 0.15
        solved_th, short_th = reach(th_fight(tk), "Thanos", "Left", block_tgt, (-1, 0.5, 0.5), (0, 0, -1))
        solved_th["LowerTorso"] = TH_POSES[k_th][1]["LowerTorso"].copy()
        TH_POSES[k_th] = (tk, solved_th)
        if short_th > 0.05:
            print(f"  block {tk} Thanos.LeftHand: {short_th:.2f} studs short")

        k_im = next(i for i, (t_, _) in enumerate(IM_POSES) if abs(t_ - tk) < 1e-4)
        solved_im = {p: m.copy() for p, m in IM_POSES[k_im][1].items()}
        orient(solved_im, "RightUpperArm", (0.05, 0.1, -0.99))
        orient(solved_im, "RightLowerArm", (0.02, 0.05, -1.0))
        orient(solved_im, "RightHand", (0.0, 0.0, -1.0), (0, 1, 0))
        IM_POSES[k_im] = (tk, solved_im)

    # 71.662-72.871: Thanos raises gauntlet to block incoming dual fire-lasers; Iron Man aims both hands
    for tk in (71.662, 72.00, 72.40, 72.871):
        k_th = keyed_at_th(tk)
        th_ut = world_point("Thanos", th_fight(tk), "UpperTorso")
        block_tgt = th_ut + th_front * 1.1 + np.array([0, 0.40, 0]) - th_right * 0.1
        solved_th, short_th = reach(th_fight(tk), "Thanos", "Left", block_tgt, (-1, 0.5, 0.5), (0, 0, -1))
        solved_th["LowerTorso"] = TH_POSES[k_th][1]["LowerTorso"].copy()
        TH_POSES[k_th] = (tk, solved_th)
        if short_th > 0.05:
            print(f"  block {tk} Thanos.LeftHand: {short_th:.2f} studs short")

        k_im = next(i for i, (t_, _) in enumerate(IM_POSES) if abs(t_ - tk) < 1e-4)
        solved_im = {p: m.copy() for p, m in IM_POSES[k_im][1].items()}
        orient(solved_im, "RightUpperArm", (0.05, 0.1, -0.99))
        orient(solved_im, "RightLowerArm", (0.02, 0.05, -1.0))
        orient(solved_im, "RightHand", (0.0, 0.0, -1.0), (0, 1, 0))
        orient(solved_im, "LeftUpperArm", (-0.05, 0.1, -0.99))
        orient(solved_im, "LeftLowerArm", (-0.02, 0.05, -1.0))
        orient(solved_im, "LeftHand", (0.0, 0.0, -1.0), (0, 1, 0))
        IM_POSES[k_im] = (tk, solved_im)

    # 73.30-76.50: Thanos contacts solved with th_fight(tk)
    for tk, side, target_part, off, pole, palm in (
        (73.30, "Left", "LeftHand", (-0.8, 0, 0), (1, 0, 0.5), (-1, 0, 0)),
        (73.30, "Right", "RightHand", (0.8, 0, 0), (1, 0, 0.5), (-1, 0, 0)),
        (73.75, "Left", "Head", (-0.1, 0.3, 0.2), (-1, 0.5, 0.5), (0, 0, -1)),
        (75.00, "Left", "LeftLowerArm", (0, 0.35, -0.1), (-1, 0.5, 0.5), (0, 0, -1)),
        (75.30, "Left", "LeftLowerArm", (0, 0.35, -0.1), (-1, 0.5, 0.5), (0, 0, -1)),
        (75.95, "Left", "LeftLowerArm", (0, 0.35, -0.1), (-1, 0.5, 0.5), (0, 0, -1)),
        (76.50, "Left", "LeftLowerArm", (0, 0.35, -0.1), (-1, 0.5, 0.5), (0, 0, -1)),
    ):
        k_th = keyed_at_th(tk)
        target = world_point("IronMan", im_fight(tk), target_part) + np.asarray(off, float)
        solved, short = reach(th_fight(tk), "Thanos", side, target, pole, palm)
        solved["LowerTorso"] = TH_POSES[k_th][1]["LowerTorso"].copy()
        TH_POSES[k_th] = (tk, solved)
        if short > 0.05:
            print(f"  contact {tk} {side} -> IronMan.{target_part}: {short:.2f} studs short")

    # impacts (movie time, rig, part, push direction in rig space, degrees): the physics layer on top
    FIGHT_HITS = [(25.70, "thanos", "UpperTorso", (0, 0.25, 1), 9),        # the two-footed kick
                  (28.33, "thanos", "UpperTorso", (0, 0.1, 1), 12),        # the cannon slam
                  (28.33, "thanos", "LeftHand", (0, 0, 1), 16), (28.33, "thanos", "RightHand", (0, 0, 1), 16),
                  (28.33, "ironman", "LeftHand", (0, 0, 1), 12), (28.33, "ironman", "RightHand", (0, 0, 1), 12),
                  (29.95, "ironman", "Head", (0.8, 0, 0.6), 28), (29.95, "ironman", "UpperTorso", (0.8, 0, 0.6), 8),   # the hook
                  (29.95, "thanos", "RightHand", (0.3, 0, 1), 10),
                  (30.55, "ironman", "Head", (-0.6, 0.2, 0.7), 18),                                                # helmet ripped off
                  (31.50, "ironman", "Head", (0.7, 0, 0.7), 32), (31.50, "ironman", "UpperTorso", (0.7, 0, 0.7), 10),  # the punch
                  (31.50, "thanos", "RightHand", (0, 0, 1), 10),
                  (32.04, "ironman", "UpperTorso", (0, -0.6, 0.8), 15), (32.04, "thanos", "RightHand", (0, 1, 0.2), 12),  # hammer
                  (32.45, "ironman", "UpperTorso", (0, 0, 1), 10), (32.45, "ironman", "Head", (0, 0, 1), 14),       # hits the ground
                  (34.80, "thanos", "LeftHand", (0.6, 0, 0), 10),
                  (37.00, "thanos", "LeftHand", (0.82, 0.25, 0.57), 14), (37.00, "thanos", "UpperTorso", (0.82, 0, 0.57), 5),   # beam recoil
                  (38.545, "ironman", "LeftHand", (0.82, 0.1, 0.57), 20), (38.545, "ironman", "UpperTorso", (0.82, 0, 0.57), 9),  # beam hits the shield
                  (38.545, "ironman", "Head", (0.82, 0, 0.57), 8),
                  (43.30, "thanos", "LeftHand", (0, -1, 0), 14), (43.30, "thanos", "UpperTorso", (0, -0.6, -0.8), 9),   # pinned
                  (43.30, "ironman", "UpperTorso", (0, -1, 0), 8),                                                    # landing
                  (45.39, "thanos", "Head", (0.6, 0.1, 0.8), 38), (45.39, "thanos", "UpperTorso", (0.6, 0, 0.8), 12),  # THE BLOW
                  (45.39, "ironman", "RightHand", (0, 0, 1), 14),
                  (53.00, "ironman", "LeftLowerLeg", (0.8, 0.3, 0.5), 25),                                         # swept
                  (54.02, "ironman", "UpperTorso", (0, 1, 0), 14), (54.02, "ironman", "Head", (0, 1, 0), 18),      # lands on his back
                  (56.15, "ironman", "LeftLowerArm", (0, -1, 0), 22), (56.15, "ironman", "UpperTorso", (0, -1, 0), 10),
                  (57.33, "ironman", "UpperTorso", (0, -1, 0), 16), (57.33, "ironman", "Head", (0, -1, 0), 14),
                  (58.35, "ironman", "Head", (-1, -0.15, 0), 34), (58.35, "ironman", "UpperTorso", (0, -1, 0), 8),
                  (56.15, "thanos", "RightHand", (0, 1, 0), 12), (57.33, "thanos", "RightHand", (0, 1, 0), 12),
                  (58.35, "thanos", "RightHand", (0, 1, 0), 14),
                  # 425-440: punch 4, punch 5, collar grab lift, Power Stone blast, and crash
                  (58.85, "ironman", "Head", (0, -1, 0), 30), (58.85, "ironman", "UpperTorso", (0, -1, 0), 8),
                  (58.85, "thanos", "RightHand", (0, 1, 0), 12),
                  (59.45, "ironman", "Head", (1, -0.15, 0), 36), (59.45, "ironman", "UpperTorso", (1, 0, 0), 8),
                  (59.45, "thanos", "RightHand", (0, 0, 1), 14),
                  (60.55, "ironman", "UpperTorso", (0, 1, 0), 10), (60.55, "ironman", "Head", (0, 1, 0), 12),
                  (61.65, "ironman", "UpperTorso", (0, 0.1, 1), 30), (61.65, "ironman", "Head", (0, 0, 1), 34),
                  (61.65, "ironman", "LeftUpperLeg", (0, 0, -1), 20), (61.65, "ironman", "RightUpperLeg", (0, 0, -1), 20),
                  (61.65, "thanos", "LeftHand", (0, 0, 1), 16), (61.65, "thanos", "UpperTorso", (0, 0, 1), 6),
                  (62.28, "ironman", "UpperTorso", (0, 1, 0), 18), (62.28, "ironman", "Head", (0, 1, 0), 22),
                  (62.42, "ironman", "UpperTorso", (0, 1, 0), 8),
                  # 445-460: repulsor recoil and beam deflection impact
                  (65.35, "ironman", "RightHand", (0, 0, 1), 16), (65.35, "ironman", "UpperTorso", (0, 0, 1), 6),
                  (65.55, "thanos", "LeftHand", (0, 0, 1), 14), (65.55, "thanos", "UpperTorso", (0, 0, 1), 5),
                  # 465-480: dual fire-laser recoil and gauntlet impact
                  (67.85, "ironman", "RightHand", (0, 0, 1), 14), (67.85, "ironman", "UpperTorso", (0, 0, 1), 6),
                  (68.20, "ironman", "LeftHand", (0, 0, 1), 14), (68.20, "ironman", "UpperTorso", (0, 0, 1), 6),
                  (68.80, "thanos", "UpperTorso", (0, 0, 1), 8),
                  (70.60, "ironman", "UpperTorso", (0, 0, 1), 8),
                  (71.70, "thanos", "LeftHand", (0, 0, 1), 12), (71.70, "thanos", "UpperTorso", (0, 0, 1), 5)]
    FIGHT_HITS += [(73.30, "thanos", "LeftHand", (0, 0, 1), 14), (73.30, "thanos", "RightHand", (0, 0, 1), 12),
                   (73.30, "ironman", "LeftHand", (0, 0, 1), 12), (73.30, "ironman", "RightHand", (0, 0, 1), 12),
                   (73.75, "ironman", "Head", (0.8, 0, 0.6), 28), (73.75, "ironman", "UpperTorso", (0.8, 0, 0.6), 8),
                   (73.75, "thanos", "LeftHand", (0, 0, 1), 10),
                   (75.00, "ironman", "LeftLowerArm", (0, -1, 0), 18), (75.00, "ironman", "UpperTorso", (0, -0.5, 0), 10),
                   (75.00, "thanos", "LeftHand", (0, 1, 0), 12),
                   (75.95, "ironman", "UpperTorso", (0, -1, 0), 8)]
    FIGHT_HITS += [(81.05, "ironman", "UpperTorso", (0, 0, 1), 12), (81.05, "ironman", "Head", (0, -0.2, 1), 8),
                   (81.05, "thanos", "LeftHand", (0, 0, 1), 8)]
    for shot, start, dur in FIGHT_SHOTS:
        for rig, fn in (("ironman", im_fight), ("thanos", th_fight)):
            S = slice_of(fn, start, dur)
            for t_hit, who, part, push, deg in FIGHT_HITS:
                if who == rig and -0.8 < t_hit - start < dur:
                    S = react(S, t_hit - start, part, push, deg)
            s[f"{shot}_{rig}"] = S

    # 040 (hand-animated) Iron Man drops out of the sky into 050's opening crouch.
    # Telephoto frame is only ~10 studs tall, so he must be low by movie 3.0 s: drop from 30 studs
    # braking on thrusters (decelerating), arms spread for the hand repulsors, touch down 3.12 s.
    stand, crouch = pose_of(s["050_ironman"], -1), pose_of(s["050_ironman"], 0)
    fly = aim(aim(stand, "LeftUpperArm", (-0.55, -0.8, 0.1)), "RightUpperArm", (0.55, -0.8, 0.1))
    fly = aim(aim(fly, "LeftLowerArm", (-0.6, -0.8, 0)), "RightLowerArm", (0.6, -0.8, 0))
    # Flying streak pose (horizontal flight)
    fly_streak = make_pose(torso=(0, 65), head=(50, 0),
                           L_up=(-0.25, 0.8, 0.5), L_lo=(-0.2, 0.85, 0.5),
                           R_up=(0.25, 0.8, 0.5), R_lo=(0.2, 0.85, 0.5), stance=0.04)
    y0, frames = crouch["LowerTorso"][1, 3], []
    for t in frame_times(1.167):
        if t < 0.20:                                     # streaking horizontally across upper sky (movie 2.63 -> 2.83)
            u = t / 0.20
            p = fly_streak
            y = 22.0
            x = -14.0 + u * 12.0
        elif t < 0.49:                                   # braking descent (movie 2.83 -> 3.12 s)
            u = (t - 0.20) / 0.29
            p, y, x = blend(fly, crouch, ease((u - 0.75) / 0.25)), y0 + 22.0 * (1 - u) ** 2, 0.0
        elif t < 0.55:                                   # impact: compress
            p, y, x = crouch, y0 - 0.35 * ease((t - 0.49) / 0.06), 0.0
        else:                                            # recover into the held crouch
            p, y, x = crouch, y0 - 0.35 * (1 - ease((t - 0.55) / 0.14)), 0.0
        p = {k: v.copy() for k, v in p.items()}
        p["LowerTorso"][0, 3] = x
        p["LowerTorso"][1, 3] = y
        frames.append(p)
    s["040_ironman"] = stack(frames)
    return s


# ------------------------------------------------------------------------------- timeline
# Movie timeline (frame-accurate from the reference clip). Every shot: which animation plays
# on which rig, and the camera. Camera keys are shot-local; pos/look = (target, offset) where
# target is "Rig.Part" (follows that part) and offset is in world studs.
TIMELINE = [
    dict(shot="010", start=0.000, dur=0.834, play={"Thanos": "010_thanos"},
         note="Thanos medium-wide, frontal, low angle; crops at upper thighs, raises the gauntlet",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-0.35, -0.7, -17.5)), look=('Thanos.UpperTorso', (0.0, 0.3, 0)), fov=28),
              dict(t=0.834, pos=('Thanos.HumanoidRootPart', (-0.3, -0.65, -17.2)), look=('Thanos.UpperTorso', (0.0, 0.3, 0)), fov=28)]),
    dict(shot="020", start=0.834, dur=1.418, play={"Thanos": "020_thanos"},
         note="close-up on the gauntlet; shoulder on left edge, arm extends to center, palm open with sunburst; pulled back to avoid mesh clip",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (0.8, -0.2, -4.5)), look=('Thanos.LeftHand', (0.1, 0.1, 0.0)), fov=24),
              dict(t=1.418, pos=('Thanos.UpperTorso', (0.7, -0.2, -4.2)), look=('Thanos.LeftHand', (0.1, 0.1, 0.0)), fov=24)]),
    dict(shot="030", start=2.252, dur=0.375, play={"Thanos": "030_thanos"},
         note="medium close, head to chest, slightly low; Thanos on the left third, hand on screen-right; he looks up",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-0.6, -0.8, -12.5)), look=('Thanos.UpperTorso', (1.2, 0.6, 0)), fov=29),
              dict(t=0.375, pos=('Thanos.HumanoidRootPart', (-0.55, -0.8, -12.2)), look=('Thanos.UpperTorso', (1.2, 0.6, 0)), fov=29)]),
    dict(shot="040", hide="Thanos", start=2.628, dur=1.168, play={"IronMan": "040_ironman", "Thanos": "040_thanos"},
         note="Cut 4: extreme wide aerial, looking up; the camera TRACKS Iron Man's streak across the sky, then his drop toward the battlefield (realvideo cut 4)",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -22.0)), look=('IronMan.LowerTorso', (0, 0, 0)), fov=40),
              dict(t=1.168, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -22.0)), look=('IronMan.LowerTorso', (0, 0, 0)), fov=40)]),
    dict(shot="050", start=3.795, dur=2.085, play={"IronMan": "050_ironman"},
         note="wide battlefield shot from distance (~28 studs, IM 25-30% height), dollying in to medium cowboy thigh-up stance",
         cam=[dict(t=0.000, pos=('IronMan.HumanoidRootPart', (0.8, -0.4, 18.0)), look=('IronMan.UpperTorso', (0.0, 0.2, 0)), fov=29),
              dict(t=2.085, pos=('IronMan.HumanoidRootPart', (0.1, -0.4, 9.8)), look=('IronMan.UpperTorso', (0.0, 0.2, 0)), fov=28)]),
    dict(shot="060", hud="mask", hide="Thanos", face={'dist': 2.5, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=5.881, dur=1.960, play={"IronMan": "060_ironman"},
         note="close-up, Iron Man's face square-on; fills ~65% frame height inside HUD",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.5)), look=('IronMan.Head', (0, -0.15, 0)), fov=26),
              dict(t=1.960, pos=('IronMan.Head', (0, 0.0, 2.45)), look=('IronMan.Head', (0, -0.15, 0)), fov=26)]),
    dict(shot="070", start=7.841, dur=1.335, play={"Thanos": "070_thanos"},
         note="close-up, head + armoured shoulders, head just left of centre (~45%); 'Stark'",
         cam=[dict(t=0.000, pos=('Thanos.Head', (0.05, -0.15, -5.2)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=28),
              dict(t=1.335, pos=('Thanos.Head', (0.05, -0.15, -5.0)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=28)]),
    dict(shot="080", hud="mask", hide="Thanos", face={'dist': 2.5, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=9.176, dur=1.251, play={"IronMan": "080_ironman"},
         note="a touch tighter than 060, eyes high; 'You know me'",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, -0.2, 0)), fov=30),
              dict(t=1.251, pos=('IronMan.Head', (0, 0.0, 2.55)), look=('IronMan.Head', (0, -0.2, 0)), fov=30)]),
    dict(shot="090", start=10.427, dur=5.422, play={"Thanos": "090_thanos"},
         note="close-up, head slightly left of centre, slow dolly push-in 0.8 studs through the line",
         cam=[dict(t=0.000, pos=('Thanos.Head', (0.05, -0.15, -5.2)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=28),
              dict(t=5.422, pos=('Thanos.Head', (0.05, -0.1, -4.2)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=27)]),
    dict(shot="100", hud="mask", hide="Thanos", face={'dist': 2.4, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=15.849, dur=2.252, play={"IronMan": "100_ironman"},
         note="close-up on Iron Man inside HUD, slow creep in; 'My only curse is you' -> FIGHT",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.5)), look=('IronMan.Head', (0, -0.15, 0)), fov=26),
              dict(t=2.252, pos=('IronMan.Head', (0, 0.0, 2.4)), look=('IronMan.Head', (0, -0.15, 0)), fov=26)]),
    dict(shot="110", hide="Thanos", start=18.101, dur=1.210, play={"IronMan": "110_ironman"},
         note="Cut 11: static medium close-up, low angle tilted up: face, collar and shoulder pods all in frame",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (0.3, 0.6, -3.2)), look=('IronMan.UpperTorso', (0, 1.2, 0)), fov=38),
              dict(t=1.210, pos=('IronMan.UpperTorso', (0.3, 0.6, -3.2)), look=('IronMan.UpperTorso', (0, 1.2, 0)), fov=38)]),
    dict(shot="115", start=19.311, dur=1.335, play={"IronMan": "115_ironman"},
         note="extreme wide, low, from Thanos' side; Iron Man small in the lower middle, missiles curl up into the sky",
         cam=[dict(t=0.000, pos=('IronMan.HumanoidRootPart', (3, 1.2, 25)), look=('IronMan.HumanoidRootPart', (0, 12, 0)), fov=40),   # low, gazing up at the missile arcs (cut 12)
              dict(t=1.335, pos=('IronMan.HumanoidRootPart', (3, 1.2, 24)), look=('IronMan.HumanoidRootPart', (0, 15, 0)), fov=40)]),
    dict(shot="120", start=20.646, dur=0.792, play={"Thanos": "120_thanos"},
         note="Thanos waist-up, left-center of frame; right arm tucked back behind hip; gauntlet raised in lower right foreground; missiles in upper right sky; 'Come on'",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (1.4, 0.9, -8.6)), look=('Thanos.UpperTorso', (-0.8, 0.8, 0)), fov=34),
              dict(t=0.792, pos=('Thanos.UpperTorso', (1.3, 0.9, -8.4)), look=('Thanos.UpperTorso', (-0.8, 0.8, 0)), fov=34)]),
    dict(shot="130a", start=21.438, dur=1.084, play={"Thanos": "130a_thanos"},
         note="Cut 14: top angle behind missiles, camera trails behind swarm converging on Thanos at high speed",
         cam=[dict(t=0.000, pos=("Thanos.HumanoidRootPart", (-6, 5, -12)), look=("Thanos.HumanoidRootPart", (0, 3, -2)), fov=44),
              dict(t=1.084, pos=("Thanos.HumanoidRootPart", (-5, 6, -11)), look=("Thanos.HumanoidRootPart", (0, 3, -2)), fov=44)]),
    dict(shot="130b", start=22.522, dur=2.002, play={"Thanos": "130b_thanos"},
         note="Cut 15: wide ground-level 35 deg profile shot of blast, high-explosive missile impacts detonate across Thanos guard, dust cloud",
         cam=[dict(t=0.000, pos=("Thanos.HumanoidRootPart", (-2, 13, -9)), look=("Thanos.HumanoidRootPart", (0, 1, 0)), fov=44),
              dict(t=2.002, pos=("Thanos.HumanoidRootPart", (-2, 13, -9)), look=("Thanos.HumanoidRootPart", (0, 1, 0)), fov=44)]),
    dict(shot="140", start=24.524, dur=0.959, play={"IronMan": "140_ironman", "Thanos": "140_thanos"},
         note="wide, low, frontal: Iron Man flying low toward camera, pitched forward 50 deg, foot/hand thrusters blazing",
         cam=[dict(t=0.000, pos=('IronMan.LowerTorso', (1.2, -0.6, 16.0)), look=('IronMan.LowerTorso', (0, 0.35, 0)), fov=28),
              dict(t=0.959, pos=('IronMan.LowerTorso', (0.8, -0.6, 7.5)), look=('IronMan.LowerTorso', (0, 0.35, 0)), fov=28)]),
    dict(shot="150", start=25.484, dur=1.043, play={"IronMan": "150_ironman", "Thanos": "150_thanos"},
         note="low-angle pitched upward (+25 deg) against bright orange sky: Iron Man in upper-right somersault flip with cyan back-thrusters",
         cam=[dict(t=0.000, pos=('IronMan.LowerTorso', (9.0, -4.5, -2.5)), look=('IronMan.LowerTorso', (0, 2.2, 0.8)), fov=38),
              dict(t=1.043, pos=('IronMan.LowerTorso', (9.0, -4.5, -2.5)), look=('IronMan.LowerTorso', (0, 2.2, 0.8)), fov=38)]),
    dict(shot="160", start=26.526, dur=0.834, play={"IronMan": "160_ironman", "Thanos": "160_thanos"},
         note="static, ankle/shin ground level: lower legs clamped to ground, heavy landing slide, dust kick-up, Thanos planted leg on left",
         cam=[dict(t=0.000, pos=('IronMan.LeftFoot', (2.8, 0.45, 2.5)), look=('IronMan.LeftFoot', (-0.6, 0.15, -0.2)), fov=32),
              dict(t=0.834, pos=('IronMan.LeftFoot', (2.75, 0.45, 2.4)), look=('IronMan.LeftFoot', (-0.6, 0.15, -0.2)), fov=32)]),
    dict(shot="170", start=27.361, dur=0.626, play={"IronMan": "170_ironman", "Thanos": "170_thanos"},
         note="past Thanos reaching arm (upper-left foreground): Iron Man in 3/4 combat stance coiled to strike with silver battering rams",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (1.5, 0.7, 14.0)), look=('IronMan.UpperTorso', (0.3, 0.25, 0)), fov=24),
              dict(t=0.626, pos=('IronMan.UpperTorso', (1.5, 0.7, 13.8)), look=('IronMan.UpperTorso', (0.3, 0.25, 0)), fov=24)]),
    dict(shot="180", start=27.986, dur=0.626, play={"IronMan": "180_ironman", "Thanos": "180_thanos"},
         note="side profile medium two-shot with clean sky headroom: Thanos right arm lowered, ram slam with radial bloom & horizontal blue back thrusters",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (-9.0, 0.5, -2.0)), look=('Thanos.UpperTorso', (1.5, 0.5, 1.0)), fov=46),   # from Iron Man's side: Iron Man at right of frame, Thanos centre, rock wall behind Thanos (movie 28.0-28.4)
              dict(t=0.626, pos=('Thanos.UpperTorso', (-9.0, 0.5, -2.0)), look=('Thanos.UpperTorso', (1.5, 0.5, 1.0)), fov=46)]),
    dict(shot="185", start=28.612, dur=0.792, play={"IronMan": "185_ironman", "Thanos": "185_thanos"},
         note="wide battlefield shot: fighters separated by 4 studs on X, shifted left-of-center onto rocky ridge, thruster clash sparks",
         cam=[dict(t=0.000, pos=('World', (10.5, 6.0, -3.3)), look=('World', (-2.0, 5.5, 3.0)), fov=46),   # two-shot between the fighters (Iron Man left, Thanos driven back right), wall behind Thanos
              dict(t=0.792, pos=('World', (10.5, 6.0, -3.3)), look=('World', (-2.0, 5.5, 3.0)), fov=46)]),
    dict(shot="190", start=29.404, dur=1.084, play={"IronMan": "190_ironman", "Thanos": "190_thanos"},
         note="tight OTS medium close-up: Thanos on left-center (35 deg right) gripping helmet, Iron Man in lower-right foreground facing up-left",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-1.2, 0.9, -2.9)), look=('Thanos.Head', (0.1, -0.2, 0)), fov=36),
              dict(t=1.084, pos=('IronMan.UpperTorso', (-1.1, 0.9, -2.8)), look=('Thanos.Head', (0.1, -0.2, 0)), fov=36)]),
    dict(shot="200", hide="Thanos", face={'dist': 3.2, 'yaw': 0, 'pitch': 0, 'roll': 0}, start=30.489, dur=0.626, play={"IronMan": "200_ironman", "Thanos": "200_thanos"},
         note="close-up pulled back: Tony unmasked with dark hair, looking up-left in shock (Yaw +20, Pitch +8), shoulders lowered",
         cam=[dict(t=0.000, pos=('IronMan.Head', (-0.35, 0.15, -3.8)), look=('IronMan.Head', (0.1, -0.05, 0)), fov=32),   # head front is -Z: camera on the face side
              dict(t=0.626, pos=('IronMan.Head', (-0.3, 0.15, -3.7)), look=('IronMan.Head', (0.1, -0.05, 0)), fov=32)]),
    dict(shot="210", start=31.114, dur=0.459, play={"IronMan": "210_ironman", "Thanos": "210_thanos"},
         note="brutal headbutt two-shot: full reformed helmet, Thanos on left lunges headbutt down-right, Tony recoils back-right with spark",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (3.2, 1.2, -6.5)), look=('Thanos.UpperTorso', (-0.8, 0.4, 0.8)), fov=34),
              dict(t=0.459, pos=('Thanos.UpperTorso', (3.1, 1.2, -6.3)), look=('Thanos.UpperTorso', (-0.8, 0.4, 0.8)), fov=34)]),
    dict(shot="213", start=31.573, dur=0.334, play={"IronMan": "213_ironman", "Thanos": "213_thanos"},
         note="side two-shot for the hit (reference 31.5-31.9): Thanos's fist into Iron Man's chest, Iron Man reeling back, both in frame",
         cam=[dict(t=0.000, pos=('World', (9.0, 5.8, 1.3)), look=('World', (0.0, 5.5, 1.3)), fov=46),
              dict(t=0.334, pos=('World', (9.0, 5.8, 1.3)), look=('World', (0.0, 5.5, 1.3)), fov=46)]),
    dict(shot="216", start=31.907, dur=0.918, play={"IronMan": "216_ironman", "Thanos": "216_thanos"},
         note="side two-shot for the leg grip and throw (reference 32.0-32.4): Thanos holds Iron Man's hip, throws him sideways to the ground",
         cam=[dict(t=0.000, pos=('World', (4.6, 4.6, -9.2)), look=('World', (-2.4, 4.0, 0.6)), fov=44),   # across the line between the fighters: Thanos and Iron Man side by side
              dict(t=0.918, pos=('World', (4.6, 4.6, -9.2)), look=('World', (-2.4, 4.0, 0.6)), fov=44)]),
    dict(shot="220", hide="IronMan", start=32.824, dur=2.419, play={"IronMan": "220_ironman", "Thanos": "220_thanos"},
         note="medium full-shot dollied close: Thanos on left-center filling 70% frame height, angled 40 deg right, fists near hips",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (3.6, 0.6, -14.5)), look=('Thanos.UpperTorso', (-0.7, 0.1, 0)), fov=34),   # full-body wide, Thanos ~70% of frame (reference 33.4)
              dict(t=2.419, pos=('Thanos.UpperTorso', (3.4, 1.0, -10.7)), look=('Thanos.UpperTorso', (-0.7, 0.1, 0)), fov=32)]),
    dict(shot="230", face={'dist': 3.0, 'yaw': 0, 'pitch': 0, 'roll': 0}, start=35.244, dur=0.626, play={"IronMan": "230_ironman", "Thanos": "230_thanos"},
         note="tight close-up pulled back: Iron Man in low ground crouch, shoulders down, helmet angled 22 deg left and +10 deg up glaring at Thanos",
         cam=[dict(t=0.000, pos=('IronMan.Head', (1.5, 0.35, -3.2)), look=('IronMan.Head', (-0.3, 0.05, 0)), fov=28),   # face side (head front is -Z)
              dict(t=0.626, pos=('IronMan.Head', (1.45, 0.35, -3.1)), look=('IronMan.Head', (-0.3, 0.05, 0)), fov=28)]),
    dict(shot="240", start=35.869, dur=1.460, play={"IronMan": "240_ironman", "Thanos": "240_thanos"},
         note="wide battlefield: Thanos on left-third raising glowing Gauntlet, Iron Man in lower-right defensive crouch",
         cam=[dict(t=0.000, pos=('World', (10.19, 4.85, -9.23)), look=('World', (-2.5, 5.0, 0.0)), fov=42),
              dict(t=1.460, pos=('World', (10.0, 4.85, -9.0)), look=('World', (-2.5, 5.0, 0.0)), fov=42)]),
    dict(shot="250", start=37.329, dur=0.542, play={"IronMan": "250_ironman", "Thanos": "250_thanos"},
         note="side profile: Iron Man in deep braced athletic lunge, thick curved nanotech tower shield deployed (beam not started yet)",
         cam=[dict(t=0.000, pos=('World', (-0.15, 5.3, -8.1)), look=('World', (-6.2, 4.8, -3.2)), fov=34),
              dict(t=0.542, pos=('World', (-0.25, 5.3, -8.0)), look=('World', (-6.2, 4.8, -3.2)), fov=34)]),
    dict(shot="255", start=37.871, dur=0.667, play={"IronMan": "255_ironman", "Thanos": "255_thanos"},
         note="medium-wide detonation: Iron Man visible right-of-center braced behind shield; thick purple beam slams in from left detonating massive radial plasma burst",
         cam=[dict(t=0.000, pos=('World', (-6.0, 4.6, -14.0)), look=('World', (-6.5, 4.5, -2.5)), fov=40),   # wider: beam from the left into the shield (reference 37.9)
              dict(t=0.667, pos=('World', (-3.15, 3.96, -8.2)), look=('World', (-6.5, 4.5, -2.5)), fov=38)]),
    dict(shot="260", start=38.538, dur=1.210, play={"IronMan": "260_ironman", "Thanos": "260_thanos"},
         note="side tracking: continuous thick purple energy torrent hammers shield, deflected plasma cones wash around body, sliding backward",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (5.2, 1.0, -12.0)), look=('IronMan.UpperTorso', (0.75, -0.3, 0.57)), fov=44),   # pulled back side tracking (reference 38.4)
              dict(t=1.210, pos=('IronMan.UpperTorso', (4.9, 0.8, -4.5)), look=('IronMan.UpperTorso', (0.75, -0.3, 0.57)), fov=42)]),
    dict(shot="262", start=39.748, dur=1.335, play={"IronMan": "262_ironman", "Thanos": "262_thanos"},
         note="tight OTS close-up behind right shoulder: violent violet plasma waves wash directly over shield & helmet, obscuring background",
         cam=[dict(t=0.000, pos=('IronMan.Head', (-0.95, 0.6, -6.0)), look=('IronMan.UpperTorso', (1.2, 0.15, 1.8)), fov=44),   # pulled back from the shoulder (reference 39.4-40.4)
              dict(t=1.335, pos=('IronMan.Head', (-0.85, 0.35, -1.4)), look=('IronMan.UpperTorso', (1.2, 0.15, 1.8)), fov=42)]),
    dict(shot="265", hide="Thanos", start=41.083, dur=0.709, play={"IronMan": "265_ironman", "Thanos": "265_thanos"},
         note="close tracking side: Iron Man drops shield and lunges forward-left in low aerodynamic sprint under the beam, thrusters firing",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (4.8, 0.8, -4.5)), look=('IronMan.UpperTorso', (-0.8, 0.1, 0.4)), fov=38),
              dict(t=0.709, pos=('IronMan.UpperTorso', (4.5, 0.8, -4.2)), look=('IronMan.UpperTorso', (-0.8, 0.1, 0.4)), fov=38)]),
    dict(shot="270", start=41.792, dur=0.542, play={"IronMan": "270_ironman", "Thanos": "270_thanos"},
         note="medium-wide tracking: Iron Man launched diagonally upward-left (~35 deg) airborne barrel-roll with focused conical thruster flame",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (5.8, 1.2, -7.2)), look=('IronMan.UpperTorso', (-0.4, 0.2, 0.0)), fov=38),
              dict(t=0.542, pos=('IronMan.UpperTorso', (5.6, 1.2, -7.0)), look=('IronMan.UpperTorso', (-0.4, 0.2, 0.0)), fov=38)]),
    dict(shot="275", hide="Thanos", start=42.334, dur=0.459, play={"IronMan": "275_ironman", "Thanos": "275_thanos"},
         note="ECU boot thruster insert: lower leg / boot skimming dirt diagonally across frame",
         cam=[dict(t=0.000, pos=('IronMan.RightLowerLeg', (1.2, 0.75, -2.5)), look=('IronMan.RightFoot', (0.1, -0.35, 0.15)), fov=34),
              dict(t=0.459, pos=('IronMan.RightLowerLeg', (1.2, 0.75, -2.5)), look=('IronMan.RightFoot', (0.1, -0.35, 0.15)), fov=34)]),
    dict(shot="280", start=42.793, dur=0.584, play={"IronMan": "280_ironman", "Thanos": "280_thanos"},
         note="medium two-shot side profile: Thanos on left punches right, Iron Man on right in defensive cross-guard",
         cam=[dict(t=0.000, pos=('World', (3.0, 5.85, -4.75)), look=('World', (-0.76, 5.35, 1.77)), fov=38),
              dict(t=0.584, pos=('World', (2.85, 5.85, -4.7)), look=('World', (-0.76, 5.35, 1.77)), fov=38)]),
    dict(shot="290", start=43.377, dur=0.709, play={"IronMan": "290_ironman", "Thanos": "290_thanos"},
         note="close, ground level: right boot slams onto pinned gauntlet, anchors bite into soil",
         cam=[dict(t=0.000, pos=('World', (-0.2, 2.6, 5.8)), look=('World', (-0.9, 2.2, 3.4)), fov=30),
              dict(t=0.709, pos=('World', (-0.15, 2.6, 5.8)), look=('World', (-0.9, 2.2, 3.4)), fov=30)]),
    dict(shot="295", start=44.086, dur=0.459, play={"IronMan": "295_ironman", "Thanos": "295_thanos"},
         note="wide: Thanos on one knee left, Iron Man standing tall winding right arm high overhead, right half negative space",
         cam=[dict(t=0.000, pos=('World', (-16.5, 6.2, -7.5)), look=('World', (4.5, 4.6, 4.5)), fov=38),
              dict(t=0.459, pos=('World', (-16.4, 6.2, -7.4)), look=('World', (4.5, 4.6, 4.5)), fov=38)]),
    dict(shot="300", start=44.544, dur=0.459, play={"IronMan": "300_ironman", "Thanos": "300_thanos"},
         note="close on his right arm mid-spin: nanotech piles onto the fist into a heavy weapon",
         cam=[dict(t=0.000, pos=('IronMan.RightHand', (1.8, 1.1, -2.4)), look=('IronMan.RightHand', (0.0, -0.2, 0.0)), fov=28),
              dict(t=0.459, pos=('IronMan.RightHand', (1.75, 1.1, -2.35)), look=('IronMan.RightHand', (0.0, -0.2, 0.0)), fov=28)]),
    dict(shot="310", start=45.003, dur=0.542, play={"IronMan": "310_ironman", "Thanos": "310_thanos"},
         note="front/OTS: Iron Man back top-left whips downward smashing battering ram into Thanos face in bottom-right",
         cam=[dict(t=0.000, pos=('World', (1.8, 7.2, -1.8)), look=('World', (-0.9, 4.8, 3.4)), fov=36),
              dict(t=0.542, pos=('World', (1.75, 7.2, -1.75)), look=('World', (-0.9, 4.8, 3.4)), fov=36)]),
    dict(shot="320", hide="IronMan", start=45.545, dur=3.212, play={"IronMan": "320_ironman", "Thanos": "320_thanos"},
         note="close, low, front-left: the blow still ringing, head hung; his fingers come up to the brow",
         cam=[dict(t=0.000, pos=('Thanos.Head', (-2.2, -0.7, -3.8)), look=('Thanos.Head', (0.0, -0.1, 0.0)), fov=28),
              dict(t=3.212, pos=('Thanos.Head', (-2.0, -0.7, -3.6)), look=('Thanos.Head', (0.0, -0.1, 0.0)), fov=28)]),
    dict(shot="340", hide="IronMan", start=48.757, dur=0.834, play={"IronMan": "340_ironman", "Thanos": "340_thanos"},
         note="close on his right hand, palm up: blood on his fingertip",
         cam=[dict(t=0.000, pos=('Thanos.RightHand', (-1.6, 1.3, -1.6)), look=('Thanos.RightHand', (0.0, 0.0, 0.0)), fov=26),   # realvideo cut 43: static extreme close-up macro on his fingertip, blood on it
              dict(t=0.834, pos=('Thanos.RightHand', (-1.6, 1.3, -1.6)), look=('Thanos.RightHand', (0.0, 0.0, 0.0)), fov=26)]),
    dict(shot="350", hide="IronMan", start=49.591, dur=2.669, play={"IronMan": "350_ironman", "Thanos": "350_thanos"},
         note="close on his face: blood on his brow; he raises his eyes to Iron Man, half a smile",
         cam=[dict(t=0.000, pos=('Thanos.Head', (-0.8, 0.0, -4.5)), look=('Thanos.Head', (0.0, -0.1, 0.0)), fov=28),
              dict(t=2.669, pos=('Thanos.Head', (-0.7, 0.0, -4.2)), look=('Thanos.Head', (0.0, -0.1, 0.0)), fov=28)]),
    dict(shot="360", start=52.261, dur=0.500, play={"IronMan": "360_ironman", "Thanos": "360_thanos"},
         note="side-on two-shot, the face-off: Thanos on his knee screen left, Iron Man standing screen right",
         cam=[dict(t=0.000, pos=('World', (1.67, 6.26, -2.55)), look=('World', (-0.61, 5.79, 1.98)), fov=40),
              dict(t=0.500, pos=('World', (1.56, 6.23, -2.33)), look=('World', (-0.61, 5.79, 1.98)), fov=40)]),
    dict(shot="370", start=52.761, dur=0.292, play={"IronMan": "370_ironman", "Thanos": "370_thanos"},
         note="low angle at the ground: Thanos lunges in and sweeps Iron Man's feet out from under him",
         cam=[dict(t=0.000, pos=('World', (-0.05, 2.28, -1.02)), look=('World', (-2.21, 2.2, 2.25)), fov=36),
              dict(t=0.292, pos=('World', (-0.05, 2.28, -1.02)), look=('World', (-2.21, 2.2, 2.25)), fov=36)]),
    dict(shot="375", start=53.053, dur=0.959, play={"IronMan": "375_ironman", "Thanos": "375_thanos"},
         note="wide, Dutch tilt: Iron Man is hurled flipping horizontally through the air toward screen right",
         cam=[dict(t=0.000, pos=('World', (-8.5, 2.6, 4.2)), look=('World', (-6.8, 6.2, -1.2)), fov=44, roll=-22),
              dict(t=0.959, pos=('World', (-8.4, 2.65, 4.0)), look=('World', (-6.8, 6.2, -1.2)), fov=44, roll=-22)]),
    dict(shot="380", start=54.012, dur=0.667, play={"IronMan": "380_ironman", "Thanos": "380_thanos"},
         note="low ground angle behind him: Iron Man slams hard onto his back, skidding face-up into the dust",
         cam=[dict(t=0.000, pos=('IronMan.Head', (-1.5, -0.6, -1.2)), look=('IronMan.LowerTorso', (0.0, -0.4, 0.0)), fov=36),
              dict(t=0.667, pos=('IronMan.Head', (-1.4, -0.6, -1.1)), look=('IronMan.LowerTorso', (0.0, -0.4, 0.0)), fov=36)]),
    dict(shot="390", start=54.680, dur=0.459, play={"IronMan": "390_ironman", "Thanos": "390_thanos"},
         note="low-angle two-shot past Tony's head in foreground: Thanos strides in menacingly, fist cocked",
         cam=[dict(t=0.000, pos=('World', (-14.0, 1.75, -6.75)), look=('World', (-6.9, 6.0, 0.7)), fov=36),
              dict(t=0.459, pos=('World', (-13.9, 1.77, -6.65)), look=('World', (-6.9, 6.0, 0.7)), fov=36)]),
    dict(shot="395", hud="mask", hide="Thanos", face={'dist': 2.8, 'yaw': 0, 'pitch': 0, 'roll': 0}, start=55.138, dur=0.375, play={"IronMan": "395_ironman", "Thanos": "395_thanos"},
         note="inside-the-mask: Tony wide-eyed looking up in dread as Thanos looms over him",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.8)), look=('IronMan.Head', (0, 0, 0)), fov=26),
              dict(t=0.375, pos=('IronMan.Head', (0, 0.0, 2.8)), look=('IronMan.Head', (0, 0, 0)), fov=26)]),
    dict(shot="400", hide="Thanos", start=55.514, dur=0.626, play={"IronMan": "400_ironman", "Thanos": "400_thanos"},
         note="top-down high angle looking down at Tony: he desperately scrambles to cross his arms and block",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (2.8, 4.8, 3.4)), look=('IronMan.UpperTorso', (0.0, 0.2, 0.0)), fov=38),
              dict(t=0.626, pos=('IronMan.UpperTorso', (2.7, 4.7, 3.3)), look=('IronMan.UpperTorso', (0.0, 0.2, 0.0)), fov=38)]),
    dict(shot="405", hud="mask", hide="Thanos", face={'dist': 2.6, 'yaw': 48, 'pitch': 0, 'roll': 0}, start=56.139, dur=0.459, play={"IronMan": "405_ironman", "Thanos": "405_thanos"},
         note="inside-the-mask: PUNCH 1 lands, Tony jerks violently under holographic HUD",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, 0, 0)), fov=26),
              dict(t=0.459, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, 0, 0)), fov=26)]),
    dict(shot="410", start=56.598, dur=1.126, play={"IronMan": "410_ironman", "Thanos": "410_thanos"},
         note="low ground angle side view: Iron Man propped on ground on his back/side, propping upper body against golden horizon",
         cam=[dict(t=0.000, pos=('World', (-12.2, 4.4, 3.6)), look=('World', (-12.0, 4.0, -4.0)), fov=44),   # side view: Thanos's punch and Iron Man both in frame (reference 57.1)
              dict(t=1.126, pos=('World', (-12.2, 4.4, 3.6)), look=('World', (-12.0, 4.0, -4.0)), fov=44)]),
    dict(shot="415", hud="mask", hide="Thanos", face={'dist': 2.6, 'yaw': 0, 'pitch': 0, 'roll': 5}, start=57.724, dur=0.375, play={"IronMan": "415_ironman", "Thanos": "415_thanos"},
         note="inside-the-mask: Tony grimacing in agony with eyes clenched as blood drips down his brow",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, 0, 0)), fov=26),
              dict(t=0.375, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, 0, 0)), fov=26)]),
    dict(shot="420", hide="Thanos", start=58.100, dur=0.667, play={"IronMan": "420_ironman", "Thanos": "420_thanos"},
         note="extreme close-up on dirt: Punch 1 — red shoulder on left, gold/red helmet turned sideways in dirt on right",
         cam=[dict(t=0.000, pos=('IronMan.Head', (-1.25, 0.85, -2.6)), look=('IronMan.Head', (0.35, -0.05, 0.15)), fov=32),
              dict(t=0.667, pos=('IronMan.Head', (-1.2, 0.85, -2.5)), look=('IronMan.Head', (0.35, -0.05, 0.15)), fov=32)]),
    dict(shot="425", start=58.767, dur=0.584, play={"IronMan": "425_ironman", "Thanos": "425_thanos"},
         note="overhead punch down Thanos's arm: purple arm bottom-left driving straight into Iron Man helmet pinned in center",
         cam=[dict(t=0.000, pos=('World', (-13.8, 4.8, -6.4)), look=('World', (-11.98, 1.43, -4.65)), fov=38),
              dict(t=0.584, pos=('World', (-13.75, 4.78, -6.35)), look=('World', (-11.98, 1.43, -4.65)), fov=38)]),
    dict(shot="430", hide="Thanos", start=59.351, dur=0.959, play={"IronMan": "430_ironman", "Thanos": "430_thanos"},
         note="extreme close-up shattered helmet: Punch 2 — gold faceplate torn away exposing Tony's bruised forehead & eye",
         cam=[dict(t=0.000, pos=('IronMan.Head', (-1.25, 0.85, -2.6)), look=('IronMan.Head', (0.35, -0.05, 0.15)), fov=32),
              dict(t=0.959, pos=('IronMan.Head', (-1.2, 0.85, -2.5)), look=('IronMan.Head', (0.35, -0.05, 0.15)), fov=32)]),
    dict(shot="435", start=60.310, dur=1.919, play={"IronMan": "435_ironman", "Thanos": "435_thanos"},
         note="wide static low: Thanos grabs collar, lifts Iron Man off ground, gauntlet glows purple, point-blank blast",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (9.2, 1.2, -12.5)), look=('Thanos.UpperTorso', (0.8, 0.4, 0.8)), fov=35),
              dict(t=1.919, pos=('Thanos.UpperTorso', (9.0, 1.2, -12.3)), look=('Thanos.UpperTorso', (0.8, 0.4, 0.8)), fov=35)]),
    dict(shot="440", hide="Thanos", start=62.229, dur=1.168, play={"IronMan": "440_ironman", "Thanos": "440_thanos"},
         note="static low behind wreckage: Iron Man crashes, tumbles, slides to a stop on his back mid-frame",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-1.39, 0.35, -5.19)), look=('IronMan.UpperTorso', (0.0, 0.2, 0.0)), fov=40),
              dict(t=1.168, pos=('IronMan.UpperTorso', (-1.35, 0.33, -5.05)), look=('IronMan.UpperTorso', (0.0, 0.2, 0.0)), fov=40)]),
    dict(shot="445", start=63.397, dur=1.335, play={"IronMan": "445_ironman", "Thanos": "445_thanos"},
         note="wide tracking: Thanos lowers gauntlet and marches toward Iron Man; Tony stirs in distant rubble",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (0.2, 0.9, -4.6)), look=('Thanos.UpperTorso', (0.0, 0.55, 0.0)), fov=30),   # frontal chest-up close-up, as the reference 63.4-64.7
              dict(t=1.335, pos=('Thanos.UpperTorso', (0.2, 0.9, -4.5)), look=('Thanos.UpperTorso', (0.0, 0.55, 0.0)), fov=30)]),
    dict(shot="450", start=64.731, dur=0.709, play={"IronMan": "450_ironman", "Thanos": "450_thanos"},
         note="low angle rubble: Iron Man pushes onto one knee, raises right gauntlet and fires repulsor beam",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-5.5, -0.2, 5.0)), look=('IronMan.UpperTorso', (0.0, 0.3, 0.0)), fov=38, roll=-8),
              dict(t=0.709, pos=('IronMan.UpperTorso', (-5.3, -0.18, 4.8)), look=('IronMan.UpperTorso', (0.0, 0.3, 0.0)), fov=38, roll=-8)]),
    dict(shot="455", start=65.440, dur=0.918, play={"IronMan": "455_ironman", "Thanos": "455_thanos"},
         note="medium-wide tracking: Thanos blocks repulsor beam with gauntlet, walking relentlessly through sparks",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (-3.5, 0.4, -6.5)), look=('Thanos.UpperTorso', (0.0, 0.3, 0.0)), fov=34),
              dict(t=0.918, pos=('Thanos.UpperTorso', (-3.4, 0.38, -6.2)), look=('Thanos.UpperTorso', (0.0, 0.3, 0.0)), fov=34)]),
    dict(shot="460", start=66.358, dur=1.418, play={"IronMan": "460_ironman", "Thanos": "460_thanos"},
         note="close-up: Iron Man kneeling, nanotech armor flows and regenerates across damaged chest plates",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-4.0, 0.3, 3.2)), look=('IronMan.UpperTorso', (0.2, 0.3, 0.0)), fov=34),
              dict(t=1.418, pos=('IronMan.UpperTorso', (-3.9, 0.32, 3.1)), look=('IronMan.UpperTorso', (0.2, 0.3, 0.0)), fov=34)]),
    dict(shot="465", hide="Thanos", start=67.776, dur=0.751, play={"IronMan": "465_ironman", "Thanos": "465_thanos"},
         note="medium-close front-right: Iron Man on one knee unleashes dual searing fire-lasers towards screen left",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (6.5, 0.6, -5.5)), look=('IronMan.UpperTorso', (-0.2, 0.3, 0.2)), fov=34),
              dict(t=0.751, pos=('IronMan.UpperTorso', (6.4, 0.6, -5.3)), look=('IronMan.UpperTorso', (-0.2, 0.3, 0.2)), fov=34)]),
    dict(shot="470", start=68.527, dur=2.002, play={"IronMan": "470_ironman", "Thanos": "470_thanos"},
         note="over-the-shoulder behind Tony: dual fiery laser streams converge on Thanos marching forward through flames",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-2.84, 0.65, -3.37)), look=('Thanos.UpperTorso', (0.4, 0.25, -0.69)), fov=36),
              dict(t=2.002, pos=('IronMan.UpperTorso', (-2.7, 0.62, -3.2)), look=('Thanos.UpperTorso', (0.35, 0.25, -0.6)), fov=36)]),
    dict(shot="475", hide="Thanos", start=70.529, dur=1.126, play={"IronMan": "475_ironman", "Thanos": "475_thanos"},
         note="medium close-up profile: Iron Man strains with intense effort, gritting teeth as he channels maximum fire",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (6.2, 0.5, -5.8)), look=('IronMan.UpperTorso', (-0.2, 0.3, 0.2)), fov=32),
              dict(t=1.126, pos=('IronMan.UpperTorso', (6.1, 0.52, -5.7)), look=('IronMan.UpperTorso', (-0.2, 0.3, 0.2)), fov=32)]),
    dict(shot="480", hide="IronMan", start=71.655, dur=1.210, play={"IronMan": "480_ironman", "Thanos": "480_thanos"},
         note="frontal medium: Thanos marches directly toward camera into convergent fire-lasers, gauntlet raised glowing purple",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (-10.5, 0.3, -6.0)), look=('Thanos.UpperTorso', (0.0, 0.35, 0.0)), fov=34),
              dict(t=1.210, pos=('Thanos.UpperTorso', (-9.5, 0.32, -5.5)), look=('Thanos.UpperTorso', (0.0, 0.35, 0.0)), fov=34)]),
    dict(shot="485", start=72.864, dur=0.542, play={"IronMan": "485_ironman", "Thanos": "485_thanos"},
         note="side two-shot: Thanos advances, fists slam down into twin beams",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (4.8, 0.8, -7.5)), look=('IronMan.UpperTorso', (1.2, 0.4, 0.7)), fov=34),
              dict(t=0.542, pos=('IronMan.UpperTorso', (4.7, 0.8, -7.3)), look=('IronMan.UpperTorso', (1.2, 0.4, 0.7)), fov=34)]),
    dict(shot="490", start=73.407, dur=0.959, play={"IronMan": "490_ironman", "Thanos": "490_thanos"},
         note="over-the-shoulder behind Iron Man: Thanos winds up left gauntlet, steps in, delivers punch to Tony face",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-2.2, 0.6, -3.2)), look=('Thanos.UpperTorso', (0.0, 0.3, 0.0)), fov=34),
              dict(t=0.959, pos=('IronMan.UpperTorso', (-2.0, 0.6, -3.0)), look=('Thanos.UpperTorso', (0.0, 0.3, 0.0)), fov=34)]),
    dict(shot="505", start=74.366, dur=0.626, play={"IronMan": "505_ironman", "Thanos": "505_thanos"},
         note="low medium two-shot: Thanos swings second strike; Tony reels, raising arms to guard",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (3.8, -0.4, -5.8)), look=('IronMan.UpperTorso', (1.0, 0.6, 0.6)), fov=36),
              dict(t=0.626, pos=('IronMan.UpperTorso', (3.7, -0.4, -5.6)), look=('IronMan.UpperTorso', (1.0, 0.6, 0.6)), fov=36)]),
    dict(shot="520", start=74.992, dur=0.959, play={"IronMan": "520_ironman", "Thanos": "520_thanos"},
         note="close two-shot: Thanos gauntlet hammers down onto Tony crossed forearms",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (2.2, 0.35, -4.2)), look=('IronMan.UpperTorso', (0.0, 0.35, 0.1)), fov=34),
              dict(t=0.959, pos=('IronMan.UpperTorso', (2.1, 0.35, -4.1)), look=('IronMan.UpperTorso', (0.0, 0.35, 0.1)), fov=34)]),
    dict(shot="525", start=75.951, dur=0.542, play={"IronMan": "525_ironman", "Thanos": "525_thanos"},
         note="OTS Tony: Thanos grimaces and presses down",
         cam=[dict(t=0.000, pos=('IronMan.Head', (-1.2, 0.3, -3.2)), look=('Thanos.Head', (0.0, 0.0, 0.0)), fov=32),
              dict(t=0.542, pos=('IronMan.Head', (-1.2, 0.3, -3.2)), look=('Thanos.Head', (0.0, 0.0, 0.0)), fov=32)]),
    dict(shot="530", start=76.493, dur=0.918, play={"IronMan": "530_ironman", "Thanos": "530_thanos"},
         note="wide landscape: both struggling on the Titan battlefield",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (18.0, 4.0, -22.0)), look=('IronMan.UpperTorso', (0.0, 1.0, 0.0)), fov=44),
              dict(t=0.918, pos=('IronMan.UpperTorso', (17.5, 4.0, -21.5)), look=('IronMan.UpperTorso', (0.0, 1.0, 0.0)), fov=44)]),
    dict(shot="535", start=77.411, dur=0.417, play={"IronMan": "535_ironman", "Thanos": "535_thanos"},
         note="medium two-shot struggle before sword pulls out",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (4.2, 0.5, -6.0)), look=('IronMan.UpperTorso', (0.8, 0.4, 0.5)), fov=34),
              dict(t=0.417, pos=('IronMan.UpperTorso', (4.2, 0.5, -6.0)), look=('IronMan.UpperTorso', (0.8, 0.4, 0.5)), fov=34)]),
    dict(shot="540", start=77.828, dur=1.376, play={"IronMan": "540_ironman", "Thanos": "540_thanos"},
         note="low close on Tony's left forearm: the nanotech sword pulls out of the armour",
         cam=[dict(t=0.000, pos=('IronMan.LeftHand', (-1.8, 0.5, -2.5)), look=('IronMan.LeftHand', (0.0, 0.0, 0.0)), fov=28),
              dict(t=1.376, pos=('IronMan.LeftHand', (-1.8, 0.5, -2.5)), look=('IronMan.LeftHand', (0.0, 0.0, 0.0)), fov=28)]),
    dict(shot="545", start=79.204, dur=0.667, play={"IronMan": "545_ironman", "Thanos": "545_thanos"},
         note="the sword raised, glowing; Thanos turns to it",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (-4.0, 1.2, -6.0)), look=('IronMan.LeftHand', (0.0, 0.3, 0.0)), fov=36),
              dict(t=0.667, pos=('IronMan.UpperTorso', (-4.0, 1.2, -6.0)), look=('IronMan.LeftHand', (0.0, 0.3, 0.0)), fov=36)]),
    dict(shot="550", start=79.871, dur=0.667, play={"IronMan": "550_ironman", "Thanos": "550_thanos"},
         note="wide: Thanos holds Iron Man down, both struggle over the blade",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (-11.0, 2.5, -12.0)), look=('IronMan.UpperTorso', (0.0, 0.3, 0.0)), fov=40),
              dict(t=0.667, pos=('Thanos.UpperTorso', (-11.0, 2.5, -12.0)), look=('IronMan.UpperTorso', (0.0, 0.3, 0.0)), fov=40)]),
    dict(shot="555", start=80.539, dur=0.500, play={"IronMan": "555_ironman", "Thanos": "555_thanos"},
         note="reference 80.5-81.0: from Tony's struggling face down to the thrust into his belly, Thanos's hand and blade in frame",
         cam=[dict(t=0.000, pos=('World', (-33.5, 7.0, -5.5)), look=('World', (-28.6, 5.6, -11.8)), fov=42),
              dict(t=0.500, pos=('World', (-33.0, 6.6, -5.0)), look=('World', (-28.4, 5.2, -11.6)), fov=42)]),
    dict(shot="560", start=81.039, dur=1.554, play={"IronMan": "560_ironman", "Thanos": "560_thanos"},
         note="Thanos' hand takes the blade; it breaks; the stab into Tony's chest. The video ends here.",
         cam=[dict(t=0.000, pos=('IronMan.UpperTorso', (6.5, 0.8, -4.5)), look=('IronMan.UpperTorso', (0.0, 0.2, 0.0)), fov=38),
              dict(t=1.554, pos=('IronMan.UpperTorso', (6.3, 0.8, -4.3)), look=('IronMan.UpperTorso', (0.0, 0.2, 0.0)), fov=38)]),
]

# hud: inside-the-helmet overlay drawn by the Director ("mask" = vignette, glow, readouts;
# "lock" = mask + the target-lock cluster that locks onto Thanos, as in movie shot 100).

# Subtitles (movie time). Lines as given in the shot log; no movie audio is used.
SUBS = [
    (4.00, 7.80, "You throw another moon at me, and I'm gonna lose it."),
    (8.10, 9.10, "Stark."),
    (9.40, 10.40, "You know me?"),
    (10.90, 15.60, "You're not the only one cursed with knowledge."),
    (16.20, 18.00, "My only curse is you."),
    (20.80, 21.40, "Come on."),
    (49.00, 51.20, "All that for a drop of blood."),
]
PREROLL = {"Thanos": "010_thanos", "IronMan": "040_ironman"}   # pose each rig holds before its first shot
STAND = {"Thanos": "070_thanos", "IronMan": "060_ironman"}      # standing shots used to settle each rig on its mark

# Roblox renders ~1.3x tighter than this file's geometry model (measured: recording 2026-10-22
# 014144, torso widths vs the movie in 010/030/050). The Director dollies every camera back
# along its line of sight by this factor, so aim and composition stay the same.
PULLBACK = 1.3

# Effects on the movie timeline (client-side, played by the Director).
#   nanoshot: Iron Man's nanotech piece streaks in from `from` (offset from the target part,
#   world studs) and hits at t+dur with a flash, then stays stuck to the target at `local`
#   (offset in the part's own axes; the left hand's +X is its palm).
FX = [
    dict(kind="nanoshot", t=0.62, dur=0.12, target="Thanos.LeftHand", frm=(18, 7, -12), local=(1.05, 0, 0)),   # on the gauntlet's +X face, just outside it (the gauntlet reaches 0.69)
    # 110: twin launcher pods pop open on shoulders with orange flames & smoke
    dict(kind="pods", t=18.15, grow=0.45, t1=20.65, target="IronMan.UpperTorso"),
    # 115: no launch bloom. The movie at 19.3-20.2 shows smoke and the missiles only; a big glow hid Iron Man.
    # 110-130: micro-missiles curling up and diving onto Thanos
    dict(kind="missiles", target="IronMan.UpperTorso", at="Thanos.HumanoidRootPart", n=12, seed=7,
         launch0=18.55, launch1=18.75, hit0=22.15, hit1=22.5),   # movie 22.2: they reach him
    # 115 -> 120: a missile whips past the lens as a blue flare
    dict(kind="flare", t=20.53, dur=0.14),
    # 130: massive multi-stud fireball and thick black/grey smoke engulfing Thanos
    # (no fireball on Thanos: movie 22.9 is a small blast on the ground far off, not a sphere over him)
    dict(kind="dust", t=22.8, t1=24.6, at="Thanos.HumanoidRootPart"),
    # 130b (movie 22.52-24.5): consecutive blasts across his guard, fireballs and shockwave dust, smoke engulfing him
    dict(kind="smokecloud", t=21.9, t1=24.6, at="Thanos.HumanoidRootPart", rate=220),
    dict(kind="blast", t=22.55, at="Thanos.UpperTorso", offset=(0, 1.0, -1.0), size=1.6),
    dict(kind="blast", t=22.85, at="Thanos.UpperTorso", offset=(1.2, 0.4, -1.0), size=1.8),
    dict(kind="blast", t=23.20, at="Thanos.UpperTorso", offset=(-1.2, 0.8, -0.8), size=1.5),
    dict(kind="blast", t=23.55, at="Thanos.UpperTorso", offset=(0.4, 1.2, -1.0), size=1.4),
    # 140-150: boot + hand thrusters (flame leaves the part along `dir`, in the part's own axes)
    dict(kind="thruster", part="IronMan.LeftFoot", dir=(0, -1, 0), t=24.40, t1=25.60, size=1.8),
    dict(kind="thruster", part="IronMan.RightFoot", dir=(0, -1, 0), t=24.40, t1=25.60, size=1.8),
    dict(kind="thruster", part="IronMan.LeftHand", dir=(0, -1, 0), t=24.40, t1=25.75, size=1.2),
    dict(kind="thruster", part="IronMan.RightHand", dir=(0, -1, 0), t=24.40, t1=25.75, size=1.2),
    # 140: warm dust haze around flying Iron Man
    dict(kind="dust", t=24.40, t1=25.50, at="IronMan.LowerTorso"),
    # 150: cyan back-thrusters enabled during mid-air somersault
    dict(kind="backthruster", rig="IronMan", t=25.80, t1=26.40, color=(50, 220, 255)),
    # 140-150: the blue device under his feet, the kick's impact, the landing dust
    dict(kind="kickdisc", rig="IronMan", t=25.15, t1=25.80),
    dict(kind="impact", t=25.70, at="Thanos.UpperTorso", offset=(0, 0, -1.2), size=5.5, color=(140, 190, 255), dur=0.25, light=10),
    dict(kind="impact", t=26.55, at="IronMan.LeftFoot", offset=(-0.2, -0.4, -0.9), size=3.5, color=(110, 95, 78), dur=1.2, light=0),
    dict(kind="impact", t=26.55, at="IronMan.RightFoot", offset=(0.2, -0.4, -0.9), size=3.5, color=(110, 95, 78), dur=1.2, light=0),
    # 160: ground anchors lock his boots down
    dict(kind="anchors", rig="IronMan", t=26.70, t1=27.40),
    # 170-185: nanotech battering-ram cannons form on both forearms, jet blue backwards while he charges, the clash
    dict(kind="cannons", rig="IronMan", t=27.40, grow=0.45, t1=29.6, jet0=27.99, jet1=29.45),
    dict(kind="wall", t=28.33, breakT=29.05, t1=32.0, pos=(0.5, 6.0, 12.5), size=(22, 12, 3)),   # fixed rock wall; face at z 11.0 meets Thanos's back at 29.0 s   # rock wall Thanos is driven into (movie 28.4)
    dict(kind="ramimpact", t=28.33, at="Thanos.UpperTorso", offset=(0, 0, -1.5), size=2.5, color=(190, 225, 255), dur=0.4, light=5),   # small hit flash, no dome (movie 28.0-28.4)
    dict(kind="impact", t=28.33, at="Thanos.UpperTorso", offset=(0, 0, -1.5), size=2.2, color=(170, 190, 255), dur=0.3, light=4),
    # 185: thruster clash sparks between fighters grappling
    dict(kind="clashsparks", rig="IronMan", t=28.65, t1=29.40, color=(255, 200, 100)),
    # 190: the hook hits the helmet (metal sparks)
    dict(kind="impact", t=29.95, at="IronMan.Head", offset=(0.4, 0, 0.3), size=3.2, color=(255, 200, 150), dur=0.2, light=5),
    # 190-200: helmet crushed at t0, torn off at t, nanotech reforms by t1=31.05 so full helmet is on for shot 210 headbutt!
    dict(kind="helmet", rig="IronMan", t0=30.15, t=30.55, t1=31.05, grow=0.06, fling=(-14, 4, 6)),
    # 210: brutal headbutt impact spark and camera shake
    dict(kind="impact", t=31.36, at="IronMan.Head", offset=(-0.1, 0.2, 0.2), size=3.5, color=(255, 210, 150), dur=0.22, light=8),
    dict(kind="shake", t=31.36, amp=0.42),
    # 216: the hammer blow on his back, the slam into the ground, the skid through the dust
    dict(kind="impact", t=32.04, at="IronMan.UpperTorso", offset=(0, 0.7, 0), size=4.5, color=(255, 190, 140), dur=0.25, light=6),
    dict(kind="impact", t=32.45, at="IronMan.LowerTorso", offset=(0, 0, 0), size=4.4, color=(110, 95, 78), dur=1.0, light=0),
    dict(kind="skid", part="IronMan.LowerTorso", t=32.20, t1=32.85),
]
# the nanotech piece stuck in his palm since 010: his right hand pulls it out at `pull` and flings it
FX[0].update(pull=34.78, hand="Thanos.RightHand", fling=(16, 9, -6))
FX += [
    # 240-262: the purple beam: charge at gauntlet from t0=36.55, fires at t=37.878 (shot 255 start!), slams into shield at hit=38.20, holds until 41.5
    dict(kind="beam", src="Thanos.LeftHand", dst="IronMan", t0=36.55, t=37.878, hit=38.20, t1=41.5),
    # 250: nanotech tower shield builds on left forearm (t=37.40 .. 37.75), facing Thanos
    dict(kind="shield", rig="IronMan", face="Thanos", t=37.40, grow=0.35, t1=41.20, fling=(-6, 9, -12)),
    # 255: massive radial violet-white plasma detonation on shield impact
    dict(kind="impact", t=38.20, at="IronMan.UpperTorso", offset=(0, 0.4, 0), size=4.5, color=(220, 140, 255), dur=0.6, light=10),   # smaller energy burst on Iron Man (reference 38.4): no hard bubble
    dict(kind="shake", t=38.20, amp=0.55),
    # 260-262: boots gouging ground, continuous rumble, deep purple ambient wash
    dict(kind="skid", part="IronMan.LeftFoot", t=38.5, t1=41.2),
    dict(kind="skid", part="IronMan.RightFoot", t=38.5, t1=41.2),
    dict(kind="shake", t=38.545, amp=0.45, t1=41.2, every=0.10, each=0.12),
    dict(kind="tint", t=38.90, t1=41.20, color=(160, 60, 255), alpha=0.22),   # purple flood starts with the energy around Iron Man (reference 38.9)
    # 265-270: thrusters firing during sprint and airborne lunge
    dict(kind="thruster", part="IronMan.UpperTorso", dir=(0, 0, 1), t=41.09, t1=42.34, size=1.4),
    dict(kind="thruster", part="IronMan.LeftFoot", dir=(0, -1, 0), t=41.75, t1=43.2, size=1.1),
    dict(kind="thruster", part="IronMan.RightFoot", dir=(0, -1, 0), t=41.75, t1=43.2, size=1.1),
    dict(kind="thruster", part="IronMan.LeftHand", dir=(0, -1, 0), t=41.8, t1=43.1, size=0.9),
    dict(kind="thruster", part="IronMan.RightHand", dir=(0, -1, 0), t=41.8, t1=43.1, size=0.9),
    # 280-290: he lands on the gauntlet: the slam, the dust, anchors bite into the ground
    dict(kind="impact", t=43.30, at="IronMan.LeftFoot", offset=(0, -0.3, 0), size=3.4, color=(110, 95, 78), dur=1.0, light=0),
    dict(kind="impact", t=43.30, at="Thanos.LeftHand", offset=(0, 0, 0), size=2.4, color=(255, 200, 150), dur=0.2, light=4),
    dict(kind="anchors", rig="IronMan", t=43.35, t1=45.05),
    # 300-310: the fist weapon forms (t .. t+grow), glows from `glow`, smashes into his face at `hit`
    dict(kind="fistgun", part="IronMan.RightHand", t=44.6, grow=0.35, glow=44.65, hit=45.39, t1=46.2, at="Thanos.Head"),
    # 320-360: the cut over his brow and the blood on his fingertip (marks stuck to the part, offsets
    # as fractions of the part's size: front of the head is -Z); `grow` s to appear
    dict(kind="mark", part="Thanos.Head", offset=(-0.22, 0.28, -0.52), size=(0.22, 0.09, 0.02), t=45.42, grow=0.4, color=(120, 10, 16)),
    dict(kind="mark", part="Thanos.Head", offset=(-0.26, 0.12, -0.52), size=(0.05, 0.22, 0.02), t=45.8, grow=1.6, color=(105, 8, 14)),
    dict(kind="mark", part="Thanos.RightHand", offset=(-0.5, 0.0, 0.0), size=(0.5, 0.3, 0.5), t=48.4, grow=0.2, color=(120, 8, 12)),   # blood on his fingertips, on the top of the hand (reference 49.2)
    # 370-380: the sweep, the flip, the slam onto the bedrock, sliding through the dust
    dict(kind="impact", t=53.00, at="IronMan.LeftFoot", offset=(0, 0, 0), size=2.8, color=(140, 115, 95), dur=0.6, light=0),
    dict(kind="shake", t=53.00, amp=0.25),
    dict(kind="impact", t=54.02, at="IronMan.UpperTorso", offset=(0, 0.3, 0), size=5.5, color=(120, 100, 80), dur=1.2, light=0),
    dict(kind="skid", part="IronMan.LowerTorso", t=54.02, t1=54.55),
    dict(kind="shake", t=54.02, amp=0.55),
    # 390: Thanos striding in, footsteps on the bedrock
    dict(kind="impact", t=54.70, at="Thanos.LeftFoot", offset=(0, -0.2, 0), size=2.0, color=(110, 95, 78), dur=0.4, light=0),
    dict(kind="impact", t=55.10, at="Thanos.RightFoot", offset=(0, -0.2, 0), size=2.2, color=(110, 95, 78), dur=0.4, light=0),
    # 405: Punch 1 on the crossed forearms — metal collision sparks, ring shockwave, hit-stop
    dict(kind="impact", t=56.15, at="IronMan.LeftLowerArm", offset=(0, 0.3, 0), size=4.2, color=(255, 220, 160), dur=0.25, light=8),
    dict(kind="shake", t=56.15, amp=0.48),
    # 410: Punch 2 breaking through into his chest — sparks fountain, armor crunch shockwave
    dict(kind="impact", t=57.33, at="IronMan.UpperTorso", offset=(0, 0.3, 0), size=5.0, color=(255, 190, 130), dur=0.3, light=9),
    dict(kind="shake", t=57.33, amp=0.52),
    # 420: Punch 3 smashing into his face — brutal impact flash, head snaps, hit-stop shudder
    dict(kind="impact", t=58.35, at="IronMan.Head", offset=(-0.2, 0.1, 0), size=4.0, color=(255, 200, 140), dur=0.25, light=8),
    dict(kind="shake", t=58.35, amp=0.6),
    # 425: Punch 4 from above landing straight down onto the helmet
    dict(kind="impact", t=58.85, at="IronMan.Head", offset=(0, 0.3, 0), size=4.0, color=(255, 210, 150), dur=0.25, light=8),
    dict(kind="impact", t=58.85, at="IronMan.Head", offset=(0, -0.2, 0), size=3.0, color=(90, 80, 68), dur=0.35, light=0),
    dict(kind="shake", t=58.85, amp=0.55),
    # 430: Punch 5 cross swing snapping face to left
    dict(kind="impact", t=59.45, at="IronMan.Head", offset=(0.2, 0.1, 0), size=3.5, color=(255, 200, 140), dur=0.25, light=7),
    dict(kind="shake", t=59.45, amp=0.50),
    # 435: Collar grab, lift off ground, and foot plant
    dict(kind="impact", t=60.55, at="IronMan.LowerTorso", offset=(0, -0.2, 0), size=2.5, color=(105, 92, 75), dur=0.4, light=0),
    dict(kind="impact", t=61.00, at="Thanos.RightFoot", offset=(0, -0.2, 0), size=1.8, color=(105, 92, 75), dur=0.35, light=0),
    # 435: Point-blank Power Stone blast to chest & frame flash
    dict(kind="stoneblast", t0=60.70, t=61.65, t1=62.30, src="Thanos.LeftHand", target="IronMan.UpperTorso"),
    dict(kind="tint", t=61.62, t1=61.80, color=(170, 90, 255), alpha=0.40),
    # 440: Iron Man crashes into rubble, skids, and settles
    dict(kind="impact", t=62.28, at="IronMan.UpperTorso", offset=(0, -0.2, 0), size=6.0, color=(115, 100, 82), dur=1.4, light=0),
    dict(kind="skid", t=62.28, t1=62.65, at="IronMan.LowerTorso"),
    dict(kind="shake", t=62.28, amp=0.45),
    dict(kind="impact", t=62.30, at="IronMan.LowerTorso", offset=(0, -0.2, 0), size=4.5, color=(105, 92, 75), dur=1.1, light=0),
    # 450-455: Repulsor beam firing and gauntlet deflection
    dict(kind="repulsor", t0=65.25, t=65.35, t1=66.45, src="IronMan.RightHand", dst="Thanos.LeftHand"),
    dict(kind="impact", t=65.35, at="IronMan.RightHand", offset=(0, 0, -0.4), size=2.8, color=(240, 255, 255), dur=0.25, light=10),
    dict(kind="shake", t=65.35, amp=0.40),
    dict(kind="shake", t=65.55, amp=0.45),
    # 460: Nanotech armor regeneration shimmer on Tony
    dict(kind="nanotech", t0=66.50, t1=67.78, part="IronMan.UpperTorso"),
    dict(kind="impact", t=73.75, at="IronMan.Head", offset=(0.2, 0.1, 0.1), size=4.0, color=(255, 180, 220), dur=0.25, light=8),
    dict(kind="shake", t=73.75, amp=0.55),
    dict(kind="impact", t=75.00, at="IronMan.LeftLowerArm", offset=(0, 0.3, 0), size=3.5, color=(220, 180, 255), dur=0.25, light=6),
    dict(kind="shake", t=75.00, amp=0.45),
    # 465-480: Dual fire-lasers and gauntlet energy flare
    dict(kind="firelaser", t=67.783, t1=71.662, src1="IronMan.RightHand", src2="IronMan.LeftHand", dst="Thanos.UpperTorso"),
    dict(kind="firelaser", t=71.662, t1=73.414, src1="IronMan.RightHand", src2="IronMan.LeftHand", dst="Thanos.LeftHand"),   # beams held until the fists stop them (73.41)
    dict(kind="impact", t=81.05, at="IronMan.UpperTorso", offset=(0, 0.2, 0), size=4.5, color=(140, 115, 95), dur=0.8, light=0),
    dict(kind="shake", t=81.05, amp=0.5),
    dict(kind="impact", t=81.45, at="IronMan.LowerTorso", offset=(0, -0.6, 0), size=3.2, color=(120, 100, 80), dur=0.6, light=0),
    dict(kind="dust", t=81.00, t1=82.60, at="IronMan.LeftFoot"),
    # Thanos' face (movie 0-4.2 s): brows (+raise / -glare) and eyelids (1 open, 0 shut). Read by Director updateFace.
    # 2.30: he looks up at Tony and glares. Blinks at 1.10 and 3.40.
    dict(kind="face", t=0.00, brow=0.00, lid=0.80, mouth=0.00),
    dict(kind="face", t=0.80, brow=0.10, lid=0.70, mouth=0.00),
    dict(kind="face", t=1.05, brow=0.25, lid=0.95, mouth=0.20),
    dict(kind="face", t=1.10, brow=0.25, lid=0.05, mouth=0.00),
    dict(kind="face", t=1.18, brow=0.20, lid=0.85, mouth=0.00),
    dict(kind="face", t=1.60, brow=0.00, lid=0.80, mouth=0.00),
    dict(kind="face", t=2.00, brow=-0.25, lid=0.50, mouth=-0.30),
    dict(kind="face", t=2.30, brow=-0.45, lid=0.40, mouth=-0.60),
    dict(kind="face", t=2.60, brow=-0.30, lid=0.55, mouth=-0.40),
    dict(kind="face", t=3.00, brow=-0.10, lid=0.75, mouth=-0.10),
    dict(kind="face", t=3.40, brow=-0.10, lid=0.04, mouth=0.00),
    dict(kind="face", t=3.48, brow=-0.10, lid=0.80, mouth=0.00),
    dict(kind="face", t=4.20, brow=0.00, lid=1.00, mouth=0.00, off=1),
    dict(kind="sword", t0=77.95, t1=79.21, handoff=79.25, brk=80.90, t_end=82.60, hand="IronMan.LeftHand", hand2="Thanos.LeftHand", aim=80.50, aimAt="IronMan.UpperTorso"),   # Thanos takes the sword at 79.25 (reference 79.0), points it at Iron Man from 80.5   # 540-560: nanotech sword
    dict(kind="impact", t=71.70, at="Thanos.LeftHand", offset=(0, 0, 0), size=4.0, color=(190, 80, 255), dur=1.1, light=8),
    dict(kind="shake", t=67.783, amp=0.35),
    dict(kind="shake", t=68.534, amp=0.30),
    dict(kind="shake", t=70.536, amp=0.40),
    dict(kind="shake", t=71.662, amp=0.35),
]
FRAME_ASPECT = 1920 / 1010                                    # the reference clip's frame (letterboxed)


# -------------------------------------------------------------------------------- output
def lua_vec(v):
    return "Vector3.new(%s)" % ", ".join(f"{x:g}" for x in v)


def lua_target(tp):
    target, off = tp
    return f'{{"{target}", {lua_vec(off)}}}'


def write_scene_data(shots, path):
    L = ["-- GENERATED by scene.py — edit scene.py, not this file.", "return {"]
    L.append(f"\taspect = {FRAME_ASPECT:.4f},")
    L.append(f"\trefHeight = {REF_HEIGHT},   -- rig height (studs, before scale) the camera offsets were planned for")
    L.append("\trigs = {")
    for name, r in RIGS.items():
        L.append(f'\t\t{name} = {{ pos = {lua_vec(r["pos"])}, yaw = {r["yaw"]}, scale = {r["scale"]}, camScale = {r["camScale"]} }},')
    L.append("\t},")
    L.append(f"\tpullback = {PULLBACK},")
    L.append("\tsubs = {")
    for a, b, text in SUBS:
        L.append(f'\t\t{{ t0 = {a}, t1 = {b}, text = "{text}" }},')
    L.append("\t},")
    L.append("\tpreroll = { " + ", ".join(f'{k} = "{v}"' for k, v in PREROLL.items()) + " },")
    L.append("\tstand = { " + ", ".join(f'{k} = "{v}"' for k, v in STAND.items()) + " },")
    L.append("\tfx = {")
    lua_key = {"frm": "from", "local": "localOffset"}             # Python keywords -> Director names
    for fx in FX:
        fields = []
        for k, v in fx.items():
            val = lua_vec(v) if isinstance(v, tuple) else f'"{v}"' if isinstance(v, str) else f"{v:g}"
            fields.append(f"{lua_key.get(k, k)} = {val}")
        L.append("\t\t{ " + ", ".join(fields) + " },")
    L.append("\t},")
    L.append("\tshots = {")
    for sh in TIMELINE:
        play = ", ".join(f'{rig} = "{anim}"' for rig, anim in sh["play"].items())
        hud = f' hud = "{sh["hud"]}",' if sh.get("hud") else ""
        hud += f' hide = "{sh["hide"]}",' if sh.get("hide") else ""
        if sh.get("face"):
            hud += " face = { " + ", ".join(f"{k} = {v:g}" for k, v in sh["face"].items()) + " },"
        L.append(f'\t\t{{ shot = "{sh["shot"]}", start = {sh["start"]}, dur = {sh["dur"]}, play = {{ {play} }},{hud}')
        L.append(f'\t\t  note = "{sh["note"]}",')
        L.append("\t\t  cam = {")
        for k in sh["cam"]:
            roll_str = f', roll = {k["roll"]}' if k.get("roll") else ""
            L.append(f'\t\t\t{{ t = {k["t"]}, pos = {lua_target(k["pos"])}, look = {lua_target(k["look"])}, fov = {k["fov"]}{roll_str} }},')
        L.append("\t\t  } },")
    L.append("\t},")
    L.append("\tlengths = { " + ", ".join(f'["{k}"] = {(len(v["LowerTorso"]) - 1) / FPS:.3f}' for k, v in shots.items()) + " },")
    L.append("}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def padded(S):
    pad = int(round(HOLD_PAD * FPS))
    return {p: np.concatenate([m, np.repeat(m[-1:], pad, 0)]) for p, m in S.items()}


if __name__ == "__main__":
    shots = build_shots()
    os.makedirs(SHOTS, exist_ok=True)
    for f in os.listdir(SHOTS):                       # shots/ is fully generated
        if f.endswith(".rbxmx"):
            os.remove(os.path.join(SHOTS, f))
    for name, S in shots.items():
        write_shot(padded(S), os.path.join(SHOTS, f"{name}.rbxmx"), name)
    write_scene_data(shots, os.path.join(HERE, "SceneData.lua"))
    print("timeline:", " | ".join(f'{s["shot"]} {s["start"]:.3f}+{s["dur"]:.3f}' for s in TIMELINE))
