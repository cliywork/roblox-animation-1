import json

with open("<ANTIGRAVITY_BRAIN>/.system_generated/steps/637/output.txt", encoding="utf-8") as f:
    batch1 = json.load(f)

with open("<ANTIGRAVITY_BRAIN>/.system_generated/steps/631/output.txt", encoding="utf-8") as f:
    batch2 = json.load(f)

all_cuts = batch1 + batch2
print(f"Total cuts combined from Studio: {len(all_cuts)}")
assert len(all_cuts) == 79

with open("roblox_studio_cuts_dump.json", "w", encoding="utf-8") as f:
    json.dump(all_cuts, f, indent=2)

print("Saved roblox_studio_cuts_dump.json successfully!")
for c in all_cuts[:5]:
    print(f"Cut {c['cut']:2d}: {c['shot']:4s} {c['start']:.3f}..{c['end']:.3f} dur={c['dur']:.3f} cam={c['camMode']} pos={c['cam_start']['pos']} fov={c['cam_start']['fov']}")
for c in all_cuts[-5:]:
    print(f"Cut {c['cut']:2d}: {c['shot']:4s} {c['start']:.3f}..{c['end']:.3f} dur={c['dur']:.3f} cam={c['camMode']} pos={c['cam_start']['pos']} fov={c['cam_start']['fov']}")
