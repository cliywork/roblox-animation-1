"""
rbxmx_io.py — read/write R15 KeyframeSequence .rbxmx files as numpy Motor6D.Transform arrays.

    from rbxmx_io import read_shot, write_shot
    times, T = read_shot("shots/050_ironman_stand.rbxmx")   # T[part] -> (N,4,4)
"""
import numpy as np
import xml.etree.ElementTree as ET
from smpl_to_r15 import R15, CHILDREN, write_rbxmx

TAGS = ["X", "Y", "Z"] + [f"R{i}{j}" for i in range(3) for j in range(3)]


def _T(cf):
    v = {c.tag: float(c.text) for c in cf}
    T = np.eye(4)
    T[:3, :3] = np.array([v[f"R{i}{j}"] for i in range(3) for j in range(3)]).reshape(3, 3)
    T[:3, 3] = [v["X"], v["Y"], v["Z"]]
    return T


def read_shot(path):
    """-> (times (N,), {part: (N,4,4)}) for every R15 part (identity where a pose is missing)."""
    root = ET.parse(path).getroot()
    kfs = root.findall("./Item/Item[@class='Keyframe']")
    times = np.array([float(k.find("Properties/float[@name='Time']").text) for k in kfs])
    T = {p: np.tile(np.eye(4), (len(kfs), 1, 1)) for p in R15}
    for i, kf in enumerate(kfs):
        for pose in kf.iter("Item"):
            if pose.get("class") != "Pose":
                continue
            name = pose.find("Properties/string[@name='Name']").text
            if name in T:
                T[name][i] = _T(pose.find("Properties/CoordinateFrame"))
    order = np.argsort(times)
    return times[order], {p: m[order] for p, m in T.items()}


def resample(times, T, new_times):
    """Sample a shot at new_times (seconds): linear position, slerp rotation."""
    from scipy.spatial.transform import Rotation as R, Slerp
    new_times = np.clip(new_times, times[0], times[-1])
    out = {}
    for p, m in T.items():
        rot = Slerp(times, R.from_matrix(m[:, :3, :3]))(new_times).as_matrix()
        pos = np.stack([np.interp(new_times, times, m[:, k, 3]) for k in range(3)], 1)
        o = np.tile(np.eye(4), (len(new_times), 1, 1))
        o[:, :3, :3], o[:, :3, 3] = rot, pos
        out[p] = o
    return out


def write_shot(T, path, name, fps=30.0):
    """Write {part: (N,4,4)} sampled at fps as a KeyframeSequence."""
    write_rbxmx(T, path, name, fps=fps)


def world(T, part, i):
    """World rotation of an R15 part at frame i (C0/C1 have no rotation on Rig Builder rigs)."""
    if part == "HumanoidRootPart":
        return np.eye(3)
    return world(T, R15[part][0], i) @ T[part][i, :3, :3]
