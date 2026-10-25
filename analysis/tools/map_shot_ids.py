import json
import sys

with open('scratch_all_79_cuts.json') as f:
    cuts = json.load(f)

# Load TIMELINE from scene.py
sys.path.insert(0, '.')
sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

# We map each cut to its planned shot ID
# Note: Shot 130 in TIMELINE corresponds to Cut 14 (130a) and Cut 15 (130b)
timeline_map = {}
for s in TIMELINE:
    timeline_map[s['shot']] = s

# Assign shot IDs to all 79 cuts
shot_ids = [
    "010", "020", "030", "040", "050", "060", "070", "080", "090", "100", # 1-10
    "110", "115", "120", "130a", "130b", "140", "150", "160", "170", "180", "185", "190", # 11-22
    "200", "210", "213", "216", "220", "230", "240", "250", "255", "260", "262", "265", "270", "275", "280", "290", "295", "300", "310", # 23-41
    "320", "340", "350", "360", "370", "375", "380", "390", "395", "400", "405", "410", "415", "420", "425", "430", # 42-57
    "435", "440", "445", "450", "455", "460", "465", "470", "475", "480", "485", "490", "505", "520", "525", "530", "535", "540", "545", "550", "555", "560" # 58-79
]

print(f"Total shot IDs assigned: {len(shot_ids)}")
assert len(shot_ids) == len(cuts)

for i in range(len(cuts)):
    cuts[i]['shot_id'] = shot_ids[i]

with open('scratch_all_79_cuts_mapped.json', 'w') as f:
    json.dump(cuts, f, indent=2)

print("Saved scratch_all_79_cuts_mapped.json")
