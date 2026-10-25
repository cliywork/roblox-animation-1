import sys
sys.path.insert(0, 'roblox_pipeline')
from scene import TIMELINE

print('Total shots in TIMELINE:', len(TIMELINE))
for i, s in enumerate(TIMELINE):
    print(f"{i+1:2d}: shot {s['shot']:5s} - start {s['start']:6.3f} - dur {s['dur']:5.3f} - cam keys {len(s['cam'])}")
