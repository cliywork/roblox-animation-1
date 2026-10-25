import os
import shutil
import json
import re

SCENE_PATH = "roblox_pipeline/scene.py"
BACKUP_PATH = "roblox_pipeline/backup/scene_before_79cuts.py"

# Restore from backup first to ensure clean state
shutil.copy(BACKUP_PATH, SCENE_PATH)
print(f"Restored clean {SCENE_PATH} from {BACKUP_PATH}")

with open("scratch_all_79_cuts_mapped.json", encoding="utf-8") as f:
    cuts = json.load(f)

with open(SCENE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update FIGHT_SHOTS
fight_shots_entries = []
for c in cuts[15:]: # cut 16 is index 15
    sid = c['shot_id']
    t_start = round(c['t_start'], 3)
    dur = 1.554 if sid == "560" else round(c['dur'], 3)
    fight_shots_entries.append(f'("{sid}", {t_start:.3f}, {dur:.3f})')

fs_lines = []
chunk = []
for entry in fight_shots_entries:
    chunk.append(entry)
    if len(chunk) == 6:
        fs_lines.append("               " + ", ".join(chunk) + ",")
        chunk = []
if chunk:
    fs_lines.append("               " + ", ".join(chunk))

new_fight_shots = "FIGHT_SHOTS = [" + fs_lines[0].strip() + "\n" + "\n".join(fs_lines[1:]) + "]"

content = re.sub(r'FIGHT_SHOTS = \[.*?\]\n', new_fight_shots + "\n", content, flags=re.DOTALL)

# 2. Add 130a and 130b into build_shots()
target_130 = 's["130_thanos"] = keyed(TH_130, 3.086)'
replacement_130 = """s["130_thanos"] = keyed(TH_130, 3.086)
    s["130a_thanos"] = stack([at_keys(t, TH_130) for t in frame_times(1.084)])
    s["130b_thanos"] = stack([at_keys(1.084 + t, TH_130) for t in frame_times(2.002)])"""

assert target_130 in content, "target_130 not found in scene.py"
content = content.replace(target_130, replacement_130, 1)

# 3. Build new TIMELINE
import sys
sys.path.insert(0, "roblox_pipeline")
sys.path.insert(0, "roblox_pipeline/backup")
import scene_before_79cuts as old_scene
old_tl = {s['shot']: s for s in old_scene.TIMELINE}

tl_lines = ["TIMELINE = ["]

for c in cuts:
    num = c['cut_num']
    sid = c['shot_id']
    t_start = round(c['t_start'], 3)
    dur = 1.554 if sid == "560" else round(c['dur'], 3)
    
    if sid == '130a':
        tl_lines.append(f'    dict(shot="130a", start={t_start:.3f}, dur={dur:.3f}, play={{"Thanos": "130a_thanos"}},')
        tl_lines.append(f'         note="Cut 14: top angle behind missiles, camera trails behind swarm converging on Thanos at high speed",')
        tl_lines.append(f'         cam=[dict(t=0.000, pos=("Thanos.HumanoidRootPart", (-7, 18, -36)), look=("Thanos.HumanoidRootPart", (0, 1, 0)), fov=35),')
        tl_lines.append(f'              dict(t={dur:.3f}, pos=("Thanos.HumanoidRootPart", (-18, 9.5, -6)), look=("Thanos.HumanoidRootPart", (0, 3, -1)), fov=34)]),')
    elif sid == '130b':
        tl_lines.append(f'    dict(shot="130b", start={t_start:.3f}, dur={dur:.3f}, play={{"Thanos": "130b_thanos"}},')
        tl_lines.append(f'         note="Cut 15: wide ground-level 35 deg profile shot of blast, high-explosive missile impacts detonate across Thanos guard, dust cloud",')
        tl_lines.append(f'         cam=[dict(t=0.000, pos=("Thanos.HumanoidRootPart", (-34, 11, -18)), look=("Thanos.HumanoidRootPart", (-1, 2, 0)), fov=40),')
        tl_lines.append(f'              dict(t={dur:.3f}, pos=("Thanos.HumanoidRootPart", (-34, 11, -18)), look=("Thanos.HumanoidRootPart", (-1, 2, 0)), fov=40)]),')
    else:
        old = old_tl[sid]
        hud_str = f', hud="{old["hud"]}"' if old.get("hud") else ""
        hide_str = f', hide="{old["hide"]}"' if old.get("hide") else ""
        face_str = f', face={old["face"]}' if old.get("face") else ""
        play_str = ", ".join(f'"{k}": "{v}"' for k, v in old["play"].items())
        
        tl_lines.append(f'    dict(shot="{sid}"{hud_str}{hide_str}{face_str}, start={t_start:.3f}, dur={dur:.3f}, play={{{play_str}}},')
        tl_lines.append(f'         note="{old["note"]}",')
        
        cam_entries = []
        for k in old['cam']:
            t_k = dur if k['t'] > 0 else 0.0
            roll_str = f', roll={k["roll"]}' if k.get("roll") else ""
            cam_entries.append(f'dict(t={t_k:.3f}, pos={k["pos"]}, look={k["look"]}, fov={k["fov"]}{roll_str})')
        
        tl_lines.append(f'         cam=[{cam_entries[0]},')
        for ce in cam_entries[1:-1]:
            tl_lines.append(f'              {ce},')
        tl_lines.append(f'              {cam_entries[-1]}]),')

tl_lines.append("]")
new_timeline_str = "\n".join(tl_lines)

# Replace TIMELINE in content up to the closing bracket of TIMELINE
content = re.sub(r'TIMELINE = \[.*?\n\]\n\n# hud:', new_timeline_str + "\n\n# hud:", content, flags=re.DOTALL)

with open(SCENE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully updated {SCENE_PATH} to 79 cuts!")
