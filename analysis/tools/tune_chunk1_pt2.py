with open("roblox_pipeline/scene.py", "r", encoding="utf-8") as f:
    text = f.read()

# 020
old_020 = """    dict(shot="020", start=0.834, dur=1.418, play={"Thanos": "020_thanos"},
         note="close-up on the gauntlet; shoulder on left edge, arm extends to center, palm open with sunburst; pulled back to avoid mesh clip",
         cam=[dict(t=0.000, pos=('Thanos.LeftUpperArm', (-2.4, 0.1, 2.8)), look=('Thanos.LeftHand', (0.0, 0.15, -0.2)), fov=25),
              dict(t=1.418, pos=('Thanos.LeftUpperArm', (-2.0, 0.1, 2.5)), look=('Thanos.LeftHand', (0.1, 0.15, -0.2)), fov=25)]),"""

new_020 = """    dict(shot="020", start=0.834, dur=1.418, play={"Thanos": "020_thanos"},
         note="close-up on the gauntlet; shoulder on left edge, arm extends to center, palm open with sunburst; pulled back to avoid mesh clip",
         cam=[dict(t=0.000, pos=('Thanos.UpperTorso', (0.8, -0.2, -4.5)), look=('Thanos.LeftHand', (0.1, 0.1, 0.0)), fov=24),
              dict(t=1.418, pos=('Thanos.UpperTorso', (0.7, -0.2, -4.2)), look=('Thanos.LeftHand', (0.1, 0.1, 0.0)), fov=24)]),"""

# 030
old_030 = """    dict(shot="030", start=2.252, dur=0.375, play={"Thanos": "030_thanos"},
         note="medium close, head to chest, slightly low; Thanos on the left third, hand on screen-right; he looks up",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-1.4, -0.4, -9.8)), look=('Thanos.UpperTorso', (0.7, 0.5, 0)), fov=30),
              dict(t=0.375, pos=('Thanos.HumanoidRootPart', (-1.35, -0.4, -9.5)), look=('Thanos.UpperTorso', (0.7, 0.5, 0)), fov=30)]),"""

new_030 = """    dict(shot="030", start=2.252, dur=0.375, play={"Thanos": "030_thanos"},
         note="medium close, head to chest, slightly low; Thanos on the left third, hand on screen-right; he looks up",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-0.6, -0.8, -12.5)), look=('Thanos.UpperTorso', (1.2, 0.6, 0)), fov=29),
              dict(t=0.375, pos=('Thanos.HumanoidRootPart', (-0.55, -0.8, -12.2)), look=('Thanos.UpperTorso', (1.2, 0.6, 0)), fov=29)]),"""

# 040
old_040 = """    dict(shot="040", hide="Thanos", start=2.628, dur=1.168, play={"IronMan": "040_ironman", "Thanos": "040_thanos"},
         note="wide aerial shot looking up at Titan sky, Iron Man streaking horizontally across upper-left sky",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -25.0)), look=('Thanos.HumanoidRootPart', (-4.0, 16.0, 5.0)), fov=34),
              dict(t=1.168, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -25.0)), look=('Thanos.HumanoidRootPart', (-4.0, 16.0, 5.0)), fov=34)]),"""

new_040 = """    dict(shot="040", hide="Thanos", start=2.628, dur=1.168, play={"IronMan": "040_ironman", "Thanos": "040_thanos"},
         note="wide aerial shot looking up at Titan sky, Iron Man streaking horizontally across upper-left sky",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -22.0)), look=('Thanos.HumanoidRootPart', (-2.0, 10.0, 5.0)), fov=34),
              dict(t=1.168, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -22.0)), look=('Thanos.HumanoidRootPart', (-2.0, 10.0, 5.0)), fov=34)]),"""

assert old_020 in text, "old_020 not found"
assert old_030 in text, "old_030 not found"
assert old_040 in text, "old_040 not found"

text = text.replace(old_020, new_020).replace(old_030, new_030).replace(old_040, new_040)

with open("roblox_pipeline/scene.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated 020, 030, 040 camera setups in scene.py!")
