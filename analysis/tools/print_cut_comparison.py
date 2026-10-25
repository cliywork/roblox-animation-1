import json
import sys

with open('scratch_all_79_cuts_mapped.json', encoding='utf-8') as f:
    cuts = json.load(f)

sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

tl_dict = {s['shot']: s for s in TIMELINE}

print(f"Total cuts: {len(cuts)}")
for i, c in enumerate(cuts):
    sid = c['shot_id']
    old = tl_dict.get(sid)
    if not old and sid in ('130a', '130b'):
        old = tl_dict.get('130')
        print(f"Cut {c['cut_num']:2d} ({sid}): real=[{c['t_start']:.3f}..{c['t_end']:.3f}, dur={c['dur']:.3f}] | old 130=[{old['start']:.3f}..{old['start']+old['dur']:.3f}, dur={old['dur']:.3f}]")
    elif old:
        print(f"Cut {c['cut_num']:2d} ({sid}): real=[{c['t_start']:.3f}..{c['t_end']:.3f}, dur={c['dur']:.3f}] | old=[{old['start']:.3f}..{old['start']+old['dur']:.3f}, dur={old['dur']:.3f}]")
    else:
        print(f"Cut {c['cut_num']:2d} ({sid}): NOT FOUND")
