import glob, os

for f in glob.glob('roblox_pipeline/*.lua') + glob.glob('roblox_pipeline/*.py'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        for i, line in enumerate(fp):
            if '"130"' in line or "'130'" in line:
                print(f"{os.path.basename(f)}:{i+1}: {line.strip()[:70]}")
