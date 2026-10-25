import json
import sys

with open('scratch_all_79_cuts_mapped.json', encoding='utf-8') as f:
    cuts = json.load(f)

sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

tl_dict = {s['shot']: s for s in TIMELINE}
print(f"{'Cut':3s} | {'Shot':5s} | {'Cut Start':9s} | {'TL Start':9s} | {'Diff Start':10s} | {'Cut Dur':8s} | {'TL Dur':7s} | {'Diff Dur':8s}")
print('-' * 80)
for c in cuts:
    sid = c['shot_id']
    tl = tl_dict.get(sid)
    if not tl and sid in ('130a', '130b'):
        tl = tl_dict.get('130')
        print(f"{c['cut_num']:3d} | {sid:5s} | {c['t_start']:9.4f} | {tl['start']:9.4f} | (130 combined in old TL)")
        continue
    if tl:
        d_start = c['t_start'] - tl['start']
        d_dur = c['dur'] - tl['dur']
        flag = '*' if abs(d_start) > 0.02 or abs(d_dur) > 0.02 else ' '
        print(f"{c['cut_num']:3d}{flag}| {sid:5s} | {c['t_start']:9.4f} | {tl['start']:9.4f} | {d_start:+10.4f} | {c['dur']:8.4f} | {tl['dur']:7.4f} | {d_dur:+8.4f}")
    else:
        print(f"{c['cut_num']:3d}!| {sid:5s} | {c['t_start']:9.4f} | NOT FOUND IN TIMELINE")
