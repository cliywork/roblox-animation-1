import sys
sys.path.insert(0, "roblox_pipeline")

with open("roblox_pipeline/scene.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace Chunk 1 shots: 010, 020, 030, 040, 050, 070, 090
chunk1_old = """    dict(shot="010", start=0.000, dur=0.834, play={"Thanos": "010_thanos"},
         note="Thanos medium-wide, frontal, low angle; crops at upper thighs, raises the gauntlet",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-0.75, 0.4, -10.8)), look=('Thanos.UpperTorso', (-0.15, 0.35, 0)), fov=27),
              dict(t=0.834, pos=('Thanos.HumanoidRootPart', (-0.7, 0.4, -10.5)), look=('Thanos.UpperTorso', (-0.15, 0.35, 0)), fov=27)]),
    dict(shot="020", start=0.834, dur=1.418, play={"Thanos": "020_thanos"},
         note="close-up on the gauntlet; shoulder on left edge, arm extends to center, palm open with sunburst; pulled back to avoid mesh clip",
         cam=[dict(t=0.000, pos=('Thanos.LeftHand', (-4.2, 0.5, -6.8)), look=('Thanos.LeftHand', (0.2, 0.1, 0.2)), fov=26),
              dict(t=1.418, pos=('Thanos.LeftHand', (-3.9, 0.5, -6.2)), look=('Thanos.LeftHand', (0.2, 0.1, 0.2)), fov=26)]),
    dict(shot="030", start=2.252, dur=0.375, play={"Thanos": "030_thanos"},
         note="medium close, head to chest, slightly low; Thanos on the left third, hand on screen-right; he looks up",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-1.8, 1.1, -9.5)), look=('Thanos.UpperTorso', (0.8, 0.8, 0)), fov=30),
              dict(t=0.375, pos=('Thanos.HumanoidRootPart', (-1.7, 1.1, -9.2)), look=('Thanos.UpperTorso', (0.8, 0.8, 0)), fov=30)]),
    dict(shot="040", hide="Thanos", start=2.628, dur=1.168, play={"IronMan": "040_ironman", "Thanos": "040_thanos"},
         note="wide aerial shot looking up at Titan sky, Iron Man streaking horizontally across upper-left sky",
         cam=[dict(t=0.000, pos=('IronMan.HumanoidRootPart', (3.0, 1.0, -32)), look=('IronMan.HumanoidRootPart', (-3.0, 20.0, 0)), fov=32),
              dict(t=1.168, pos=('IronMan.HumanoidRootPart', (3.0, 1.0, -32)), look=('IronMan.HumanoidRootPart', (-1.0, 4.0, 0)), fov=30)]),
    dict(shot="050", start=3.795, dur=2.085, play={"IronMan": "050_ironman"},
         note="wide battlefield shot from distance (~28 studs, IM 25-30% height), dollying in to medium cowboy thigh-up stance",
         cam=[dict(t=0.000, pos=('IronMan.HumanoidRootPart', (2.2, 0.2, 29.0)), look=('IronMan.UpperTorso', (-0.8, 0.4, 0)), fov=31),
              dict(t=2.085, pos=('IronMan.HumanoidRootPart', (1.0, 0.1, 13.0)), look=('IronMan.UpperTorso', (-0.3, 0.3, 0)), fov=29)]),
    dict(shot="060", hud="mask", hide="Thanos", face={'dist': 2.5, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=5.881, dur=1.960, play={"IronMan": "060_ironman"},
         note="close-up, Iron Man's face square-on; fills ~65% frame height inside HUD",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.5)), look=('IronMan.Head', (0, -0.15, 0)), fov=26),
              dict(t=1.960, pos=('IronMan.Head', (0, 0.0, 2.45)), look=('IronMan.Head', (0, -0.15, 0)), fov=26)]),
    dict(shot="070", start=7.841, dur=1.335, play={"Thanos": "070_thanos"},
         note="close-up, head + armoured shoulders, head just left of centre (~45%); 'Stark'",
         cam=[dict(t=0.000, pos=('Thanos.Head', (0.15, -0.05, -4.2)), look=('Thanos.Head', (0.35, -0.25, 0)), fov=29),
              dict(t=1.335, pos=('Thanos.Head', (0.15, -0.05, -4.1)), look=('Thanos.Head', (0.35, -0.25, 0)), fov=29)]),
    dict(shot="080", hud="mask", hide="Thanos", face={'dist': 2.5, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=9.176, dur=1.251, play={"IronMan": "080_ironman"},
         note="a touch tighter than 060, eyes high; 'You know me'",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, -0.2, 0)), fov=30),
              dict(t=1.251, pos=('IronMan.Head', (0, 0.0, 2.55)), look=('IronMan.Head', (0, -0.2, 0)), fov=30)]),
    dict(shot="090", start=10.427, dur=5.422, play={"Thanos": "090_thanos"},
         note="close-up, head slightly left of centre, slow dolly push-in 0.8 studs through the line",
         cam=[dict(t=0.000, pos=('Thanos.Head', (0.15, -0.05, -4.2)), look=('Thanos.Head', (0.35, -0.25, 0)), fov=29),
              dict(t=5.422, pos=('Thanos.Head', (0.12, -0.05, -3.4)), look=('Thanos.Head', (0.35, -0.25, 0)), fov=29)]),"""

chunk1_new = """    dict(shot="010", start=0.000, dur=0.834, play={"Thanos": "010_thanos"},
         note="Thanos medium-wide, frontal, low angle; crops at upper thighs, raises the gauntlet",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-0.35, -0.7, -17.5)), look=('Thanos.UpperTorso', (0.0, 0.3, 0)), fov=28),
              dict(t=0.834, pos=('Thanos.HumanoidRootPart', (-0.3, -0.65, -17.2)), look=('Thanos.UpperTorso', (0.0, 0.3, 0)), fov=28)]),
    dict(shot="020", start=0.834, dur=1.418, play={"Thanos": "020_thanos"},
         note="close-up on the gauntlet; shoulder on left edge, arm extends to center, palm open with sunburst; pulled back to avoid mesh clip",
         cam=[dict(t=0.000, pos=('Thanos.LeftUpperArm', (-2.4, 0.1, 2.8)), look=('Thanos.LeftHand', (0.0, 0.15, -0.2)), fov=25),
              dict(t=1.418, pos=('Thanos.LeftUpperArm', (-2.0, 0.1, 2.5)), look=('Thanos.LeftHand', (0.1, 0.15, -0.2)), fov=25)]),
    dict(shot="030", start=2.252, dur=0.375, play={"Thanos": "030_thanos"},
         note="medium close, head to chest, slightly low; Thanos on the left third, hand on screen-right; he looks up",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (-1.4, -0.4, -9.8)), look=('Thanos.UpperTorso', (0.7, 0.5, 0)), fov=30),
              dict(t=0.375, pos=('Thanos.HumanoidRootPart', (-1.35, -0.4, -9.5)), look=('Thanos.UpperTorso', (0.7, 0.5, 0)), fov=30)]),
    dict(shot="040", hide="Thanos", start=2.628, dur=1.168, play={"IronMan": "040_ironman", "Thanos": "040_thanos"},
         note="wide aerial shot looking up at Titan sky, Iron Man streaking horizontally across upper-left sky",
         cam=[dict(t=0.000, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -25.0)), look=('Thanos.HumanoidRootPart', (-4.0, 16.0, 5.0)), fov=34),
              dict(t=1.168, pos=('Thanos.HumanoidRootPart', (0.0, -1.0, -25.0)), look=('Thanos.HumanoidRootPart', (-4.0, 16.0, 5.0)), fov=34)]),
    dict(shot="050", start=3.795, dur=2.085, play={"IronMan": "050_ironman"},
         note="wide battlefield shot from distance (~28 studs, IM 25-30% height), dollying in to medium cowboy thigh-up stance",
         cam=[dict(t=0.000, pos=('IronMan.HumanoidRootPart', (0.8, -0.4, 18.0)), look=('IronMan.UpperTorso', (0.0, 0.2, 0)), fov=29),
              dict(t=2.085, pos=('IronMan.HumanoidRootPart', (0.1, -0.4, 9.8)), look=('IronMan.UpperTorso', (0.0, 0.2, 0)), fov=28)]),
    dict(shot="060", hud="mask", hide="Thanos", face={'dist': 2.5, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=5.881, dur=1.960, play={"IronMan": "060_ironman"},
         note="close-up, Iron Man's face square-on; fills ~65% frame height inside HUD",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.5)), look=('IronMan.Head', (0, -0.15, 0)), fov=26),
              dict(t=1.960, pos=('IronMan.Head', (0, 0.0, 2.45)), look=('IronMan.Head', (0, -0.15, 0)), fov=26)]),
    dict(shot="070", start=7.841, dur=1.335, play={"Thanos": "070_thanos"},
         note="close-up, head + armoured shoulders, head just left of centre (~45%); 'Stark'",
         cam=[dict(t=0.000, pos=('Thanos.Head', (0.05, -0.15, -5.2)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=28),
              dict(t=1.335, pos=('Thanos.Head', (0.05, -0.15, -5.0)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=28)]),
    dict(shot="080", hud="mask", hide="Thanos", face={'dist': 2.5, 'yaw': 0, 'pitch': -3, 'roll': 0}, start=9.176, dur=1.251, play={"IronMan": "080_ironman"},
         note="a touch tighter than 060, eyes high; 'You know me'",
         cam=[dict(t=0.000, pos=('IronMan.Head', (0, 0.0, 2.6)), look=('IronMan.Head', (0, -0.2, 0)), fov=30),
              dict(t=1.251, pos=('IronMan.Head', (0, 0.0, 2.55)), look=('IronMan.Head', (0, -0.2, 0)), fov=30)]),
    dict(shot="090", start=10.427, dur=5.422, play={"Thanos": "090_thanos"},
         note="close-up, head slightly left of centre, slow dolly push-in 0.8 studs through the line",
         cam=[dict(t=0.000, pos=('Thanos.Head', (0.05, -0.15, -5.2)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=28),
              dict(t=5.422, pos=('Thanos.Head', (0.05, -0.1, -4.2)), look=('Thanos.Head', (0.2, 0.05, 0)), fov=27)]),"""

assert chunk1_old in content, "chunk1_old not found in scene.py"
content = content.replace(chunk1_old, chunk1_new, 1)

with open("roblox_pipeline/scene.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated Chunk 1 camera setups in roblox_pipeline/scene.py!")
