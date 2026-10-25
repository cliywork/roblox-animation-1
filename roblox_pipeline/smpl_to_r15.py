"""
smpl_to_r15.py — GVHMR (SMPL/SMPL-X body pose) -> Roblox R15 KeyframeSequence (.rbxmx)

No Blender. In Studio: Explorer > right-click Workspace > Insert from File... > pick the .rbxmx.

  python smpl_to_r15.py hmr4d_results.pt  out.rbxmx  [--name Thanos_Shot12] [--fps-step 1]
  python smpl_to_r15.py --test            test.rbxmx      # synthetic convention check

How it works
  SMPL stores each joint's rotation relative to its parent, with the rest pose = T-pose,
  Y-up, facing +Z. We run forward kinematics to get every joint's world rotation, convert
  to Roblox space (Y-up, facing -Z = a 180° turn about Y), map SMPL joints onto R15 parts,
  correct for R15's arms-down rest pose, and store Motor6D.Transform per part:
      Transform(part) = World(parent)^-1 * World(part)
  This assumes the rig's Motor6D C0/C1 have no rotation (true for Studio's Rig Builder R15).
"""
import sys, argparse
import numpy as np
from scipy.spatial.transform import Rotation as R

# first 22 SMPL / SMPL-X body joints
SMPL_PARENTS = [-1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 12, 13, 14, 16, 17, 18, 19]

# R15 part -> (R15 parent part, SMPL joint whose WORLD rotation drives it)
# Spine1-3 merge into the Waist (UpperTorso), Neck+Head into Head, Collar into UpperArm.
R15 = {
    "LowerTorso":    ("HumanoidRootPart", 0),   # Pelvis
    "UpperTorso":    ("LowerTorso", 9),         # Spine3
    "Head":          ("UpperTorso", 15),        # Head
    "LeftUpperArm":  ("UpperTorso", 16),        # L_Shoulder
    "LeftLowerArm":  ("LeftUpperArm", 18),      # L_Elbow
    "LeftHand":      ("LeftLowerArm", 20),      # L_Wrist
    "RightUpperArm": ("UpperTorso", 17),
    "RightLowerArm": ("RightUpperArm", 19),
    "RightHand":     ("RightLowerArm", 21),
    "LeftUpperLeg":  ("LowerTorso", 1),         # L_Hip
    "LeftLowerLeg":  ("LeftUpperLeg", 4),       # L_Knee
    "LeftFoot":      ("LeftLowerLeg", 7),       # L_Ankle
    "RightUpperLeg": ("LowerTorso", 2),
    "RightLowerLeg": ("RightUpperLeg", 5),
    "RightFoot":     ("RightLowerLeg", 8),
}

# SMPL -> Roblox axes: rotate 180° about Y (SMPL faces +Z, Roblox faces -Z)
M = np.diag([-1.0, 1.0, -1.0])

# Rest-pose correction: R15 arms hang down (-Y); SMPL rest is a T-pose.
# In Roblox axes the character's left is -X, right is +X.
_rz = lambda deg: R.from_euler("z", deg, degrees=True).as_matrix()
REST_FIX = {p: np.eye(3) for p in R15}
for p in ("LeftUpperArm", "LeftLowerArm", "LeftHand"):    REST_FIX[p] = _rz(-90)   # -Y -> -X
for p in ("RightUpperArm", "RightLowerArm", "RightHand"): REST_FIX[p] = _rz(+90)   # -Y -> +X

STUDS_PER_METER = 3.2   # R15 hip height (~3 studs) / human pelvis height (~0.93 m); tweak per character


def world_rotations(pose):
    """pose (N,22,3) axis-angle local rotations -> (N,22,3,3) world rotations in SMPL axes."""
    N = len(pose)
    local = R.from_rotvec(pose.reshape(-1, 3)).as_matrix().reshape(N, 22, 3, 3)
    world = np.empty_like(local)
    for j, p in enumerate(SMPL_PARENTS):
        world[:, j] = local[:, j] if p < 0 else world[:, p] @ local[:, j]
    return world


def to_r15_transforms(global_orient, body_pose, transl):
    """Returns {part: (N,4,4)} Motor6D.Transform matrices, Roblox space, studs."""
    N = len(global_orient)
    pose = np.concatenate([global_orient.reshape(N, 1, 3), body_pose.reshape(N, 21, 3)], 1)
    W = M @ world_rotations(pose) @ M.T                       # world rotations in Roblox axes
    G = {"HumanoidRootPart": np.broadcast_to(np.eye(3), (N, 3, 3))}
    for part, (_, j) in R15.items():
        G[part] = W[:, j] @ REST_FIX[part]
    out = {}
    for part, (parent, _) in R15.items():
        T = np.tile(np.eye(4), (N, 1, 1))
        T[:, :3, :3] = np.swapaxes(G[parent], 1, 2) @ G[part]
        out[part] = T
    # root motion: pelvis displacement from frame 0 (pelvis = transl + constant rest offset)
    d = (transl.reshape(N, 3) - transl.reshape(N, 3)[0]) @ M.T * STUDS_PER_METER
    out["LowerTorso"][:, :3, 3] = d
    return face_forward(out)


def start_turn(root_T):
    """Degrees the body is turned about Y (vs the rig's front, -Z) in one Root (LowerTorso) transform."""
    fwd = root_T[:3, :3] @ np.array([0.0, 0.0, -1.0])
    return np.degrees(np.arctan2(-fwd[0], -fwd[2]))

