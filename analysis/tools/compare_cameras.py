import re
import json
import sys

sys.path.insert(0, 'roblox_pipeline')
import scene

with open('realvideo-camera.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Parse the 79 cuts from realvideo-camera.md
cuts = []
pattern = r"### Cut (\d+) — Shot `([^`]+)`.*?\n- \*\*Movie Time Range\*\*:\s*`([^`]+)`.*?\n- \*\*Duration\*\*:\s*([^\n]+)\n- \*\*Reference Video Frame Range\*\*:\s*([^\n]+)\n- \*\*Framing / Camera Angle\*\*:\s*([^\n]+)\n- \*\*Camera Motion\*\*:\s*([^\n]+)\n- \*\*Subject Framing & Composition\*\*:\s*([^\n]+)"

for m in re.finditer(pattern, text, re.DOTALL):
    c_num = int(m.group(1))
    sid = m.group(2)
    time_range = m.group(3)
    dur = m.group(4)
    fr_range = m.group(5)
    framing = m.group(6).strip()
    motion = m.group(7).strip()
    subj = m.group(8).strip()
    cuts.append({
        'cut_num': c_num,
        'shot_id': sid,
        'time_range': time_range,
        'framing': framing,
        'motion': motion,
        'subj': subj
    })

print(f"Parsed {len(cuts)} cuts from realvideo-camera.md")

# Compare with scene.TIMELINE
tl_map = {s['shot']: s for s in scene.TIMELINE}

for c in cuts:
    sid = c['shot_id']
    tl = tl_map.get(sid)
    if not tl:
        print(f"Cut {c['cut_num']:2d} ({sid}): NOT FOUND in scene.TIMELINE")
        continue
    cam = tl.get('cam', [])
    k0 = cam[0] if cam else {}
    k1 = cam[-1] if len(cam) > 1 else k0
    fov = k0.get('fov', 'N/A')
    target = k0.get('pos', ('None', (0,0,0)))
    look = k0.get('look', ('None', (0,0,0)))
    print(f"Cut {c['cut_num']:2d} ({sid}): Real: {c['framing'][:40]} | Motion: {c['motion'][:30]}")
    print(f"       Roblox: target={target[0]} off={target[1]} look={look[0]} off={look[1]} fov={fov} keys={len(cam)}")
