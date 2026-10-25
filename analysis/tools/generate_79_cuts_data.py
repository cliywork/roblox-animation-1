import json
import os
import sys

# Define all 79 cut start frames
cut_frames = [
    0, 20, 54, 63, 91, 141, 188, 220, 250, 380,
    434, 463, 495, 514, 540, 588, 611, 636, 656, 671, 686, 705,
    731, 746, 757, 765, 787, 845, 860, 895, 908, 924, 953, 985, 1002, 1015, 1026, 1040, 1057, 1068, 1079,
    1092, 1169, 1189, 1253, 1265, 1272, 1295, 1311, 1322, 1331, 1346, 1357, 1384, 1393, 1409, 1423,
    1446, 1492, 1520, 1552, 1569, 1591, 1625, 1643, 1691, 1718, 1747, 1760, 1783, 1798, 1821, 1834, 1856, 1866, 1899, 1915, 1931, 1943
]

fps = 23.976023976023978
total_frames = 1955  # frames 0..1954

def fmt_time(t):
    m = int(t // 60)
    s = t % 60
    return f"{m:02d}:{s:06.3f}"

cuts = []
for i in range(len(cut_frames)):
    f_start = cut_frames[i]
    f_end = cut_frames[i+1] if i + 1 < len(cut_frames) else total_frames
    n_frames = f_end - f_start
    t_start = f_start / fps
    t_end = f_end / fps
    dur = n_frames / fps
    cuts.append({
        'cut_num': i + 1,
        'f_start': f_start,
        'f_end': f_end - 1, # inclusive last frame of cut
        'next_f': f_end,
        'n_frames': n_frames,
        't_start': t_start,
        't_end': t_end,
        'dur': dur,
        't_start_str': fmt_time(t_start),
        't_end_str': fmt_time(t_end),
    })

print(f"Generated {len(cuts)} cuts:")
for c in cuts[:15]:
    print(f"Cut {c['cut_num']:2d}: {c['t_start_str']} -> {c['t_end_str']} ({c['dur']:.3f}s, {c['n_frames']:2d} fr, f{c['f_start']:4d}-f{c['f_end']:4d})")

with open('scratch_all_79_cuts.json', 'w') as f:
    json.dump(cuts, f, indent=2)