def face_forward(transforms):
    """Turn the whole shot about Y so frame 0 faces the rig's front.

    GVHMR's world yaw is arbitrary per clip (it depends on the camera), so without this a shot can
    start facing sideways or backwards. Turning during the shot is kept. Aim a character by rotating
    its rig in Studio — the Root transform is relative to HumanoidRootPart.
    """
    C = np.eye(4)
    C[:3, :3] = R.from_euler("y", -start_turn(transforms["LowerTorso"][0]), degrees=True).as_matrix()
    transforms["LowerTorso"] = C @ transforms["LowerTorso"]        # rotates body and root motion
    return transforms


# ------------------------------------------------------------------ .rbxmx writer
CHILDREN = {}
for part, (parent, _) in R15.items():
    CHILDREN.setdefault(parent, []).append(part)

def _cframe(T):
    x, y, z = T[:3, 3]; r = T[:3, :3].reshape(-1)
    tags = ["X", "Y", "Z"] + [f"R{i}{j}" for i in range(3) for j in range(3)]
    return "".join(f"<{t}>{v:.6f}</{t}>" for t, v in zip(tags, [x, y, z, *r]))

def write_rbxmx(transforms, path, name="GVHMR_Anim", fps=30.0, step=1, loop=False):
    N = len(next(iter(transforms.values())))
    ref = iter(range(10**9))
    out = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="4">',
           f'<Item class="KeyframeSequence" referent="RBX{next(ref)}"><Properties>'
           f'<string name="Name">{name}</string><bool name="Loop">{str(loop).lower()}</bool>'
           f'<token name="Priority">2</token></Properties>']   # Priority 2 = Action

    def pose(part, f):
        T = transforms[part][f] if part in transforms else np.eye(4)
        s = (f'<Item class="Pose" referent="RBX{next(ref)}"><Properties>'
             f'<CoordinateFrame name="CFrame">{_cframe(T)}</CoordinateFrame>'
             f'<token name="EasingDirection">0</token><token name="EasingStyle">0</token>'
             f'<string name="Name">{part}</string><float name="Weight">1</float></Properties>')
        return s + "".join(pose(c, f) for c in CHILDREN.get(part, [])) + "</Item>"

    for f in list(range(0, N, step)) + ([N - 1] if (N - 1) % step else []):
        out.append(f'<Item class="Keyframe" referent="RBX{next(ref)}"><Properties>'
                   f'<string name="Name">Keyframe</string><float name="Time">{f / fps:.5f}</float>'
                   f'</Properties>{pose("HumanoidRootPart", f)}</Item>')
    out.append("</Item></roblox>")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print(f"wrote {path}: {N} frames ({N / fps:.2f}s), {len(range(0, N, step))} keyframes")


# ------------------------------------------------------------------ inputs
def load_gvhmr(path):
    import torch
    P = torch.load(path, map_location="cpu")["smpl_params_global"]
    g = lambda k: P[k].detach().cpu().numpy()
    return g("global_orient"), g("body_pose"), g("transl")

def test_motion(fps=30):
    """5 one-second phases with known expected results (see README)."""
    N = 5 * fps; go = np.zeros((N, 3)); bp = np.zeros((N, 21, 3)); tr = np.zeros((N, 3))
    J = lambda smpl_idx: smpl_idx - 1           # body_pose index of an SMPL joint
    ramp = lambda f, a: np.clip((f - a * fps) / (0.5 * fps), 0, 1)   # 0->1 over half a second
    from scipy.spatial.transform import Slerp
    r_down, r_fwd = R.from_euler("z", 90, degrees=True), R.from_euler("y", 90, degrees=True)
    punch_path = Slerp([0, 1], R.concatenate([r_down, r_fwd]))   # SMPL right arm: -Y -> +Z
    for f in range(N):
        down = ramp(f, 1)                                  # 1s: arms down to sides
        bp[f, J(16)] = [0, 0, -np.pi / 2 * down]           # L_Shoulder: SMPL +X -> -Y
        bp[f, J(17)] = [0, 0, +np.pi / 2 * down]           # R_Shoulder: SMPL -X -> -Y
        punch = ramp(f, 2)                                 # 2s: RIGHT arm punches forward
        if punch > 0:
            bp[f, J(17)] = punch_path(punch).as_rotvec()
        knee = ramp(f, 3)                                  # 3s: LEFT knee lifts forward
        bp[f, J(1)] = [-np.pi / 2 * knee, 0, 0]            # L_Hip flex
        bp[f, J(4)] = [np.pi / 2 * knee, 0, 0]             # L_Knee bend back
        turn = ramp(f, 4)                                  # 4s: body turns to ITS left + steps up 1 m
        go[f] = [0, np.pi / 2 * turn, 0]
        tr[f] = [0, 1.0 * turn, 0]
    return go, bp, tr


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("inp", nargs="?"); ap.add_argument("out", nargs="?")
    ap.add_argument("--test", metavar="OUT"); ap.add_argument("--name")
    ap.add_argument("--fps-step", type=int, default=1, help="keep every Nth frame (1 = all 30 fps)")
    a = ap.parse_args()
    if a.test:
        write_rbxmx(to_r15_transforms(*test_motion()), a.test, a.name or "GVHMR_Test")
    else:
        write_rbxmx(to_r15_transforms(*load_gvhmr(a.inp)), a.out, a.name or "GVHMR_Anim", step=a.fps_step)
