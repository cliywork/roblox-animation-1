import json
import os

with open("roblox_studio_cuts_dump.json", encoding="utf-8") as f:
    studio_cuts = json.load(f)

with open("scratch_all_79_cuts_mapped.json", encoding="utf-8") as f:
    mapped_cuts = json.load(f)

print(f"Loaded {len(studio_cuts)} studio cuts and {len(mapped_cuts)} mapped cuts.")
assert len(studio_cuts) == 79
assert len(mapped_cuts) == 79
