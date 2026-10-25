import re
import json

with open("scratch_all_79_cuts_mapped.json", encoding="utf-8") as f:
    cuts = json.load(f)

with open("realvideo-camera.md", encoding="utf-8") as f:
    text = f.read()

# Verify each cut in realvideo-camera.md
for c in cuts:
    cut_num = c['cut_num']
    shot_id = c['shot_id']
    pattern = rf"\|\s*\*\*{cut_num}\*\*\s*\|\s*`{shot_id}`\s*\|\s*`([0-9:.]+)`\s*\(([0-9.]+)s\)\s*\|\s*`([0-9:.]+)`\s*\(([0-9.]+)s\)\s*\|\s*([0-9.]+)s\s*\((\d+)\s*fr\)\s*\|\s*f(\d+)–f(\d+)"
    m = re.search(pattern, text)
    if not m:
        print(f"FAILED to match cut {cut_num} ({shot_id}) in realvideo-camera.md!")
    else:
        start_s = float(m.group(2))
        end_s = float(m.group(4))
        dur_s = float(m.group(5))
        fr_start = int(m.group(7))
        fr_end = int(m.group(8))
        # compare with c
        assert abs(start_s - c['t_start']) < 0.002, f"Cut {cut_num} start mismatch: md={start_s}, json={c['t_start']}"
        assert abs(dur_s - c['dur']) < 0.002, f"Cut {cut_num} dur mismatch: md={dur_s}, json={c['dur']}"
        assert fr_start == c['f_start'], f"Cut {cut_num} f_start mismatch: md={fr_start}, json={c['f_start']}"
        assert fr_end == c['f_end'], f"Cut {cut_num} f_end mismatch: md={fr_end}, json={c['f_end']}"

print(f"ALL 79 CUTS MATCH realvideo-camera.md 100% PERFECTLY!")
