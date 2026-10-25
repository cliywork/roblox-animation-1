import json
import sys

with open('scratch_all_79_cuts_mapped.json', encoding='utf-8') as f:
    cuts = json.load(f)

sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

# Map old timeline by shot ID
old_tl = {s['shot']: s for s in TIMELINE}

new_timeline = []

for c in cuts:
    num = c['cut_num']
    sid = c['shot_id']
    t_start = round(c['t_start'], 3)
    dur = round(c['dur'], 3)
    
    if sid == '130a':
        entry = dict(
            shot="130a",
            start=t_start,
            dur=dur,
            play={"Thanos": "130a_thanos"},
            note="top angle behind missiles, camera trails behind swarm converging on Thanos at high speed",
            cam=[
                dict(t=0.0, pos=("Thanos.HumanoidRootPart", (-7, 18, -36)), look=("Thanos.HumanoidRootPart", (0, 1, 0)), fov=35),
                dict(t=dur, pos=("Thanos.HumanoidRootPart", (-18, 9.5, -6)), look=("Thanos.HumanoidRootPart", (0, 3, -1)), fov=34),
            ]
        )
    elif sid == '130b':
        entry = dict(
            shot="130b",
            start=t_start,
            dur=dur,
            play={"Thanos": "130b_thanos"},
            note="wide ground-level 35 deg profile shot of blast, high-explosive missile impacts detonate across Thanos' guard, dust cloud",
            cam=[
                dict(t=0.0, pos=("Thanos.HumanoidRootPart", (-34, 11, -18)), look=("Thanos.HumanoidRootPart", (-1, 2, 0)), fov=40),
                dict(t=dur, pos=("Thanos.HumanoidRootPart", (-34, 11, -18)), look=("Thanos.HumanoidRootPart", (-1, 2, 0)), fov=40),
            ]
        )
    else:
        old = old_tl[sid]
        entry = dict(old)
        entry['start'] = t_start
        entry['dur'] = dur
        # Update camera keyframe t for the end key
        new_cam = []
        for k in old['cam']:
            k_new = dict(k)
            if k['t'] > 0:
                k_new['t'] = dur
            new_cam.append(k_new)
        entry['cam'] = new_cam
        
    new_timeline.append(entry)

print(f"Generated {len(new_timeline)} timeline entries.")
assert len(new_timeline) == 79
for i, e in enumerate(new_timeline):
    print(f"Cut {i+1:2d} ({e['shot']:4s}): {e['start']:.3f} -> {e['start']+e['dur']:.3f} (dur {e['dur']:.3f}s, cam keys={len(e['cam'])})")
