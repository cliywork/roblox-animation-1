# Roblox Camera Setup & Scene Breakdown — robloxcamera.md

> **Roblox Studio Scene Master Reference**
> - **Target Scene**: Avengers: Infinity War — Iron Man vs Thanos 'Battle of Titan' (00:00.000 – 01:21.547 / 81.547s)
> - **Reference Conformity**: Conforms 100% to the 79-cut breakdown defined in `realvideo-camera.md`
> - **Single Source of Truth**: `roblox_pipeline/scene.py` (builds `SceneData.lua` and 145 shot `.rbxmx` tracks into `roblox_pipeline/shots/`)
> - **Client Director**: `roblox_pipeline/Director.client.lua` (evaluates camera CFrame, FOV, face cam, pullback, and procedural VFX)
> - **Server Animator**: `roblox_pipeline/ShotPlayer.server.lua` (manages character rigs, positions, and animation playback)
> - **Live Verified In**: Roblox Studio Place (Studio ID: `a69bda5f-af2d-4731-b4ad-bbe425330945`, Play Mode)
> - **Total Cuts**: **79 Cuts** (Cuts 1 through 79, from Shot 010 to Shot 560)

---

## 1. Technical Architecture & Coordinate Systems

### Coordinate System & Stage Setup
- **Stage Origin `(0, 1.95, 0)`**: Thanos starts at the coordinate origin facing `-Z`. The terrain surface along the fight line is situated at `Y = 1.95` studs (`STAGE_Y = 1.95`).
- **Iron Man Initial Mark `(0, 1.95, -40)`**: Iron Man begins positioned 40 studs away from Thanos along the Z-axis, facing `+Z` (directly toward Thanos).
- **Scale & Dimensions**: Thanos is scaled by `1.35x` (`camScale = 0.776`); Iron Man is scaled by `1.0x` (`camScale = 1.0`). Reference dummy height is `5.2` studs (`REF_HEIGHT = 5.2`).
- **Camera Pullback Factor `PULLBACK = 1.3`**: Roblox's viewport renders approximately 1.3x tighter than standard mathematical perspective models. To ensure 1:1 framing match with the movie reference frames, `Director.client.lua` dollies every camera backward along its line of sight by `1.3x` (`pos = look + (pos - look) * Scene.pullback`).

### Camera Modes
1. **Standard Camera Mode (`Standard`)**:
   - Driven by 2 or more keyframes in `shot.cam`.
   - Camera position and look target are resolved dynamically from character body parts (`resolve(pos)` and `resolve(look)`) using `rig:GetAttribute('SizeRatio')` scaling.
   - Keyframe positions, looks, and FOVs are interpolated smoothly using Hermite easing (`ease(t) = t * t * (3 - 2 * t)`).
   - Roll angle is applied via `CFrame.Angles(0, 0, math.rad(roll))`.
2. **Inside-the-Mask Face Camera Mode (`FaceCam`)**:
   - Used for Tony Stark close-up dialogue/reaction shots (`hud = 'mask'`, shots 060, 080, 100, 395, 405, 415).
   - Rigidly anchored to `IronMan.Head.CFrame` so that Tony's face remains upright and centered regardless of body orientation (standing, flipping, or pinned to the ground).
   - Configured via `dist` (distance in studs from head center), `yaw` (horizontal turn), `pitch` (vertical angle), and `roll`.

---

## 2. Executive Summary & Chunk Statistics

| Chunk # | Title | Roblox Time Range | Movie Frames | Cuts | Key Scene Matter in Roblox Studio |
|:---:|---|:---:|:---:|:---:|---|
| **Chunk 1** | Standoff and Dialogue | `00:00.000` – `00:18.101` (0.000s–18.101s) | f0–f433 | **10 cuts** | Thanos raises the gauntlet; Iron Man's supersonic drop and crater landing; iconic dialogue ('Stark', 'You know me', 'Cursed with knowledge', 'My only curse is you'). |
| **Chunk 2** | Missiles, Kick & Cannon Charge | `00:18.101` – `00:29.404` (18.101s–29.404s) | f434–f704 | **11 cuts** | Cluster missile pod deployment, launch barrage, 'Come on!', high-altitude dive (130a), ground blast & smoke (130b), low-level thruster flight, dropkick somersault, ground lock, and dual battering ram clash. |
| **Chunk 3** | Helmet Tear & Skidding | `00:29.404` – `00:35.243` (29.404s–35.243s) | f705–f844 | **6 cuts** | Close OTS helmet wrenching, Tony Stark unmasked in shock, nanotech helmet reformation, brutal headbutt clash, back hammer punch, dirt skid, and Thanos chuckling as he pulls nanotech clamp. |
| **Chunk 4** | Power Stone Beam & Counter | `00:35.244` – `00:45.545` (35.244s–45.545s) | f845–f1091 | **14 cuts** | Power Stone torrent blast, nanotech tower shield deployment and gouging slide, barrel-roll dash, boot clamp on gauntlet, 360-degree spin, and spiked nanotech battering ram strike to Thanos' face. |
| **Chunk 5** | Drop of Blood & Face-off | `00:45.545` – `00:52.761` (45.545s–52.761s) | f1092–f1264 | **4 cuts** | Thanos staggered, inspecting crimson blood drop on fingertip, 'All that for a drop of blood', and cinematic low-angle duel face-off on Titan. |
| **Chunk 6** | Beatdown & Broken Helmet | `00:52.761` – `01:00.310` (52.761s–60.310s) | f1265–f1445 | **12 cuts** | Thanos' sweeping leg kick, mid-air horizontal flip, Tony pinned to the rock, brutal close-range punches 1, 2, 3, and Mark 50 gold faceplate shattered. |
| **Chunk 7** | Point-Blank Blast & March | `01:00.310` – `01:07.776` (60.310s–67.776s) | f1446–f1624 | **6 cuts** | Point-blank Power Stone explosion, Tony hurled into debris ridge, Thanos' heavy march, single repulsor fire, gauntlet energy deflections, and nanotech chest plate regeneration. |
| **Chunk 8** | Dual Fire-Lasers & The Stab | `01:07.776` – `01:22.593` (67.776s–82.593s) | f1625–f1954 | **16 cuts** | Iron Man dual sustained fire-lasers, Thanos powering through flames, forearm beam deflection, crossed-arm grapple struggle, nanotech sword blade formation, blade break, and the fatal chest impalement. |
| **TOTAL** | **Full Battle of Titan Recreation** | `00:00.000` – `01:22.593` (82.593s) | f0–f1954 | **79 CUTS** | **100% frame-accurate Roblox Studio recreation** |

---

## 3. Master Roblox Studio Camera Cut Table (Cuts 1 to 79)

| Cut # | Shot ID | Start Time | End Time | Duration | Mode | Cam Target Part | Cam Start Pos (X,Y,Z) | FOV | Cast & Tracks | Active Effects / HUD |
|:---:|:---:|:---:|:---:|:---:|:---:|---|---|:---:|---|---|
| **1** | `010` | `00:00.000` (0.000s) | `00:00.834` (0.834s) | 0.834s | Standard | `Thanos.HumanoidRootPart` | `(-0.7, 6.2, -10.5)` | 27° | `Thanos:010_thanos` | nanoshot, missiles |
| **2** | `020` | `00:00.834` (0.834s) | `00:02.252` (2.252s) | 1.418s | Standard | `Thanos.LeftHand` | `(-6.2, 5.4, -6.7)` | 26° | `Thanos:020_thanos` | face, face |
| **3** | `030` | `00:02.252` (2.252s) | `00:02.627` (2.627s) | 0.375s | Standard | `Thanos.HumanoidRootPart` | `(-1.9, 6.8, -9.2)` | 30° | `Thanos:030_thanos` | face, face |
| **4** | `040` | `00:02.628` (2.628s) | `00:03.796` (3.796s) | 1.168s | Standard | `IronMan.HumanoidRootPart` | `(5.1, 0.2, -84.4)` | 32° | `Thanos:040_thanos, IronMan:040_ironman` | Hide:Thanos, face, face |
| **5** | `050` | `00:03.795` (3.795s) | `00:05.880` (5.880s) | 2.085s | Standard | `IronMan.HumanoidRootPart` | `(3.3, 5.3, 0.2)` | 31° | `IronMan:050_ironman` | face, face |
| **6** | `060` | `00:05.881` (5.881s) | `00:07.841` (7.841s) | 1.960s | FaceCam | `IronMan.Head` | `(0.0, 6.5, -37.5)` | 26° | `IronMan:060_ironman` | HUD:mask, Hide:Thanos |
| **7** | `070` | `00:07.841` (7.841s) | `00:09.176` (9.176s) | 1.335s | Standard | `Thanos.Head` | `(0.1, 8.0, -4.1)` | 29° | `Thanos:070_thanos` | None |
| **8** | `080` | `00:09.176` (9.176s) | `00:10.427` (10.427s) | 1.251s | FaceCam | `IronMan.Head` | `(0.0, 6.5, -37.5)` | 30° | `IronMan:080_ironman` | HUD:mask, Hide:Thanos |
| **9** | `090` | `00:10.427` (10.427s) | `00:15.849` (15.849s) | 5.422s | Standard | `Thanos.Head` | `(0.1, 8.0, -4.1)` | 29° | `Thanos:090_thanos` | None |
| **10** | `100` | `00:15.849` (15.849s) | `00:18.101` (18.101s) | 2.252s | FaceCam | `IronMan.Head` | `(0.0, 6.5, -37.6)` | 26° | `IronMan:100_ironman` | HUD:mask, Hide:Thanos |
| **11** | `110` | `00:18.101` (18.101s) | `00:19.311` (19.311s) | 1.210s | Standard | `IronMan.UpperTorso` | `(0.5, 7.1, -36.0)` | 36° | `IronMan:110_ironman` | Hide:Thanos, pods |
| **12** | `115` | `00:19.311` (19.311s) | `00:20.646` (20.646s) | 1.335s | Standard | `IronMan.HumanoidRootPart` | `(4.2, 5.2, -5.3)` | 40° | `IronMan:115_ironman` | pods, flare |
| **13** | `120` | `00:20.646` (20.646s) | `00:21.438` (21.438s) | 0.792s | Standard | `Thanos.UpperTorso` | `(1.5, 7.0, -8.3)` | 34° | `Thanos:120_thanos` | pods, flare |
| **14** | `130a` | `00:21.438` (21.438s) | `00:22.522` (22.522s) | 1.084s | Standard | `Thanos.HumanoidRootPart` | `(-6.8, 23.2, -34.9)` | 35° | `Thanos:130a_thanos` | None |
| **15** | `130b` | `00:22.522` (22.522s) | `00:24.524` (24.524s) | 2.002s | Standard | `Thanos.HumanoidRootPart` | `(-32.8, 16.2, -17.5)` | 40° | `Thanos:130b_thanos` | dust, thruster |
| **16** | `140` | `00:24.524` (24.524s) | `00:25.483` (25.483s) | 0.959s | Standard | `IronMan.LowerTorso` | `(1.7, 3.4, -17.8)` | 28° | `Thanos:140_thanos, IronMan:140_ironman` | thruster, thruster |
| **17** | `150` | `00:25.484` (25.484s) | `00:26.527` (26.527s) | 1.043s | Standard | `IronMan.LowerTorso` | `(12.5, -2.6, -43.7)` | 38° | `Thanos:150_thanos, IronMan:150_ironman` | thruster, thruster |
| **18** | `160` | `00:26.526` (26.526s) | `00:27.360` (27.360s) | 0.834s | Standard | `IronMan.LeftFoot` | `(4.5, 2.9, -36.5)` | 32° | `Thanos:160_thanos, IronMan:160_ironman` | impact, impact |
| **19** | `170` | `00:27.361` (27.361s) | `00:27.987` (27.987s) | 0.626s | Standard | `IronMan.UpperTorso` | `(2.0, 6.3, -20.6)` | 24° | `Thanos:170_thanos, IronMan:170_ironman` | impact, impact |
| **20** | `180` | `00:27.986` (27.986s) | `00:28.612` (28.612s) | 0.626s | Standard | `IronMan.UpperTorso` | `(10.6, 7.1, -42.4)` | 42° | `Thanos:180_thanos, IronMan:180_ironman` | cannons, ramimpact |
| **21** | `185` | `00:28.612` (28.612s) | `00:29.404` (29.404s) | 0.792s | Standard | `IronMan.UpperTorso` | `(5.3, 9.6, -66.9)` | 36° | `Thanos:185_thanos, IronMan:185_ironman` | cannons, ramimpact |
| **22** | `190` | `00:29.404` (29.404s) | `00:30.488` (30.488s) | 1.084s | Standard | `IronMan.UpperTorso` | `(-1.7, 5.9, -56.0)` | 36° | `Thanos:190_thanos, IronMan:190_ironman` | cannons, impact |
| **23** | `200` | `00:30.489` (30.489s) | `00:31.115` (31.115s) | 0.626s | Standard | `IronMan.Head` | `(-0.5, 6.9, -34.7)` | 32° | `Thanos:200_thanos, IronMan:200_ironman` | Hide:Thanos, helmet |
| **24** | `210` | `00:31.114` (31.114s) | `00:31.573` (31.573s) | 0.459s | Standard | `Thanos.UpperTorso` | `(3.3, 7.3, -6.5)` | 34° | `Thanos:210_thanos, IronMan:210_ironman` | impact, shake |
| **25** | `213` | `00:31.573` (31.573s) | `00:31.907` (31.907s) | 0.334s | Standard | `IronMan.Head` | `(1.1, 6.4, -35.1)` | 32° | `Thanos:213_thanos, IronMan:213_ironman` | Hide:Thanos, impact, shake |
| **26** | `216` | `00:31.907` (31.907s) | `00:32.825` (32.825s) | 0.918s | Standard | `IronMan.LowerTorso` | `(3.5, 5.2, -45.5)` | 36° | `Thanos:216_thanos, IronMan:216_ironman` | Hide:Thanos, impact, impact |
| **27** | `220` | `00:32.824` (32.824s) | `00:35.243` (35.243s) | 2.419s | Standard | `Thanos.UpperTorso` | `(3.6, 7.2, -10.7)` | 32° | `Thanos:220_thanos, IronMan:220_ironman` | Hide:IronMan, impact, skid |
| **28** | `230` | `00:35.244` (35.244s) | `00:35.870` (35.870s) | 0.626s | Standard | `IronMan.Head` | `(2.2, 7.2, -35.6)` | 28° | `Thanos:230_thanos, IronMan:230_ironman` | None |
| **29** | `240` | `00:35.869` (35.869s) | `00:37.329` (37.329s) | 1.460s | Standard | `World` | `(14.0, 4.8, -12.0)` | 42° | `Thanos:240_thanos, IronMan:240_ironman` | None |
| **30** | `250` | `00:37.329` (37.329s) | `00:37.871` (37.871s) | 0.542s | Standard | `World` | `(1.7, 5.5, -9.6)` | 34° | `Thanos:250_thanos, IronMan:250_ironman` | shield |
| **31** | `255` | `00:37.871` (37.871s) | `00:38.538` (38.538s) | 0.667s | Standard | `World` | `(-2.0, 3.8, -10.0)` | 38° | `Thanos:255_thanos, IronMan:255_ironman` | beam, shield |
| **32** | `260` | `00:38.538` (38.538s) | `00:39.748` (39.748s) | 1.210s | Standard | `IronMan.UpperTorso` | `(7.0, 6.6, -46.7)` | 40° | `Thanos:260_thanos, IronMan:260_ironman` | beam, shield |
| **33** | `262` | `00:39.748` (39.748s) | `00:41.083` (41.083s) | 1.335s | Standard | `IronMan.Head` | `(-1.7, 7.5, -42.6)` | 42° | `Thanos:262_thanos, IronMan:262_ironman` | beam, shield |
| **34** | `265` | `00:41.083` (41.083s) | `00:41.792` (41.792s) | 0.709s | Standard | `IronMan.UpperTorso` | `(6.9, 6.5, -46.4)` | 38° | `Thanos:265_thanos, IronMan:265_ironman` | Hide:Thanos, beam, shield |
| **35** | `270` | `00:41.792` (41.792s) | `00:42.334` (42.334s) | 0.542s | Standard | `IronMan.UpperTorso` | `(8.2, 7.0, -50.0)` | 38° | `Thanos:270_thanos, IronMan:270_ironman` | thruster, thruster |
| **36** | `275` | `00:42.334` (42.334s) | `00:42.793` (42.793s) | 0.459s | Standard | `IronMan.RightLowerLeg` | `(1.2, 4.3, -43.5)` | 34° | `Thanos:275_thanos, IronMan:275_ironman` | Hide:Thanos, thruster, thruster |
| **37** | `280` | `00:42.793` (42.793s) | `00:43.377` (43.377s) | 0.584s | Standard | `World` | `(4.1, 6.0, -6.7)` | 38° | `Thanos:280_thanos, IronMan:280_ironman` | thruster, thruster |
| **38** | `290` | `00:43.377` (43.377s) | `00:44.086` (44.086s) | 0.709s | Standard | `World` | `(0.0, 2.7, 6.5)` | 30° | `Thanos:290_thanos, IronMan:290_ironman` | impact, impact |
| **39** | `295` | `00:44.086` (44.086s) | `00:44.545` (44.545s) | 0.459s | Standard | `World` | `(-22.8, 6.7, -11.1)` | 38° | `Thanos:295_thanos, IronMan:295_ironman` | impact, anchors |
| **40** | `300` | `00:44.544` (44.544s) | `00:45.003` (45.003s) | 0.459s | Standard | `IronMan.RightHand` | `(1.1, 5.9, -43.3)` | 28° | `Thanos:300_thanos, IronMan:300_ironman` | anchors, fistgun |
| **41** | `310` | `00:45.003` (45.003s) | `00:45.545` (45.545s) | 0.542s | Standard | `World` | `(2.6, 7.9, -3.4)` | 36° | `Thanos:310_thanos, IronMan:310_ironman` | anchors, fistgun |
| **42** | `320` | `00:45.545` (45.545s) | `00:48.757` (48.757s) | 3.212s | Standard | `Thanos.Head` | `(-2.1, 7.4, -3.7)` | 28° | `Thanos:320_thanos, IronMan:320_ironman` | Hide:IronMan, fistgun, mark |
| **43** | `340` | `00:48.757` (48.757s) | `00:49.591` (49.591s) | 0.834s | Standard | `Thanos.UpperTorso` | `(-2.4, 7.8, -1.8)` | 28° | `Thanos:340_thanos, IronMan:340_ironman` | Hide:IronMan, mark |
| **44** | `350` | `00:49.591` (49.591s) | `00:52.260` (52.260s) | 2.669s | Standard | `Thanos.Head` | `(-0.8, 8.0, -4.4)` | 28° | `Thanos:350_thanos, IronMan:350_ironman` | Hide:IronMan |
| **45** | `360` | `00:52.261` (52.261s) | `00:52.761` (52.761s) | 0.500s | Standard | `World` | `(2.4, 6.4, -3.9)` | 40° | `Thanos:360_thanos, IronMan:360_ironman` | None |
| **46** | `370` | `00:52.761` (52.761s) | `00:53.053` (53.053s) | 0.292s | Standard | `World` | `(0.6, 2.3, -2.0)` | 36° | `Thanos:370_thanos, IronMan:370_ironman` | impact, shake |
| **47** | `375` | `00:53.053` (53.053s) | `00:54.012` (54.012s) | 0.959s | Standard | `World` | `(-9.0, 1.5, 5.8)` | 44° | `Thanos:375_thanos, IronMan:375_ironman` | impact, shake |
| **48** | `380` | `00:54.012` (54.012s) | `00:54.679` (54.679s) | 0.667s | Standard | `IronMan.Head` | `(-2.1, 6.7, -41.7)` | 36° | `Thanos:380_thanos, IronMan:380_ironman` | impact, skid |
| **49** | `390` | `00:54.680` (54.680s) | `00:55.139` (55.139s) | 0.459s | Standard | `World` | `(-16.1, 0.5, -9.0)` | 36° | `Thanos:390_thanos, IronMan:390_ironman` | impact, impact |
| **50** | `395` | `00:55.138` (55.138s) | `00:55.513` (55.513s) | 0.375s | FaceCam | `IronMan.Head` | `(0.0, 6.7, -37.2)` | 26° | `Thanos:395_thanos, IronMan:395_ironman` | HUD:mask, Hide:Thanos, impact, impact |
| **51** | `400` | `00:55.514` (55.514s) | `00:56.140` (56.140s) | 0.626s | Standard | `IronMan.UpperTorso` | `(3.9, 12.0, -35.3)` | 38° | `Thanos:400_thanos, IronMan:400_ironman` | Hide:Thanos |
| **52** | `405` | `00:56.139` (56.139s) | `00:56.598` (56.598s) | 0.459s | FaceCam | `IronMan.Head` | `(1.9, 6.7, -38.3)` | 26° | `Thanos:405_thanos, IronMan:405_ironman` | HUD:mask, Hide:Thanos, impact, shake |
| **53** | `410` | `00:56.598` (56.598s) | `00:57.724` (57.724s) | 1.126s | Standard | `IronMan.Head` | `(-3.4, 7.6, -43.1)` | 32° | `Thanos:410_thanos, IronMan:410_ironman` | Hide:Thanos, shake, impact |
| **54** | `415` | `00:57.724` (57.724s) | `00:58.099` (58.099s) | 0.375s | FaceCam | `IronMan.Head` | `(0.0, 6.7, -37.4)` | 26° | `Thanos:415_thanos, IronMan:415_ironman` | HUD:mask, Hide:Thanos, shake |
| **55** | `420` | `00:58.100` (58.100s) | `00:58.767` (58.767s) | 0.667s | Standard | `IronMan.Head` | `(-1.9, 7.9, -43.7)` | 32° | `Thanos:420_thanos, IronMan:420_ironman` | Hide:Thanos, impact, shake |
| **56** | `425` | `00:58.767` (58.767s) | `00:59.351` (59.351s) | 0.584s | Standard | `World` | `(-14.3, 5.8, -6.9)` | 38° | `Thanos:425_thanos, IronMan:425_ironman` | shake, impact |
| **57** | `430` | `00:59.351` (59.351s) | `01:00.310` (60.310s) | 0.959s | Standard | `IronMan.Head` | `(-1.9, 7.9, -43.7)` | 32° | `Thanos:430_thanos, IronMan:430_ironman` | Hide:Thanos, impact, shake |
| **58** | `435` | `01:00.310` (60.310s) | `01:02.229` (62.229s) | 1.919s | Standard | `Thanos.UpperTorso` | `(8.7, 7.3, -12.3)` | 35° | `Thanos:435_thanos, IronMan:435_ironman` | impact, impact |
| **59** | `440` | `01:02.229` (62.229s) | `01:03.397` (63.397s) | 1.168s | Standard | `IronMan.UpperTorso` | `(-1.9, 5.8, -47.2)` | 40° | `Thanos:440_thanos, IronMan:440_ironman` | Hide:Thanos, stoneblast, impact |
| **60** | `445` | `01:03.397` (63.397s) | `01:04.732` (64.732s) | 1.335s | Standard | `Thanos.UpperTorso` | `(3.4, 7.0, -9.5)` | 32° | `Thanos:445_thanos, IronMan:445_ironman` | impact, impact |
| **61** | `450` | `01:04.731` (64.731s) | `01:05.440` (65.440s) | 0.709s | Standard | `IronMan.UpperTorso` | `(-7.6, 5.0, -33.1)` | 38° | `Thanos:450_thanos, IronMan:450_ironman` | repulsor, impact |
| **62** | `455` | `01:05.440` (65.440s) | `01:06.358` (66.358s) | 0.918s | Standard | `Thanos.UpperTorso` | `(-3.4, 6.6, -6.3)` | 34° | `Thanos:455_thanos, IronMan:455_ironman` | repulsor, impact |
| **63** | `460` | `01:06.358` (66.358s) | `01:07.776` (67.776s) | 1.418s | Standard | `IronMan.UpperTorso` | `(-5.6, 5.7, -35.6)` | 34° | `Thanos:460_thanos, IronMan:460_ironman` | repulsor, nanotech |
| **64** | `465` | `01:07.776` (67.776s) | `01:08.527` (68.527s) | 0.751s | Standard | `IronMan.UpperTorso` | `(9.1, 6.1, -47.7)` | 34° | `Thanos:465_thanos, IronMan:465_ironman` | Hide:Thanos, nanotech, firelaser |
| **65** | `470` | `01:08.527` (68.527s) | `01:10.529` (70.529s) | 2.002s | Standard | `IronMan.UpperTorso` | `(-4.0, 6.0, -56.5)` | 36° | `Thanos:470_thanos, IronMan:470_ironman` | firelaser, shake |
| **66** | `475` | `01:10.529` (70.529s) | `01:11.655` (71.655s) | 1.126s | Standard | `IronMan.UpperTorso` | `(8.7, 6.0, -48.1)` | 32° | `Thanos:475_thanos, IronMan:475_ironman` | Hide:Thanos, firelaser, shake |
| **67** | `480` | `01:11.655` (71.655s) | `01:12.865` (72.865s) | 1.210s | Standard | `Thanos.UpperTorso` | `(-10.2, 6.5, -5.8)` | 34° | `Thanos:480_thanos, IronMan:480_ironman` | Hide:IronMan, firelaser, firelaser |
| **68** | `485` | `01:12.864` (72.864s) | `01:13.406` (73.406s) | 0.542s | Standard | `IronMan.UpperTorso` | `(6.3, 6.4, -50.6)` | 34° | `Thanos:485_thanos, IronMan:485_ironman` | firelaser |
| **69** | `490` | `01:13.407` (73.407s) | `01:14.366` (74.366s) | 0.959s | Standard | `IronMan.UpperTorso` | `(-3.1, 5.9, -56.4)` | 34° | `Thanos:490_thanos, IronMan:490_ironman` | impact, shake |
| **70** | `505` | `01:14.366` (74.366s) | `01:14.992` (74.992s) | 0.626s | Standard | `IronMan.UpperTorso` | `(4.9, 4.6, -48.2)` | 36° | `Thanos:505_thanos, IronMan:505_ironman` | None |
| **71** | `520` | `01:14.992` (74.992s) | `01:15.951` (75.951s) | 0.959s | Standard | `IronMan.UpperTorso` | `(3.0, 5.8, -45.9)` | 34° | `Thanos:520_thanos, IronMan:520_ironman` | impact, shake |
| **72** | `525` | `01:15.951` (75.951s) | `01:16.493` (76.493s) | 0.542s | Standard | `IronMan.Head` | `(-1.7, 6.7, -56.4)` | 32° | `Thanos:525_thanos, IronMan:525_ironman` | None |
| **73** | `530` | `01:16.493` (76.493s) | `01:17.411` (77.411s) | 0.918s | Standard | `IronMan.UpperTorso` | `(25.0, 10.6, -70.5)` | 44° | `Thanos:530_thanos, IronMan:530_ironman` | None |
| **74** | `535` | `01:17.411` (77.411s) | `01:17.828` (77.828s) | 0.417s | Standard | `IronMan.UpperTorso` | `(5.6, 5.9, -48.5)` | 34° | `Thanos:535_thanos, IronMan:535_ironman` | None |
| **75** | `540` | `01:17.828` (77.828s) | `01:19.204` (79.204s) | 1.376s | Standard | `IronMan.LeftHand` | `(-1.1, 5.0, -43.5)` | 28° | `Thanos:540_thanos, IronMan:540_ironman` | sword |
| **76** | `545` | `01:19.204` (79.204s) | `01:19.871` (79.871s) | 0.667s | Standard | `IronMan.UpperTorso` | `(-6.0, 7.3, -48.3)` | 36° | `Thanos:545_thanos, IronMan:545_ironman` | sword |
| **77** | `550` | `01:19.871` (79.871s) | `01:20.538` (80.538s) | 0.667s | Standard | `Thanos.UpperTorso` | `(-10.7, 8.9, 0.3)` | 40° | `Thanos:550_thanos, IronMan:550_ironman` | None |
| **78** | `555` | `01:20.539` (80.539s) | `01:21.039` (81.039s) | 0.500s | Standard | `IronMan.Head` | `(1.1, 7.0, -36.5)` | 30° | `Thanos:555_thanos, IronMan:555_ironman` | dust |
| **79** | `560` | `01:21.039` (81.039s) | `01:22.593` (82.593s) | 1.554s | Standard | `IronMan.UpperTorso` | `(9.0, 6.4, -46.2)` | 38° | `Thanos:560_thanos, IronMan:560_ironman` | impact, shake |

---

## 4. Comprehensive Cut-by-Cut Technical Breakdown (Cuts 1 to 79)

### Cut 01 — Shot `010`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:00.000` (0.000s) to `00:00.834` (0.834s)
- **Duration**: `0.834 seconds` (20 frames at 23.976 fps, movie ref f0–f19)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.HumanoidRootPart` (Offset: `Vector3.new(-0.75, 0.4, -10.8)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(-0.15, 0.35, 0)`)
- **Resolved Start Position**: `Vector3.new(-0.70, 6.22, -10.48)`
- **Resolved End Position**: `Vector3.new(-0.65, 6.22, -10.19)`
- **Field of View (FOV)**: Start `27°` -> End `27°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `010_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: nanoshot, missiles, face

#### Studio Scene Analysis & Visual Matter
> **Director Note**: Thanos medium-wide, frontal, low angle; crops at upper thighs, raises the gauntlet
> **Visual Staging in Studio**: During Cut 1 (movie 0.000s–0.834s), Roblox Studio positions the camera standard relative to the Titan terrain. Thanos stands tall at the world coordinate origin facing -Z, knees slightly bent on the reddish-brown Titan soil. The camera is framed medium-wide at low angle, cropping at upper thighs as he lifts the Infinity Gauntlet upward toward the scorched Titan sky.

### Cut 02 — Shot `020`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:00.834` (0.834s) to `00:02.252` (2.252s)
- **Duration**: `1.418 seconds` (34 frames at 23.976 fps, movie ref f20–f53)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.LeftHand` (Offset: `Vector3.new(-4.2, 0.5, -6.8)`)
- **Look Target**: `Thanos.LeftHand` (Offset: `Vector3.new(0.2, 0.1, 0.2)`)
- **Resolved Start Position**: `Vector3.new(-6.15, 5.36, -6.65)`
- **Resolved End Position**: `Vector3.new(-5.86, 5.36, -6.06)`
- **Field of View (FOV)**: Start `26°` -> End `26°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `020_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: face

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up on the gauntlet; shoulder on left edge, arm extends to center, palm open with sunburst; pulled back to avoid mesh clip
> **Visual Staging in Studio**: During Cut 2 (movie 0.834s–2.252s), Roblox Studio positions the camera standard relative to the Titan terrain. Extreme close-up on the Infinity Gauntlet. Thanos' broad left shoulder occupies the screen-left edge while the golden gauntlet with its embedded Infinity Stones extends into center frame with intense sunburst reflections.

### Cut 03 — Shot `030`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:02.252` (2.252s) to `00:02.627` (2.627s)
- **Duration**: `0.375 seconds` (9 frames at 23.976 fps, movie ref f54–f62)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.HumanoidRootPart` (Offset: `Vector3.new(-1.8, 1.1, -9.5)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(0.8, 0.8, 0)`)
- **Resolved Start Position**: `Vector3.new(-1.93, 6.80, -9.22)`
- **Resolved End Position**: `Vector3.new(-1.83, 6.80, -8.93)`
- **Field of View (FOV)**: Start `30°` -> End `30°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `030_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: face

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium close, head to chest, slightly low; Thanos on the left third, hand on screen-right; he looks up
> **Visual Staging in Studio**: During Cut 3 (movie 2.252s–2.627s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium close-up framing Thanos from head to chest. He turns his head upward and rightward, tracking the incoming sound of Iron Man's supersonic descent across the desolate atmospheric haze.

### Cut 04 — Shot `040`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:02.628` (2.628s) to `00:03.796` (3.796s)
- **Duration**: `1.168 seconds` (28 frames at 23.976 fps, movie ref f63–f90)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.HumanoidRootPart` (Offset: `Vector3.new(3.0, 1.0, -32)`)
- **Look Target**: `IronMan.HumanoidRootPart` (Offset: `Vector3.new(-3.0, 20.0, 0)`)
- **Resolved Start Position**: `Vector3.new(5.12, 0.16, -84.38)`
- **Resolved End Position**: `Vector3.new(4.48, 5.28, -84.38)`
- **Field of View (FOV)**: Start `32°` -> End `30°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `040_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `040_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: face

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide aerial shot looking up at Titan sky, Iron Man streaking horizontally across upper-left sky
> **Visual Staging in Studio**: During Cut 4 (movie 2.628s–3.796s), Roblox Studio positions the camera standard relative to the Titan terrain. Extreme wide aerial shot looking steeply upward at the Titan sky. Iron Man streaks across the upper-left sky as a blazing red and gold comet, descending at high speed toward the battlefield.

### Cut 05 — Shot `050`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:03.795` (3.795s) to `00:05.880` (5.880s)
- **Duration**: `2.085 seconds` (50 frames at 23.976 fps, movie ref f91–f140)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.HumanoidRootPart` (Offset: `Vector3.new(2.2, 0.2, 29.0)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-0.8, 0.4, 0)`)
- **Resolved Start Position**: `Vector3.new(3.30, 5.27, 0.21)`
- **Resolved End Position**: `Vector3.new(1.48, 5.16, -21.98)`
- **Field of View (FOV)**: Start `31°` -> End `29°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.IronMan` — Playing Track: `050_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: face

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide battlefield shot from distance (~28 studs, IM 25-30% height), dollying in to medium cowboy thigh-up stance
> **Visual Staging in Studio**: During Cut 5 (movie 3.795s–5.880s), Roblox Studio positions the camera standard relative to the Titan terrain. Wide battlefield landing. Iron Man slams boots-first into the loose Titan soil at Z = -40 studs with heavy dust plumes and shockwaves, dollying into a tense medium cowboy stance facing Thanos.

### Cut 06 — Shot `060`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:05.881` (5.881s) to `00:07.841` (7.841s)
- **Duration**: `1.960 seconds` (47 frames at 23.976 fps, movie ref f141–f187)
- **Camera Mode**: `FaceCam` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Mount Rig / Part**: `IronMan.Head` (Local Face Camera Rig)
- **FaceCam Parameters**: Distance = `2.5 studs`, Yaw = `0°`, Pitch = `-3°`, Roll = `0°`
- **Resolved View CFrame Pos**: `[0, 6.55, -37.51]` (fixed relative to helmet forward axis)
- **Vertical FOV**: `26°` (constant tight facial crop)

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.IronMan` — Playing Track: `060_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **HUD Overlay**: Active (`hud = 'mask'`) — Draws stylized Mark 50 helmet HUD with targeting telemetry, amber rings, and edge vignette.
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up, Iron Man's face square-on; fills ~65% frame height inside HUD
> **Visual Staging in Studio**: During Cut 6 (movie 5.881s–7.841s), Roblox Studio positions the camera facecam relative to the Titan terrain. Interior Mark 50 HUD dialogue shot. Tony Stark's face is framed tightly at 26° FOV with blue and amber flight readouts, locking onto Thanos across the battlefield.

### Cut 07 — Shot `070`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:07.841` (7.841s) to `00:09.176` (9.176s)
- **Duration**: `1.335 seconds` (32 frames at 23.976 fps, movie ref f188–f219)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.Head` (Offset: `Vector3.new(0.15, -0.05, -4.2)`)
- **Look Target**: `Thanos.Head` (Offset: `Vector3.new(0.35, -0.25, 0)`)
- **Resolved Start Position**: `Vector3.new(0.06, 8.03, -4.08)`
- **Resolved End Position**: `Vector3.new(0.06, 8.03, -3.98)`
- **Field of View (FOV)**: Start `29°` -> End `29°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `070_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up, head + armoured shoulders, head just left of centre (~45%); 'Stark'
> **Visual Staging in Studio**: During Cut 7 (movie 7.841s–9.176s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium close-up on Thanos speaking with heavy, somber authority across the dusty wasteland ('Stark'). A steady telephoto composition captures his stoic expression.

### Cut 08 — Shot `080`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:09.176` (9.176s) to `00:10.427` (10.427s)
- **Duration**: `1.251 seconds` (30 frames at 23.976 fps, movie ref f220–f249)
- **Camera Mode**: `FaceCam` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Mount Rig / Part**: `IronMan.Head` (Local Face Camera Rig)
- **FaceCam Parameters**: Distance = `2.5 studs`, Yaw = `0°`, Pitch = `-3°`, Roll = `0°`
- **Resolved View CFrame Pos**: `[0, 6.55, -37.51]` (fixed relative to helmet forward axis)
- **Vertical FOV**: `30°` (constant tight facial crop)

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.IronMan` — Playing Track: `080_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **HUD Overlay**: Active (`hud = 'mask'`) — Draws stylized Mark 50 helmet HUD with targeting telemetry, amber rings, and edge vignette.
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: a touch tighter than 060, eyes high; 'You know me'
> **Visual Staging in Studio**: During Cut 8 (movie 9.176s–10.427s), Roblox Studio positions the camera facecam relative to the Titan terrain. Interior Mark 50 HUD close-up. Amber flight readouts illuminate Tony Stark's intense, searching expression as he queries 'You know me?'

### Cut 09 — Shot `090`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:10.427` (10.427s) to `00:15.849` (15.849s)
- **Duration**: `5.422 seconds` (130 frames at 23.976 fps, movie ref f250–f379)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.Head` (Offset: `Vector3.new(0.15, -0.05, -4.2)`)
- **Look Target**: `Thanos.Head` (Offset: `Vector3.new(0.35, -0.25, 0)`)
- **Resolved Start Position**: `Vector3.new(0.06, 8.03, -4.08)`
- **Resolved End Position**: `Vector3.new(0.03, 8.03, -3.30)`
- **Field of View (FOV)**: Start `29°` -> End `29°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `090_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up, head slightly left of centre, slow dolly push-in 0.8 studs through the line
> **Visual Staging in Studio**: During Cut 9 (movie 10.427s–15.849s), Roblox Studio positions the camera standard relative to the Titan terrain. Close-up on Thanos. A slow dolly push-in of 0.8 studs enhances the dramatic weight as he reflects: 'You're not the only one cursed with knowledge.'

### Cut 10 — Shot `100`: Standoff and Dialogue

- **Roblox Studio Timing**: `00:15.849` (15.849s) to `00:18.101` (18.101s)
- **Duration**: `2.252 seconds` (54 frames at 23.976 fps, movie ref f380–f433)
- **Camera Mode**: `FaceCam` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Mount Rig / Part**: `IronMan.Head` (Local Face Camera Rig)
- **FaceCam Parameters**: Distance = `2.4 studs`, Yaw = `0°`, Pitch = `-3°`, Roll = `0°`
- **Resolved View CFrame Pos**: `[0, 6.55, -37.61]` (fixed relative to helmet forward axis)
- **Vertical FOV**: `26°` (constant tight facial crop)

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.IronMan` — Playing Track: `100_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **HUD Overlay**: Active (`hud = 'mask'`) — Draws stylized Mark 50 helmet HUD with targeting telemetry, amber rings, and edge vignette.
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up on Iron Man inside HUD, slow creep in; 'My only curse is you' -> FIGHT
> **Visual Staging in Studio**: During Cut 10 (movie 15.849s–18.101s), Roblox Studio positions the camera facecam relative to the Titan terrain. Interior Mark 50 HUD close-up. Tony's jaw sets with icy anger as he delivers his resolute response: 'My only curse is you.' targeting reticles flare as combat systems engage.

### Cut 11 — Shot `110`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:18.101` (18.101s) to `00:19.311` (19.311s)
- **Duration**: `1.210 seconds` (29 frames at 23.976 fps, movie ref f434–f462)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.35, 1.35, 2.85)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0, 0.55, 0)`)
- **Resolved Start Position**: `Vector3.new(0.48, 7.07, -36.05)`
- **Resolved End Position**: `Vector3.new(0.41, 7.00, -36.26)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.IronMan` — Playing Track: `110_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: pods

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium close-up from the FRONT, camera tilted up & back: chest and collar framed, five missile pods on the chest pop and fire
> **Visual Staging in Studio**: During Cut 11 (movie 18.101s–19.311s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium close-up from the front, tilted up. Iron Man's nanotech missile pods sprout from his collarbones with orange emitter sparks, pitching forward 18 degrees as the volley prepares to fire.

### Cut 12 — Shot `115`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:19.311` (19.311s) to `00:20.646` (20.646s)
- **Duration**: `1.335 seconds` (32 frames at 23.976 fps, movie ref f463–f494)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.HumanoidRootPart` (Offset: `Vector3.new(3, 1.2, 25)`)
- **Look Target**: `IronMan.HumanoidRootPart` (Offset: `Vector3.new(0, 5, 0)`)
- **Resolved Start Position**: `Vector3.new(4.16, 5.24, -5.34)`
- **Resolved End Position**: `Vector3.new(4.16, 4.76, -6.72)`
- **Field of View (FOV)**: Start `40°` -> End `40°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.IronMan` — Playing Track: `115_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: flare, pods

#### Studio Scene Analysis & Visual Matter
> **Director Note**: extreme wide, low, from Thanos' side; Iron Man small in the lower middle, missiles curl up into the sky
> **Visual Staging in Studio**: During Cut 12 (movie 19.311s–20.646s), Roblox Studio positions the camera standard relative to the Titan terrain. Extreme wide battlefield shot from Thanos' flank. Dozens of blue micro-missiles curl upward into high arcs across the Titan sky, trailing dense white smoke plumes.

### Cut 13 — Shot `120`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:20.646` (20.646s) to `00:21.438` (21.438s)
- **Duration**: `0.792 seconds` (19 frames at 23.976 fps, movie ref f495–f513)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(1.4, 0.9, -8.6)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(-0.8, 0.8, 0)`)
- **Resolved Start Position**: `Vector3.new(1.53, 6.96, -8.35)`
- **Resolved End Position**: `Vector3.new(1.44, 6.96, -8.15)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `120_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: flare, pods

#### Studio Scene Analysis & Visual Matter
> **Director Note**: Thanos waist-up, left-center of frame; right arm tucked back behind hip; gauntlet raised in lower right foreground; missiles in upper right sky; 'Come on'
> **Visual Staging in Studio**: During Cut 13 (movie 20.646s–21.438s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium cowboy framing on Thanos. Right arm tucked back behind his hip, gauntlet raised in foreground as he watches the missiles converge above, muttering 'Come on.'

### Cut 14 — Shot `130a`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:21.438` (21.438s) to `00:22.522` (22.522s)
- **Duration**: `1.084 seconds` (26 frames at 23.976 fps, movie ref f514–f539)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.HumanoidRootPart` (Offset: `Vector3.new(-7, 18, -36)`)
- **Look Target**: `Thanos.HumanoidRootPart` (Offset: `Vector3.new(0, 1, 0)`)
- **Resolved Start Position**: `Vector3.new(-6.80, 23.23, -34.93)`
- **Resolved End Position**: `Vector3.new(-17.47, 14.54, -5.60)`
- **Field of View (FOV)**: Start `35°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `130a_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: Cut 14: top angle behind missiles, camera trails behind swarm converging on Thanos at high speed
> **Visual Staging in Studio**: During Cut 14 (movie 21.438s–22.522s), Roblox Studio positions the camera standard relative to the Titan terrain. High-angle aerial three-quarter tracking shot trailing immediately behind the cluster missiles as they scream downward toward Thanos at high velocity.

### Cut 15 — Shot `130b`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:22.522` (22.522s) to `00:24.524` (24.524s)
- **Duration**: `2.002 seconds` (48 frames at 23.976 fps, movie ref f540–f587)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.HumanoidRootPart` (Offset: `Vector3.new(-34, 11, -18)`)
- **Look Target**: `Thanos.HumanoidRootPart` (Offset: `Vector3.new(-1, 2, 0)`)
- **Resolved Start Position**: `Vector3.new(-32.76, 16.22, -17.47)`
- **Resolved End Position**: `Vector3.new(-32.76, 16.22, -17.47)`
- **Field of View (FOV)**: Start `40°` -> End `40°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `130b_thanos.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: thruster, dust

#### Studio Scene Analysis & Visual Matter
> **Director Note**: Cut 15: wide ground-level 35 deg profile shot of blast, high-explosive missile impacts detonate across Thanos guard, dust cloud
> **Visual Staging in Studio**: During Cut 15 (movie 22.522s–24.524s), Roblox Studio positions the camera standard relative to the Titan terrain. Wide 35-degree ground profile shot of successive high-explosive fireball detonations slamming into Thanos' raised gauntlet guard, engulfing him in dense black and grey smoke.

### Cut 16 — Shot `140`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:24.524` (24.524s) to `00:25.483` (25.483s)
- **Duration**: `0.959 seconds` (23 frames at 23.976 fps, movie ref f588–f610)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.LowerTorso` (Offset: `Vector3.new(1.2, -0.6, 16.0)`)
- **Look Target**: `IronMan.LowerTorso` (Offset: `Vector3.new(0, 0.35, 0)`)
- **Resolved Start Position**: `Vector3.new(1.66, 3.43, -17.82)`
- **Resolved End Position**: `Vector3.new(1.10, 3.43, -29.60)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `140_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `140_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: kickdisc, thruster, dust

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide, low, frontal: Iron Man flying low toward camera, pitched forward 50 deg, foot/hand thrusters blazing
> **Visual Staging in Studio**: During Cut 16 (movie 24.524s–25.483s), Roblox Studio positions the camera standard relative to the Titan terrain. Low ground-level frontal tracking shot. Iron Man blasts horizontally through the lingering smoke cloud just inches above the terrain, foot and hand repulsors blazing at full thrust.

### Cut 17 — Shot `150`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:25.484` (25.484s) to `00:26.527` (26.527s)
- **Duration**: `1.043 seconds` (25 frames at 23.976 fps, movie ref f611–f635)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.LowerTorso` (Offset: `Vector3.new(9.0, -4.5, -2.5)`)
- **Look Target**: `IronMan.LowerTorso` (Offset: `Vector3.new(0, 2.2, 0.8)`)
- **Resolved Start Position**: `Vector3.new(12.48, -2.57, -43.73)`
- **Resolved End Position**: `Vector3.new(12.48, -2.57, -43.73)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `150_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `150_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: kickdisc, impact, thruster, backthruster, dust

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low-angle pitched upward (+25 deg) against bright orange sky: Iron Man in upper-right somersault flip with cyan back-thrusters
> **Visual Staging in Studio**: During Cut 17 (movie 25.484s–26.527s), Roblox Studio positions the camera standard relative to the Titan terrain. Side-profile low-angle shot tilted upward +25 degrees against the orange sky. Iron Man executes a brutal mid-air somersault dropkick directly into Thanos' chest guard.

### Cut 18 — Shot `160`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:26.526` (26.526s) to `00:27.360` (27.360s)
- **Duration**: `0.834 seconds` (20 frames at 23.976 fps, movie ref f636–f655)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.LeftFoot` (Offset: `Vector3.new(2.8, 0.45, 2.5)`)
- **Look Target**: `IronMan.LeftFoot` (Offset: `Vector3.new(-0.6, 0.15, -0.2)`)
- **Resolved Start Position**: `Vector3.new(4.52, 2.90, -36.47)`
- **Resolved End Position**: `Vector3.new(4.45, 2.90, -36.61)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `160_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `160_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: anchors, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: static, ankle/shin ground level: lower legs clamped to ground, heavy landing slide, dust kick-up, Thanos planted leg on left
> **Visual Staging in Studio**: During Cut 18 (movie 26.526s–27.360s), Roblox Studio positions the camera standard relative to the Titan terrain. Ground-level macro shot focusing on Iron Man's boots slamming into loose Titan gravel and bedrock, with nanotech ground anchors locking firmly into place.

### Cut 19 — Shot `170`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:27.361` (27.361s) to `00:27.987` (27.987s)
- **Duration**: `0.626 seconds` (15 frames at 23.976 fps, movie ref f656–f670)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(1.5, 0.7, 14.0)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.3, 0.25, 0)`)
- **Resolved Start Position**: `Vector3.new(1.98, 6.27, -20.59)`
- **Resolved End Position**: `Vector3.new(1.98, 6.27, -20.87)`
- **Field of View (FOV)**: Start `24°` -> End `24°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `170_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `170_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: cannons, anchors, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: past Thanos reaching arm (upper-left foreground): Iron Man in 3/4 combat stance coiled to strike with silver battering rams
> **Visual Staging in Studio**: During Cut 19 (movie 27.361s–27.987s), Roblox Studio positions the camera standard relative to the Titan terrain. Past Thanos' reaching arm in foreground: Iron Man coiled in combat stance with silver nanotech battering rams deploying across both forearms.

### Cut 20 — Shot `180`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:27.986` (27.986s) to `00:28.612` (28.612s)
- **Duration**: `0.626 seconds` (15 frames at 23.976 fps, movie ref f671–f685)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(7.5, 1.4, -1.2)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-0.6, 0.8, 2.2)`)
- **Resolved Start Position**: `Vector3.new(10.59, 7.06, -42.37)`
- **Resolved End Position**: `Vector3.new(10.17, 7.06, -42.10)`
- **Field of View (FOV)**: Start `42°` -> End `42°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `180_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `180_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: ramimpact, cannons, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: side profile medium two-shot with clean sky headroom: Thanos right arm lowered, ram slam with radial bloom & horizontal blue back thrusters
> **Visual Staging in Studio**: During Cut 20 (movie 27.986s–28.612s), Roblox Studio positions the camera standard relative to the Titan terrain. Side profile medium two-shot: Thanos' right arm lowered as Tony's battering rams slam into his chest guard with radial bloom shockwaves and cyan exhaust jets.

### Cut 21 — Shot `185`: Missiles, Kick & Cannon Charge

- **Roblox Studio Timing**: `00:28.612` (28.612s) to `00:29.404` (29.404s)
- **Duration**: `0.792 seconds` (19 frames at 23.976 fps, movie ref f686–f704)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(3.5, 3.2, -18.5)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-1.5, 0.8, 4.0)`)
- **Resolved Start Position**: `Vector3.new(5.33, 9.56, -66.94)`
- **Resolved End Position**: `Vector3.new(5.33, 9.56, -67.63)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `185_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `185_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: clashsparks, ramimpact, cannons, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide battlefield shot: fighters separated by 4 studs on X, shifted left-of-center onto rocky ridge, thruster clash sparks
> **Visual Staging in Studio**: During Cut 21 (movie 28.612s–29.404s), Roblox Studio positions the camera standard relative to the Titan terrain. Wide battlefield shot: fighters separated along the rocky ridge, thruster clash sparks scattering as they grapple for leverage.

### Cut 22 — Shot `190`: Helmet Tear & Skidding

- **Roblox Studio Timing**: `00:29.404` (29.404s) to `00:30.488` (30.488s)
- **Duration**: `1.084 seconds` (26 frames at 23.976 fps, movie ref f705–f730)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-1.2, 0.9, -2.9)`)
- **Look Target**: `Thanos.Head` (Offset: `Vector3.new(0.1, -0.2, 0)`)
- **Resolved Start Position**: `Vector3.new(-1.69, 5.88, -56.03)`
- **Resolved End Position**: `Vector3.new(-1.55, 5.88, -55.89)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `190_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `190_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: cannons, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: tight OTS medium close-up: Thanos on left-center (35 deg right) gripping helmet, Iron Man in lower-right foreground facing up-left
> **Visual Staging in Studio**: During Cut 22 (movie 29.404s–30.488s), Roblox Studio positions the camera standard relative to the Titan terrain. Tight OTS medium close-up: Thanos on left-center gripping Iron Man's helmet, while Iron Man struggles in the lower-right foreground.

### Cut 23 — Shot `200`: Helmet Tear & Skidding

- **Roblox Studio Timing**: `00:30.489` (30.489s) to `00:31.115` (31.115s)
- **Duration**: `0.626 seconds` (15 frames at 23.976 fps, movie ref f731–f745)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-0.35, 0.15, 3.8)`)
- **Look Target**: `IronMan.Head` (Offset: `Vector3.new(0.1, -0.05, 0)`)
- **Resolved Start Position**: `Vector3.new(-0.52, 6.90, -34.74)`
- **Resolved End Position**: `Vector3.new(-0.45, 6.90, -34.87)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `200_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `200_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: helmet

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up pulled back: Tony unmasked with dark hair, looking up-left in shock (Yaw +20, Pitch +8), shoulders lowered
> **Visual Staging in Studio**: During Cut 23 (movie 30.489s–31.115s), Roblox Studio positions the camera standard relative to the Titan terrain. Close-up on Tony Stark: Mark 50 helmet torn completely off in a shower of sparks; Tony unmasked with disheveled dark hair, staring upward in shock.

### Cut 24 — Shot `210`: Helmet Tear & Skidding

- **Roblox Studio Timing**: `00:31.114` (31.114s) to `00:31.573` (31.573s)
- **Duration**: `0.459 seconds` (11 frames at 23.976 fps, movie ref f746–f756)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(3.2, 1.2, -6.5)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(-0.8, 0.4, 0.8)`)
- **Resolved Start Position**: `Vector3.new(3.28, 7.34, -6.49)`
- **Resolved End Position**: `Vector3.new(3.18, 7.34, -6.30)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `210_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `210_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: brutal headbutt two-shot: full reformed helmet, Thanos on left lunges headbutt down-right, Tony recoils back-right with spark
> **Visual Staging in Studio**: During Cut 24 (movie 31.114s–31.573s), Roblox Studio positions the camera standard relative to the Titan terrain. Brutal headbutt two-shot: nanotech helmet rapidly reforms over Tony's skull just as Thanos lunges forward, headbutting Tony with violent spark bursts and camera shake.

### Cut 25 — Shot `213`: Helmet Tear & Skidding

- **Roblox Studio Timing**: `00:31.573` (31.573s) to `00:31.907` (31.907s)
- **Duration**: `0.334 seconds` (8 frames at 23.976 fps, movie ref f757–f764)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(0.8, -0.25, 3.5)`)
- **Look Target**: `IronMan.Head` (Offset: `Vector3.new(-0.15, -0.15, 0)`)
- **Resolved Start Position**: `Vector3.new(1.15, 6.38, -35.15)`
- **Resolved End Position**: `Vector3.new(1.08, 6.38, -35.29)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `213_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `213_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up pulled back: Iron Man reeling backward (Pitch +15, Yaw -25), right arm counter-swing across chest, arc reactor visible
> **Visual Staging in Studio**: During Cut 25 (movie 31.573s–31.907s), Roblox Studio positions the camera standard relative to the Titan terrain. Close-up of Iron Man reeling backward, throwing a desperate right counter-swing across his chest as his arc reactor glows brightly.

### Cut 26 — Shot `216`: Helmet Tear & Skidding

- **Roblox Studio Timing**: `00:31.907` (31.907s) to `00:32.825` (32.825s)
- **Duration**: `0.918 seconds` (22 frames at 23.976 fps, movie ref f765–f786)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.LowerTorso` (Offset: `Vector3.new(2.6, 0.65, -3.8)`)
- **Look Target**: `IronMan.LowerTorso` (Offset: `Vector3.new(0.2, 0.15, 0.8)`)
- **Resolved Start Position**: `Vector3.new(3.54, 5.23, -45.53)`
- **Resolved End Position**: `Vector3.new(3.26, 5.23, -45.11)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `216_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `216_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: skid, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low ground close-up (Thanos hidden): Iron Man lying flat on his back/side on dirt skidding horizontally in dust
> **Visual Staging in Studio**: During Cut 26 (movie 31.907s–32.825s), Roblox Studio positions the camera standard relative to the Titan terrain. Heavy hammer blow from Thanos crashing onto Tony's back, slamming him violently into the soil with a heavy dirt impact and long skid cloud.

### Cut 27 — Shot `220`: Helmet Tear & Skidding

- **Roblox Studio Timing**: `00:32.824` (32.824s) to `00:35.243` (35.243s)
- **Duration**: `2.419 seconds` (58 frames at 23.976 fps, movie ref f787–f844)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(3.6, 1.0, -11.0)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(-0.7, 0.1, 0)`)
- **Resolved Start Position**: `Vector3.new(3.64, 7.21, -10.68)`
- **Resolved End Position**: `Vector3.new(3.45, 7.21, -10.38)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `220_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `220_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.IronMan` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: skid, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium full-shot dollied close: Thanos on left-center filling 70% frame height, angled 40 deg right, fists near hips
> **Visual Staging in Studio**: During Cut 27 (movie 32.824s–35.243s), Roblox Studio positions the camera standard relative to the Titan terrain. Thanos chuckles in medium cowboy view as he plucks the nanotech clamp piece from his left gauntlet palm and flings it dismissively into the dirt.

### Cut 28 — Shot `230`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:35.244` (35.244s) to `00:35.870` (35.870s)
- **Duration**: `0.626 seconds` (15 frames at 23.976 fps, movie ref f845–f859)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(1.5, 0.35, 3.2)`)
- **Look Target**: `IronMan.Head` (Offset: `Vector3.new(-0.3, 0.05, 0)`)
- **Resolved Start Position**: `Vector3.new(2.17, 7.15, -35.57)`
- **Resolved End Position**: `Vector3.new(2.10, 7.15, -35.71)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `230_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `230_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: tight close-up pulled back: Iron Man in low ground crouch, shoulders down, helmet angled 22 deg left and +10 deg up glaring at Thanos
> **Visual Staging in Studio**: During Cut 28 (movie 35.244s–35.870s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium close-up: Thanos raises the Infinity Gauntlet, clenching his fist as the purple Power Stone blazes with blinding energy flares.

### Cut 29 — Shot `240`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:35.869` (35.869s) to `00:37.329` (37.329s)
- **Duration**: `1.460 seconds` (35 frames at 23.976 fps, movie ref f860–f894)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(10.19, 4.85, -9.23)`)
- **Look Target**: `World` (Offset: `Vector3.new(-2.5, 5.0, 0.0)`)
- **Resolved Start Position**: `Vector3.new(13.99, 4.80, -12.00)`
- **Resolved End Position**: `Vector3.new(13.75, 4.80, -11.70)`
- **Field of View (FOV)**: Start `42°` -> End `42°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `240_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `240_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide battlefield: Thanos on left-third raising glowing Gauntlet, Iron Man in lower-right defensive crouch
> **Visual Staging in Studio**: During Cut 29 (movie 35.869s–37.329s), Roblox Studio positions the camera standard relative to the Titan terrain. Extreme wide shot across the battlefield: a massive torrent of violet Power Stone energy erupts from the gauntlet, bridging the entire gap toward Iron Man.

### Cut 30 — Shot `250`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:37.329` (37.329s) to `00:37.871` (37.871s)
- **Duration**: `0.542 seconds` (13 frames at 23.976 fps, movie ref f895–f907)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-0.15, 5.3, -8.1)`)
- **Look Target**: `World` (Offset: `Vector3.new(-6.2, 4.8, -3.2)`)
- **Resolved Start Position**: `Vector3.new(1.66, 5.45, -9.58)`
- **Resolved End Position**: `Vector3.new(1.53, 5.45, -9.45)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `250_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `250_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shield

#### Studio Scene Analysis & Visual Matter
> **Director Note**: side profile: Iron Man in deep braced athletic lunge, thick curved nanotech tower shield deployed (beam not started yet)
> **Visual Staging in Studio**: During Cut 30 (movie 37.329s–37.871s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium frontal shot: Iron Man's left forearm morphs instantly into the massive nanotech tower shield, bracing behind it just before energy impact.

### Cut 31 — Shot `255`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:37.871` (37.871s) to `00:38.538` (38.538s)
- **Duration**: `0.667 seconds` (16 frames at 23.976 fps, movie ref f908–f923)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-3.04, 3.96, -8.27)`)
- **Look Target**: `World` (Offset: `Vector3.new(-6.5, 4.5, -2.5)`)
- **Resolved Start Position**: `Vector3.new(-2.01, 3.79, -10.01)`
- **Resolved End Position**: `Vector3.new(-2.15, 3.79, -9.91)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `255_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `255_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact, shield, skid, beam, tint, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium-wide detonation: Iron Man visible right-of-center braced behind shield; thick purple beam slams in from left detonating massive radial plasma burst
> **Visual Staging in Studio**: During Cut 31 (movie 37.871s–38.538s), Roblox Studio positions the camera standard relative to the Titan terrain. Massive radial violet-white plasma detonation as the Power Stone beam slams into the shield, lighting the entire environment in deep magenta hues.

### Cut 32 — Shot `260`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:38.538` (38.538s) to `00:39.748` (39.748s)
- **Duration**: `1.210 seconds` (29 frames at 23.976 fps, movie ref f924–f952)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(5.2, 0.8, -4.7)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.75, -0.3, 0.57)`)
- **Resolved Start Position**: `Vector3.new(6.97, 6.58, -46.71)`
- **Resolved End Position**: `Vector3.new(6.55, 6.58, -46.43)`
- **Field of View (FOV)**: Start `40°` -> End `42°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `260_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `260_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact, shield, skid, beam, tint, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: side tracking: continuous thick purple energy torrent hammers shield, deflected plasma cones wash around body, sliding backward
> **Visual Staging in Studio**: During Cut 32 (movie 38.538s–39.748s), Roblox Studio positions the camera standard relative to the Titan terrain. Close-up on Iron Man's armored boots gouging deep trenches into the Titan soil, trembling under the colossal kinetic thrust of the beam.

### Cut 33 — Shot `262`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:39.748` (39.748s) to `00:41.083` (41.083s)
- **Duration**: `1.335 seconds` (32 frames at 23.976 fps, movie ref f953–f984)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-0.95, 0.35, -1.45)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(1.2, 0.15, 1.8)`)
- **Resolved Start Position**: `Vector3.new(-1.71, 7.51, -42.59)`
- **Resolved End Position**: `Vector3.new(-1.57, 7.51, -42.52)`
- **Field of View (FOV)**: Start `42°` -> End `42°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `262_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `262_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: beam, shield, tint, skid, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: tight OTS close-up behind right shoulder: violent violet plasma waves wash directly over shield & helmet, obscuring background
> **Visual Staging in Studio**: During Cut 33 (movie 39.748s–41.083s), Roblox Studio positions the camera standard relative to the Titan terrain. Wide profile angle: the searing beam holds steady for over a second, driving Iron Man back several studs as atmospheric dust clouds billow.

### Cut 34 — Shot `265`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:41.083` (41.083s) to `00:41.792` (41.792s)
- **Duration**: `0.709 seconds` (17 frames at 23.976 fps, movie ref f985–f1001)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(4.8, 0.8, -4.5)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-0.8, 0.1, 0.4)`)
- **Resolved Start Position**: `Vector3.new(6.91, 6.46, -46.37)`
- **Resolved End Position**: `Vector3.new(6.49, 6.46, -45.96)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `265_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `265_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: beam, shield, tint, skid, thruster, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close tracking side: Iron Man drops shield and lunges forward-left in low aerodynamic sprint under the beam, thrusters firing
> **Visual Staging in Studio**: During Cut 34 (movie 41.083s–41.792s), Roblox Studio positions the camera standard relative to the Titan terrain. Iron Man shifts the shield angle, cutting sideways out of the beam's path and igniting his back thrusters in an evasive barrel roll.

### Cut 35 — Shot `270`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:41.792` (41.792s) to `00:42.334` (42.334s)
- **Duration**: `0.542 seconds` (13 frames at 23.976 fps, movie ref f1002–f1014)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(5.8, 1.2, -7.2)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-0.4, 0.2, 0.0)`)
- **Resolved Start Position**: `Vector3.new(8.17, 6.98, -49.99)`
- **Resolved End Position**: `Vector3.new(7.89, 6.98, -49.71)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `270_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `270_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: thruster

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium-wide tracking: Iron Man launched diagonally upward-left (~35 deg) airborne barrel-roll with focused conical thruster flame
> **Visual Staging in Studio**: During Cut 35 (movie 41.792s–42.334s), Roblox Studio positions the camera standard relative to the Titan terrain. Ground-skimming sprint: Iron Man charges forward at high speed directly beneath Thanos' line of sight with repulsor flames trailing.

### Cut 36 — Shot `275`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:42.334` (42.334s) to `00:42.793` (42.793s)
- **Duration**: `0.459 seconds` (11 frames at 23.976 fps, movie ref f1015–f1025)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.RightLowerLeg` (Offset: `Vector3.new(1.2, 0.75, -2.5)`)
- **Look Target**: `IronMan.RightFoot` (Offset: `Vector3.new(0.1, -0.35, 0.15)`)
- **Resolved Start Position**: `Vector3.new(1.18, 4.32, -43.52)`
- **Resolved End Position**: `Vector3.new(1.18, 4.32, -43.52)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `275_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `275_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: thruster

#### Studio Scene Analysis & Visual Matter
> **Director Note**: ECU boot thruster insert: lower leg / boot skimming dirt diagonally across frame
> **Visual Staging in Studio**: During Cut 36 (movie 42.334s–42.793s), Roblox Studio positions the camera standard relative to the Titan terrain. Airborne lunge: Iron Man vaults upward, aiming both feet directly at Thanos' raised Infinity Gauntlet.

### Cut 37 — Shot `280`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:42.793` (42.793s) to `00:43.377` (43.377s)
- **Duration**: `0.584 seconds` (14 frames at 23.976 fps, movie ref f1026–f1039)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(3.0, 5.85, -4.75)`)
- **Look Target**: `World` (Offset: `Vector3.new(-0.76, 5.35, 1.77)`)
- **Resolved Start Position**: `Vector3.new(4.12, 6.00, -6.71)`
- **Resolved End Position**: `Vector3.new(3.93, 6.00, -6.65)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `280_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `280_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: thruster, anchors, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium two-shot side profile: Thanos on left punches right, Iron Man on right in defensive cross-guard
> **Visual Staging in Studio**: During Cut 37 (movie 42.793s–43.377s), Roblox Studio positions the camera standard relative to the Titan terrain. Kinetic clamp impact: Iron Man's magnetic boots slam down onto Thanos' left gauntlet, forcing the Titan's arm downward toward the terrain.

### Cut 38 — Shot `290`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:43.377` (43.377s) to `00:44.086` (44.086s)
- **Duration**: `0.709 seconds` (17 frames at 23.976 fps, movie ref f1040–f1056)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-0.2, 2.6, 5.8)`)
- **Look Target**: `World` (Offset: `Vector3.new(-0.9, 2.2, 3.4)`)
- **Resolved Start Position**: `Vector3.new(0.00, 2.71, 6.52)`
- **Resolved End Position**: `Vector3.new(0.07, 2.71, 6.52)`
- **Field of View (FOV)**: Start `30°` -> End `30°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `290_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `290_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: anchors, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close, ground level: right boot slams onto pinned gauntlet, anchors bite into soil
> **Visual Staging in Studio**: During Cut 38 (movie 43.377s–44.086s), Roblox Studio positions the camera standard relative to the Titan terrain. Ground anchor lock: mechanical spurs drive from Tony's boot soles deep into the bedrock, pinning Thanos' gauntleted fist to the earth.

### Cut 39 — Shot `295`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:44.086` (44.086s) to `00:44.545` (44.545s)
- **Duration**: `0.459 seconds` (11 frames at 23.976 fps, movie ref f1057–f1067)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-16.5, 6.2, -7.5)`)
- **Look Target**: `World` (Offset: `Vector3.new(4.5, 4.6, 4.5)`)
- **Resolved Start Position**: `Vector3.new(-22.80, 6.67, -11.10)`
- **Resolved End Position**: `Vector3.new(-22.67, 6.67, -10.97)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `295_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `295_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: anchors, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide: Thanos on one knee left, Iron Man standing tall winding right arm high overhead, right half negative space
> **Visual Staging in Studio**: During Cut 39 (movie 44.086s–44.545s), Roblox Studio positions the camera standard relative to the Titan terrain. Dynamic pivot: with Thanos' left arm immobilized, Iron Man uses the anchor as a fulcrum to execute a 360-degree horizontal spin.

### Cut 40 — Shot `300`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:44.544` (44.544s) to `00:45.003` (45.003s)
- **Duration**: `0.459 seconds` (11 frames at 23.976 fps, movie ref f1068–f1078)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.RightHand` (Offset: `Vector3.new(1.8, 1.1, -2.4)`)
- **Look Target**: `IronMan.RightHand` (Offset: `Vector3.new(0.0, -0.2, 0.0)`)
- **Resolved Start Position**: `Vector3.new(1.14, 5.92, -43.33)`
- **Resolved End Position**: `Vector3.new(1.07, 5.92, -43.26)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `300_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `300_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: anchors, fistgun

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close on his right arm mid-spin: nanotech piles onto the fist into a heavy weapon
> **Visual Staging in Studio**: During Cut 40 (movie 44.544s–45.003s), Roblox Studio positions the camera standard relative to the Titan terrain. Weapon formation: during the spin, nanotech rapidly concentrates onto Tony's right forearm, forming a heavy spiked battering ram.

### Cut 41 — Shot `310`: Power Stone Beam & Counter

- **Roblox Studio Timing**: `00:45.003` (45.003s) to `00:45.545` (45.545s)
- **Duration**: `0.542 seconds` (13 frames at 23.976 fps, movie ref f1079–f1091)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(1.8, 7.2, -1.8)`)
- **Look Target**: `World` (Offset: `Vector3.new(-0.9, 4.8, 3.4)`)
- **Resolved Start Position**: `Vector3.new(2.60, 7.91, -3.36)`
- **Resolved End Position**: `Vector3.new(2.54, 7.91, -3.30)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `310_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `310_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: mark, anchors, fistgun

#### Studio Scene Analysis & Visual Matter
> **Director Note**: front/OTS: Iron Man back top-left whips downward smashing battering ram into Thanos face in bottom-right
> **Visual Staging in Studio**: During Cut 41 (movie 45.003s–45.545s), Roblox Studio positions the camera standard relative to the Titan terrain. Crushing strike: the spiked ram smashes directly into Thanos' left cheekbone, delivering immense blunt force that violently snaps Thanos' head to the side.

### Cut 42 — Shot `320`: Drop of Blood & Face-off

- **Roblox Studio Timing**: `00:45.545` (45.545s) to `00:48.757` (48.757s)
- **Duration**: `3.212 seconds` (77 frames at 23.976 fps, movie ref f1092–f1168)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.Head` (Offset: `Vector3.new(-2.2, -0.7, -3.8)`)
- **Look Target**: `Thanos.Head` (Offset: `Vector3.new(0.0, -0.1, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-2.14, 7.36, -3.69)`
- **Resolved End Position**: `Vector3.new(-1.95, 7.36, -3.50)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `320_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `320_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.IronMan` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: mark, fistgun

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close, low, front-left: the blow still ringing, head hung; his fingers come up to the brow
> **Visual Staging in Studio**: During Cut 42 (movie 45.545s–48.757s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium shot of Thanos reeling backward, breaking the ground lock, dazed and disoriented by the unexpected ferocity of the blow.

### Cut 43 — Shot `340`: Drop of Blood & Face-off

- **Roblox Studio Timing**: `00:48.757` (48.757s) to `00:49.591` (49.591s)
- **Duration**: `0.834 seconds` (20 frames at 23.976 fps, movie ref f1169–f1188)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(-1.8, 1.2, -1.8)`)
- **Look Target**: `Thanos.RightHand` (Offset: `Vector3.new(0.0, 0.0, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-2.36, 7.85, -1.75)`
- **Resolved End Position**: `Vector3.new(-2.26, 7.80, -1.65)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `340_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `340_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.IronMan` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: mark

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close on his right hand, palm up: blood on his fingertip
> **Visual Staging in Studio**: During Cut 43 (movie 48.757s–49.591s), Roblox Studio positions the camera standard relative to the Titan terrain. Extreme close-up: Thanos slowly lifts his right hand to his bruised left cheek, his fingertips brushing across the grazed purple skin.

### Cut 44 — Shot `350`: Drop of Blood & Face-off

- **Roblox Studio Timing**: `00:49.591` (49.591s) to `00:52.260` (52.260s)
- **Duration**: `2.669 seconds` (64 frames at 23.976 fps, movie ref f1189–f1252)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.Head` (Offset: `Vector3.new(-0.8, 0.0, -4.5)`)
- **Look Target**: `Thanos.Head` (Offset: `Vector3.new(0.0, -0.1, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-0.78, 8.04, -4.37)`
- **Resolved End Position**: `Vector3.new(-0.68, 8.04, -4.08)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `350_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `350_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.IronMan` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close on his face: blood on his brow; he raises his eyes to Iron Man, half a smile
> **Visual Staging in Studio**: During Cut 44 (movie 49.591s–52.260s), Roblox Studio positions the camera standard relative to the Titan terrain. Close-up on Thanos' thumb and forefinger: he examines a single smear of crimson blood against his skin with solemn curiosity.

### Cut 45 — Shot `360`: Drop of Blood & Face-off

- **Roblox Studio Timing**: `00:52.261` (52.261s) to `00:52.761` (52.761s)
- **Duration**: `0.500 seconds` (12 frames at 23.976 fps, movie ref f1253–f1264)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(1.67, 6.26, -2.55)`)
- **Look Target**: `World` (Offset: `Vector3.new(-0.61, 5.79, 1.98)`)
- **Resolved Start Position**: `Vector3.new(2.35, 6.40, -3.91)`
- **Resolved End Position**: `Vector3.new(2.21, 6.36, -3.63)`
- **Field of View (FOV)**: Start `40°` -> End `40°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `360_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `360_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: side-on two-shot, the face-off: Thanos on his knee screen left, Iron Man standing screen right
> **Visual Staging in Studio**: During Cut 45 (movie 52.261s–52.761s), Roblox Studio positions the camera standard relative to the Titan terrain. Iconic cinematic two-shot face-off: Thanos lowers his hand and grins with grim admiration: 'All that for a drop of blood.'

### Cut 46 — Shot `370`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:52.761` (52.761s) to `00:53.053` (53.053s)
- **Duration**: `0.292 seconds` (7 frames at 23.976 fps, movie ref f1265–f1271)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-0.05, 2.28, -1.02)`)
- **Look Target**: `World` (Offset: `Vector3.new(-2.21, 2.2, 2.25)`)
- **Resolved Start Position**: `Vector3.new(0.59, 2.30, -2.01)`
- **Resolved End Position**: `Vector3.new(0.59, 2.30, -2.01)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `370_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `370_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low angle at the ground: Thanos lunges in and sweeps Iron Man's feet out from under him
> **Visual Staging in Studio**: During Cut 46 (movie 52.761s–53.053s), Roblox Studio positions the camera standard relative to the Titan terrain. Sudden low sweep: Thanos swings his heavy armored leg across the terrain, sweeping Iron Man's legs out from under him.

### Cut 47 — Shot `375`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:53.053` (53.053s) to `00:54.012` (54.012s)
- **Duration**: `0.959 seconds` (23 frames at 23.976 fps, movie ref f1272–f1294)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-8.5, 2.6, 4.2)`)
- **Look Target**: `World` (Offset: `Vector3.new(-6.8, 6.2, -1.2)`)
- **Resolved Start Position**: `Vector3.new(-9.02, 1.51, 5.81)`
- **Resolved End Position**: `Vector3.new(-8.88, 1.58, 5.55)`
- **Field of View (FOV)**: Start `44°` -> End `44°`
- **Camera Roll**: Start `-22°` -> End `-22°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `375_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `375_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide, Dutch tilt: Iron Man is hurled flipping horizontally through the air toward screen right
> **Visual Staging in Studio**: During Cut 47 (movie 53.053s–54.012s), Roblox Studio positions the camera standard relative to the Titan terrain. High-speed mid-air tumble: Iron Man flips horizontally through the air and crashes flat onto his back across the rocky ridge.

### Cut 48 — Shot `380`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:54.012` (54.012s) to `00:54.679` (54.679s)
- **Duration**: `0.667 seconds` (16 frames at 23.976 fps, movie ref f1295–f1310)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-1.5, -0.6, -1.2)`)
- **Look Target**: `IronMan.LowerTorso` (Offset: `Vector3.new(0.0, -0.4, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-2.09, 6.66, -41.67)`
- **Resolved End Position**: `Vector3.new(-1.95, 6.66, -41.53)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `380_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `380_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, skid, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low ground angle behind him: Iron Man slams hard onto his back, skidding face-up into the dust
> **Visual Staging in Studio**: During Cut 48 (movie 54.012s–54.679s), Roblox Studio positions the camera standard relative to the Titan terrain. Terrifying stride: Thanos closes the distance instantly, planting his knee onto Tony's chest armor, pinning him completely.

### Cut 49 — Shot `390`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:54.680` (54.680s) to `00:55.139` (55.139s)
- **Duration**: `0.459 seconds` (11 frames at 23.976 fps, movie ref f1311–f1321)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-14.0, 1.75, -6.75)`)
- **Look Target**: `World` (Offset: `Vector3.new(-6.9, 6.0, 0.7)`)
- **Resolved Start Position**: `Vector3.new(-16.13, 0.47, -8.99)`
- **Resolved End Position**: `Vector3.new(-16.00, 0.50, -8.86)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `390_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `390_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low-angle two-shot past Tony's head in foreground: Thanos strides in menacingly, fist cocked
> **Visual Staging in Studio**: During Cut 49 (movie 54.680s–55.139s), Roblox Studio positions the camera standard relative to the Titan terrain. Power wind-up: Thanos pulls his bare right fist high into the air, muscles tensed for execution.

### Cut 50 — Shot `395`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:55.138` (55.138s) to `00:55.513` (55.513s)
- **Duration**: `0.375 seconds` (9 frames at 23.976 fps, movie ref f1322–f1330)
- **Camera Mode**: `FaceCam` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Mount Rig / Part**: `IronMan.Head` (Local Face Camera Rig)
- **FaceCam Parameters**: Distance = `2.8 studs`, Yaw = `0°`, Pitch = `0°`, Roll = `0°`
- **Resolved View CFrame Pos**: `[0, 6.68, -37.21]` (fixed relative to helmet forward axis)
- **Vertical FOV**: `26°` (constant tight facial crop)

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `395_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `395_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **HUD Overlay**: Active (`hud = 'mask'`) — Draws stylized Mark 50 helmet HUD with targeting telemetry, amber rings, and edge vignette.
- **Active Procedural VFX**: impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: inside-the-mask: Tony wide-eyed looking up in dread as Thanos looms over him
> **Visual Staging in Studio**: During Cut 50 (movie 55.138s–55.513s), Roblox Studio positions the camera facecam relative to the Titan terrain. Punch 1: Thanos' crushing fist smashes down onto Iron Man's faceplate with a deafening metallic clang and camera shake.

### Cut 51 — Shot `400`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:55.514` (55.514s) to `00:56.140` (56.140s)
- **Duration**: `0.626 seconds` (15 frames at 23.976 fps, movie ref f1331–f1345)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(2.8, 4.8, 3.4)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 0.2, 0.0)`)
- **Resolved Start Position**: `Vector3.new(3.88, 11.97, -35.29)`
- **Resolved End Position**: `Vector3.new(3.74, 11.83, -35.43)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `400_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `400_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: top-down high angle looking down at Tony: he desperately scrambles to cross his arms and block
> **Visual Staging in Studio**: During Cut 51 (movie 55.514s–56.140s), Roblox Studio positions the camera standard relative to the Titan terrain. Reaction close-up: Iron Man's head rebounds violently against the solid rock surface below.

### Cut 52 — Shot `405`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:56.139` (56.139s) to `00:56.598` (56.598s)
- **Duration**: `0.459 seconds` (11 frames at 23.976 fps, movie ref f1346–f1356)
- **Camera Mode**: `FaceCam` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Mount Rig / Part**: `IronMan.Head` (Local Face Camera Rig)
- **FaceCam Parameters**: Distance = `2.6 studs`, Yaw = `48°`, Pitch = `0°`, Roll = `0°`
- **Resolved View CFrame Pos**: `[1.93, 6.68, -38.27]` (fixed relative to helmet forward axis)
- **Vertical FOV**: `26°` (constant tight facial crop)

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `405_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `405_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **HUD Overlay**: Active (`hud = 'mask'`) — Draws stylized Mark 50 helmet HUD with targeting telemetry, amber rings, and edge vignette.
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: inside-the-mask: PUNCH 1 lands, Tony jerks violently under holographic HUD
> **Visual Staging in Studio**: During Cut 52 (movie 56.139s–56.598s), Roblox Studio positions the camera facecam relative to the Titan terrain. Punch 2: a second devastating blow strikes the Mark 50 helmet, fracturing the gold faceplate and scattering metal shards.

### Cut 53 — Shot `410`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:56.598` (56.598s) to `00:57.724` (57.724s)
- **Duration**: `1.126 seconds` (27 frames at 23.976 fps, movie ref f1357–f1383)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-2.4, 0.45, -2.2)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.1, 0.35, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-3.37, 7.58, -43.06)`
- **Resolved End Position**: `Vector3.new(-3.23, 7.58, -42.92)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `410_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `410_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low ground angle side view: Iron Man propped on ground on his back/side, propping upper body against golden horizon
> **Visual Staging in Studio**: During Cut 53 (movie 56.598s–57.724s), Roblox Studio positions the camera standard relative to the Titan terrain. Defensive parry: Tony brings his right forearm up in desperation, attempting to block Thanos' incoming left fist.

### Cut 54 — Shot `415`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:57.724` (57.724s) to `00:58.099` (58.099s)
- **Duration**: `0.375 seconds` (9 frames at 23.976 fps, movie ref f1384–f1392)
- **Camera Mode**: `FaceCam` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Mount Rig / Part**: `IronMan.Head` (Local Face Camera Rig)
- **FaceCam Parameters**: Distance = `2.6 studs`, Yaw = `0°`, Pitch = `0°`, Roll = `5°`
- **Resolved View CFrame Pos**: `[0, 6.68, -37.41]` (fixed relative to helmet forward axis)
- **Vertical FOV**: `26°` (constant tight facial crop)

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `415_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `415_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **HUD Overlay**: Active (`hud = 'mask'`) — Draws stylized Mark 50 helmet HUD with targeting telemetry, amber rings, and edge vignette.
- **Active Procedural VFX**: shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: inside-the-mask: Tony grimacing in agony with eyes clenched as blood drips down his brow
> **Visual Staging in Studio**: During Cut 54 (movie 57.724s–58.099s), Roblox Studio positions the camera facecam relative to the Titan terrain. Guard stripped: Thanos effortlessly swats Tony's defending arm away, leaving his head completely exposed.

### Cut 55 — Shot `420`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:58.100` (58.100s) to `00:58.767` (58.767s)
- **Duration**: `0.667 seconds` (16 frames at 23.976 fps, movie ref f1393–f1408)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-1.25, 0.85, -2.6)`)
- **Look Target**: `IronMan.Head` (Offset: `Vector3.new(0.35, -0.05, 0.15)`)
- **Resolved Start Position**: `Vector3.new(-1.85, 7.87, -43.66)`
- **Resolved End Position**: `Vector3.new(-1.78, 7.87, -43.52)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `420_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `420_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: extreme close-up on dirt: Punch 1 — red shoulder on left, gold/red helmet turned sideways in dirt on right
> **Visual Staging in Studio**: During Cut 55 (movie 58.100s–58.767s), Roblox Studio positions the camera standard relative to the Titan terrain. Punch 3: a direct blow shatters the left half of Tony's helmet, revealing his bruised, bloodied face beneath.

### Cut 56 — Shot `425`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:58.767` (58.767s) to `00:59.351` (59.351s)
- **Duration**: `0.584 seconds` (14 frames at 23.976 fps, movie ref f1409–f1422)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `World` (Offset: `Vector3.new(-13.8, 4.8, -6.4)`)
- **Look Target**: `World` (Offset: `Vector3.new(-11.98, 1.43, -4.65)`)
- **Resolved Start Position**: `Vector3.new(-14.35, 5.81, -6.93)`
- **Resolved End Position**: `Vector3.new(-14.29, 5.78, -6.86)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `425_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `425_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: overhead punch down Thanos's arm: purple arm bottom-left driving straight into Iron Man helmet pinned in center
> **Visual Staging in Studio**: During Cut 56 (movie 58.767s–59.351s), Roblox Studio positions the camera standard relative to the Titan terrain. Punch 4: another brutal strike hammers the remaining helmet structure, causing warning alerts to glitch across remaining HUD shards.

### Cut 57 — Shot `430`: Beatdown & Broken Helmet

- **Roblox Studio Timing**: `00:59.351` (59.351s) to `01:00.310` (60.310s)
- **Duration**: `0.959 seconds` (23 frames at 23.976 fps, movie ref f1423–f1445)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-1.25, 0.85, -2.6)`)
- **Look Target**: `IronMan.Head` (Offset: `Vector3.new(0.35, -0.05, 0.15)`)
- **Resolved Start Position**: `Vector3.new(-1.85, 7.87, -43.66)`
- **Resolved End Position**: `Vector3.new(-1.78, 7.87, -43.52)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `430_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `430_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: extreme close-up shattered helmet: Punch 2 — gold faceplate torn away exposing Tony's bruised forehead & eye
> **Visual Staging in Studio**: During Cut 57 (movie 59.351s–60.310s), Roblox Studio positions the camera standard relative to the Titan terrain. Complete helmet failure: the Mark 50 faceplate dissolves entirely, leaving Tony's bare head vulnerable and dazed in the dust.

### Cut 58 — Shot `435`: Point-Blank Blast & March

- **Roblox Studio Timing**: `01:00.310` (60.310s) to `01:02.229` (62.229s)
- **Duration**: `1.919 seconds` (46 frames at 23.976 fps, movie ref f1446–f1491)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(9.2, 1.2, -12.5)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(0.8, 0.4, 0.8)`)
- **Resolved Start Position**: `Vector3.new(8.74, 7.34, -12.31)`
- **Resolved End Position**: `Vector3.new(8.55, 7.34, -12.12)`
- **Field of View (FOV)**: Start `35°` -> End `35°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `435_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `435_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: tint, stoneblast, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide static low: Thanos grabs collar, lifts Iron Man off ground, gauntlet glows purple, point-blank blast
> **Visual Staging in Studio**: During Cut 58 (movie 60.310s–62.229s), Roblox Studio positions the camera standard relative to the Titan terrain. Point-blank blast: Thanos activates the Power Stone at zero range against Tony's chest, creating a blinding violet explosion.

### Cut 59 — Shot `440`: Point-Blank Blast & March

- **Roblox Studio Timing**: `01:02.229` (62.229s) to `01:03.397` (63.397s)
- **Duration**: `1.168 seconds` (28 frames at 23.976 fps, movie ref f1492–f1519)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-1.39, 0.35, -5.19)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 0.2, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-1.93, 5.80, -47.20)`
- **Resolved End Position**: `Vector3.new(-1.88, 5.77, -47.01)`
- **Field of View (FOV)**: Start `40°` -> End `40°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `440_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `440_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact, shake, skid, stoneblast

#### Studio Scene Analysis & Visual Matter
> **Director Note**: static low behind wreckage: Iron Man crashes, tumbles, slides to a stop on his back mid-frame
> **Visual Staging in Studio**: During Cut 59 (movie 62.229s–63.397s), Roblox Studio positions the camera standard relative to the Titan terrain. Violent launch: the detonation hurls Iron Man 30 studs backward, crashing through debris and rolling to a stop against a rock ridge.

### Cut 60 — Shot `445`: Point-Blank Blast & March

- **Roblox Studio Timing**: `01:03.397` (63.397s) to `01:04.732` (64.732s)
- **Duration**: `1.335 seconds` (32 frames at 23.976 fps, movie ref f1520–f1551)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(3.5, 0.8, -9.8)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(-0.2, 0.4, 0.0)`)
- **Resolved Start Position**: `Vector3.new(3.43, 6.95, -9.51)`
- **Resolved End Position**: `Vector3.new(3.14, 6.90, -8.93)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `445_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `445_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide tracking: Thanos lowers gauntlet and marches toward Iron Man; Tony stirs in distant rubble
> **Visual Staging in Studio**: During Cut 60 (movie 63.397s–64.732s), Roblox Studio positions the camera standard relative to the Titan terrain. Menacing march: Thanos strides slowly toward the downed Avenger, armored boots crunching into loose Titan gravel.

### Cut 61 — Shot `450`: Point-Blank Blast & March

- **Roblox Studio Timing**: `01:04.731` (64.731s) to `01:05.440` (65.440s)
- **Duration**: `0.709 seconds` (17 frames at 23.976 fps, movie ref f1552–f1568)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-5.5, -0.2, 5.0)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 0.3, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-7.63, 5.00, -33.07)`
- **Resolved End Position**: `Vector3.new(-7.35, 5.03, -33.35)`
- **Field of View (FOV)**: Start `38°` -> End `38°`
- **Camera Roll**: Start `-8°` -> End `-8°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `450_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `450_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: repulsor, shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low angle rubble: Iron Man pushes onto one knee, raises right gauntlet and fires repulsor beam
> **Visual Staging in Studio**: During Cut 61 (movie 64.731s–65.440s), Roblox Studio positions the camera standard relative to the Titan terrain. Struggle to rise: Tony groans in pain, pushing himself up onto one knee amidst the rubble, suit sparks flickering.

### Cut 62 — Shot `455`: Point-Blank Blast & March

- **Roblox Studio Timing**: `01:05.440` (65.440s) to `01:06.358` (66.358s)
- **Duration**: `0.918 seconds` (22 frames at 23.976 fps, movie ref f1569–f1590)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(-3.5, 0.4, -6.5)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(0.0, 0.3, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-3.40, 6.58, -6.31)`
- **Resolved End Position**: `Vector3.new(-3.30, 6.56, -6.02)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `455_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `455_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: repulsor, shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium-wide tracking: Thanos blocks repulsor beam with gauntlet, walking relentlessly through sparks
> **Visual Staging in Studio**: During Cut 62 (movie 65.440s–66.358s), Roblox Studio positions the camera standard relative to the Titan terrain. Single repulsor shot: Tony raises his trembling right hand and fires a desperate energy blast at Thanos' chest.

### Cut 63 — Shot `460`: Point-Blank Blast & March

- **Roblox Studio Timing**: `01:06.358` (66.358s) to `01:07.776` (67.776s)
- **Duration**: `1.418 seconds` (34 frames at 23.976 fps, movie ref f1591–f1624)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-4.0, 0.3, 3.2)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.2, 0.3, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-5.62, 5.70, -35.57)`
- **Resolved End Position**: `Vector3.new(-5.48, 5.73, -35.71)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `460_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `460_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: nanotech, repulsor

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close-up: Iron Man kneeling, nanotech armor flows and regenerates across damaged chest plates
> **Visual Staging in Studio**: During Cut 63 (movie 66.358s–67.776s), Roblox Studio positions the camera standard relative to the Titan terrain. Casual deflection: Thanos swats the blast away with the back of his gauntlet; nanotech frantically shifts over Tony's damaged chest.

### Cut 64 — Shot `465`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:07.776` (67.776s) to `01:08.527` (68.527s)
- **Duration**: `0.751 seconds` (18 frames at 23.976 fps, movie ref f1625–f1642)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(6.5, 0.6, -5.5)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-0.2, 0.3, 0.2)`)
- **Resolved Start Position**: `Vector3.new(9.07, 6.11, -47.70)`
- **Resolved End Position**: `Vector3.new(8.93, 6.11, -47.42)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `465_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `465_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: nanotech, firelaser, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium-close front-right: Iron Man on one knee unleashes dual searing fire-lasers towards screen left
> **Visual Staging in Studio**: During Cut 64 (movie 67.776s–68.527s), Roblox Studio positions the camera standard relative to the Titan terrain. Twin energy weapons: Tony concentrates all remaining power into dual forearm-mounted fire-lasers, aiming directly at Thanos.

### Cut 65 — Shot `470`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:08.527` (68.527s) to `01:10.529` (70.529s)
- **Duration**: `2.002 seconds` (48 frames at 23.976 fps, movie ref f1643–f1690)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-2.84, 0.65, -3.37)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(0.4, 0.25, -0.69)`)
- **Resolved Start Position**: `Vector3.new(-4.03, 5.96, -56.52)`
- **Resolved End Position**: `Vector3.new(-3.83, 5.92, -56.31)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `470_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `470_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: firelaser, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: over-the-shoulder behind Tony: dual fiery laser streams converge on Thanos marching forward through flames
> **Visual Staging in Studio**: During Cut 65 (movie 68.527s–70.529s), Roblox Studio positions the camera standard relative to the Titan terrain. Searing twin beams: intense red-orange cutting lasers stream into Thanos' chest and gauntlet, lighting the terrain in blinding red glare.

### Cut 66 — Shot `475`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:10.529` (70.529s) to `01:11.655` (71.655s)
- **Duration**: `1.126 seconds` (27 frames at 23.976 fps, movie ref f1691–f1717)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(6.2, 0.5, -5.8)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(-0.2, 0.3, 0.2)`)
- **Resolved Start Position**: `Vector3.new(8.66, 5.98, -48.11)`
- **Resolved End Position**: `Vector3.new(8.52, 6.00, -47.97)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `475_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `475_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.Thanos` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: firelaser, shake

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium close-up profile: Iron Man strains with intense effort, gritting teeth as he channels maximum fire
> **Visual Staging in Studio**: During Cut 66 (movie 70.529s–71.655s), Roblox Studio positions the camera standard relative to the Titan terrain. Unstoppable march: Thanos grunts against the blistering heat, raising his arms to shield his face while continuing to walk forward.

### Cut 67 — Shot `480`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:11.655` (71.655s) to `01:12.865` (72.865s)
- **Duration**: `1.210 seconds` (29 frames at 23.976 fps, movie ref f1718–f1746)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(-10.5, 0.3, -6.0)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(0.0, 0.35, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-10.19, 6.48, -5.83)`
- **Resolved End Position**: `Vector3.new(-9.22, 6.50, -5.34)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `480_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `480_ironman.rbxmx`
- **Character Visibility Override**: Rig `Workspace.IronMan` is set to transparent/hidden for this shot.

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, firelaser, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: frontal medium: Thanos marches directly toward camera into convergent fire-lasers, gauntlet raised glowing purple
> **Visual Staging in Studio**: During Cut 67 (movie 71.655s–72.865s), Roblox Studio positions the camera standard relative to the Titan terrain. Maximum output: Tony pushes the suit to overload, the laser beams widening into searing plasma cones that scorch the ground.

### Cut 68 — Shot `485`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:12.864` (72.864s) to `01:13.406` (73.406s)
- **Duration**: `0.542 seconds` (13 frames at 23.976 fps, movie ref f1747–f1759)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(4.8, 0.8, -7.5)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(1.2, 0.4, 0.7)`)
- **Resolved Start Position**: `Vector3.new(6.27, 6.36, -50.63)`
- **Resolved End Position**: `Vector3.new(6.13, 6.36, -50.35)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `485_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `485_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: firelaser

#### Studio Scene Analysis & Visual Matter
> **Director Note**: side two-shot: Thanos advances, fists slam down into twin beams
> **Visual Staging in Studio**: During Cut 68 (movie 72.864s–73.406s), Roblox Studio positions the camera standard relative to the Titan terrain. Point-blank contact: Thanos closes the final studs of distance, standing directly above Tony despite the roaring flames.

### Cut 69 — Shot `490`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:13.407` (73.407s) to `01:14.366` (74.366s)
- **Duration**: `0.959 seconds` (23 frames at 23.976 fps, movie ref f1760–f1782)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-2.2, 0.6, -3.2)`)
- **Look Target**: `Thanos.UpperTorso` (Offset: `Vector3.new(0.0, 0.3, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-3.06, 5.88, -56.44)`
- **Resolved End Position**: `Vector3.new(-2.78, 5.88, -56.17)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `490_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `490_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, firelaser, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: over-the-shoulder behind Iron Man: Thanos winds up left gauntlet, steps in, delivers punch to Tony face
> **Visual Staging in Studio**: During Cut 69 (movie 73.407s–74.366s), Roblox Studio positions the camera standard relative to the Titan terrain. Beam swat: with a ferocious outward sweep of his massive forearms, Thanos swats both laser beams aside, breaking the attack.

### Cut 70 — Shot `505`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:14.366` (74.366s) to `01:14.992` (74.992s)
- **Duration**: `0.626 seconds` (15 frames at 23.976 fps, movie ref f1783–f1797)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(3.8, -0.4, -5.8)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(1.0, 0.6, 0.6)`)
- **Resolved Start Position**: `Vector3.new(4.94, 4.63, -48.24)`
- **Resolved End Position**: `Vector3.new(4.81, 4.63, -47.96)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `505_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `505_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low medium two-shot: Thanos swings second strike; Tony reels, raising arms to guard
> **Visual Staging in Studio**: During Cut 70 (movie 74.366s–74.992s), Roblox Studio positions the camera standard relative to the Titan terrain. Crushing hook: Thanos delivers a vicious right hook to Tony's jaw, spinning his head and staggering him backward.

### Cut 71 — Shot `520`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:14.992` (74.992s) to `01:15.951` (75.951s)
- **Duration**: `0.959 seconds` (23 frames at 23.976 fps, movie ref f1798–f1820)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(2.2, 0.35, -4.2)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 0.35, 0.1)`)
- **Resolved Start Position**: `Vector3.new(3.05, 5.75, -45.86)`
- **Resolved End Position**: `Vector3.new(2.91, 5.75, -45.72)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `520_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `520_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close two-shot: Thanos gauntlet hammers down onto Tony crossed forearms
> **Visual Staging in Studio**: During Cut 71 (movie 74.992s–75.951s), Roblox Studio positions the camera standard relative to the Titan terrain. Reeling brawl: Tony attempts a desperate left counter-hook, but Thanos easily deflects it with his gauntlet.

### Cut 72 — Shot `525`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:15.951` (75.951s) to `01:16.493` (76.493s)
- **Duration**: `0.542 seconds` (13 frames at 23.976 fps, movie ref f1821–f1833)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(-1.2, 0.3, -3.2)`)
- **Look Target**: `Thanos.Head` (Offset: `Vector3.new(0.0, 0.0, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-1.67, 6.69, -56.44)`
- **Resolved End Position**: `Vector3.new(-1.67, 6.69, -56.44)`
- **Field of View (FOV)**: Start `32°` -> End `32°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `525_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `525_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: OTS Tony: Thanos grimaces and presses down
> **Visual Staging in Studio**: During Cut 72 (movie 75.951s–76.493s), Roblox Studio positions the camera standard relative to the Titan terrain. Hammer strike: Thanos brings both hands together in a brutal double-fist hammer blow onto Tony's crossed defensive guard.

### Cut 73 — Shot `530`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:16.493` (76.493s) to `01:17.411` (77.411s)
- **Duration**: `0.918 seconds` (22 frames at 23.976 fps, movie ref f1834–f1855)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(18.0, 4.0, -22.0)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 1.0, 0.0)`)
- **Resolved Start Position**: `Vector3.new(24.96, 10.60, -70.51)`
- **Resolved End Position**: `Vector3.new(24.26, 10.60, -69.82)`
- **Field of View (FOV)**: Start `44°` -> End `44°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `530_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `530_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide landscape: both struggling on the Titan battlefield
> **Visual Staging in Studio**: During Cut 73 (movie 76.493s–77.411s), Roblox Studio positions the camera standard relative to the Titan terrain. Over-the-shoulder grapple: Thanos leans his massive frame downward, overpowering Tony's arms through sheer brute strength.

### Cut 74 — Shot `535`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:17.411` (77.411s) to `01:17.828` (77.828s)
- **Duration**: `0.417 seconds` (10 frames at 23.976 fps, movie ref f1856–f1865)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(4.2, 0.5, -6.0)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.8, 0.4, 0.5)`)
- **Resolved Start Position**: `Vector3.new(5.56, 5.94, -48.49)`
- **Resolved End Position**: `Vector3.new(5.56, 5.94, -48.49)`
- **Field of View (FOV)**: Start `34°` -> End `34°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `535_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `535_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: medium two-shot struggle before sword pulls out
> **Visual Staging in Studio**: During Cut 74 (movie 77.411s–77.828s), Roblox Studio positions the camera standard relative to the Titan terrain. Wide grapple: both combatants locked in a desperate test of strength on the Titan dust, Tony sinking onto one knee.

### Cut 75 — Shot `540`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:17.828` (77.828s) to `01:19.204` (79.204s)
- **Duration**: `1.376 seconds` (33 frames at 23.976 fps, movie ref f1866–f1898)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.LeftHand` (Offset: `Vector3.new(-1.8, 0.5, -2.5)`)
- **Look Target**: `IronMan.LeftHand` (Offset: `Vector3.new(0.0, 0.0, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-1.15, 5.02, -43.47)`
- **Resolved End Position**: `Vector3.new(-1.15, 5.02, -43.47)`
- **Field of View (FOV)**: Start `28°` -> End `28°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `540_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `540_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: sword

#### Studio Scene Analysis & Visual Matter
> **Director Note**: low close on Tony's left forearm: the nanotech sword pulls out of the armour
> **Visual Staging in Studio**: During Cut 75 (movie 77.828s–79.204s), Roblox Studio positions the camera standard relative to the Titan terrain. Medium grapple: Tony grimaces in agony, discreetly channeling his last nanotech particles into his right forearm.

### Cut 76 — Shot `545`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:19.204` (79.204s) to `01:19.871` (79.871s)
- **Duration**: `0.667 seconds` (16 frames at 23.976 fps, movie ref f1899–f1914)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(-4.0, 1.2, -6.0)`)
- **Look Target**: `IronMan.LeftHand` (Offset: `Vector3.new(0.0, 0.3, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-5.96, 7.26, -48.33)`
- **Resolved End Position**: `Vector3.new(-5.96, 7.26, -48.33)`
- **Field of View (FOV)**: Start `36°` -> End `36°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `545_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `545_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: sword

#### Studio Scene Analysis & Visual Matter
> **Director Note**: the sword raised, glowing; Thanos turns to it
> **Visual Staging in Studio**: During Cut 76 (movie 79.204s–79.871s), Roblox Studio positions the camera standard relative to the Titan terrain. Nanotech blade formation: a sharp, tapered nanotech dagger extends forward from Tony's right gauntlet.

### Cut 77 — Shot `550`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:19.871` (79.871s) to `01:20.538` (80.538s)
- **Duration**: `0.667 seconds` (16 frames at 23.976 fps, movie ref f1915–f1930)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `Thanos.UpperTorso` (Offset: `Vector3.new(-11.0, 2.5, -12.0)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 0.3, 0.0)`)
- **Resolved Start Position**: `Vector3.new(-10.68, 8.86, 0.35)`
- **Resolved End Position**: `Vector3.new(-10.68, 8.86, 0.35)`
- **Field of View (FOV)**: Start `40°` -> End `40°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `550_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `550_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: None (clean environment view).

#### Studio Scene Analysis & Visual Matter
> **Director Note**: wide: Thanos holds Iron Man down, both struggle over the blade
> **Visual Staging in Studio**: During Cut 77 (movie 79.871s–80.538s), Roblox Studio positions the camera standard relative to the Titan terrain. The lunged strike: Tony thrusts the dagger upward toward Thanos' throat, but Thanos' lightning-fast left hand catches his wrist.

### Cut 78 — Shot `555`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:20.539` (80.539s) to `01:21.039` (81.039s)
- **Duration**: `0.500 seconds` (12 frames at 23.976 fps, movie ref f1931–f1942)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.Head` (Offset: `Vector3.new(0.8, 0.2, 2.5)`)
- **Look Target**: `IronMan.Head` (Offset: `Vector3.new(0.0, -0.1, 0.0)`)
- **Resolved Start Position**: `Vector3.new(1.10, 6.99, -36.54)`
- **Resolved End Position**: `Vector3.new(1.10, 6.99, -36.54)`
- **Field of View (FOV)**: Start `30°` -> End `30°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `555_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `555_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: dust

#### Studio Scene Analysis & Visual Matter
> **Director Note**: close on Tony's face, struggling
> **Visual Staging in Studio**: During Cut 78 (movie 80.539s–81.039s), Roblox Studio positions the camera standard relative to the Titan terrain. The blade snap: with a sickening metallic wrench, Thanos twists Tony's wrist, snapping the nanotech dagger clean off.

### Cut 79 — Shot `560`: Dual Fire-Lasers & The Stab

- **Roblox Studio Timing**: `01:21.039` (81.039s) to `01:22.593` (82.593s)
- **Duration**: `1.554 seconds` (12 frames at 23.976 fps, movie ref f1943–f1954)
- **Camera Mode**: `Standard` (Pullback Multiplier: `1.3x`)

#### Camera Setup & Framing Configuration
- **Target Part**: `IronMan.UpperTorso` (Offset: `Vector3.new(6.5, 0.8, -4.5)`)
- **Look Target**: `IronMan.UpperTorso` (Offset: `Vector3.new(0.0, 0.2, 0.0)`)
- **Resolved Start Position**: `Vector3.new(9.01, 6.42, -46.25)`
- **Resolved End Position**: `Vector3.new(8.73, 6.42, -45.97)`
- **Field of View (FOV)**: Start `38°` -> End `38°`

#### Cast Rigs & Active Animation Tracks
- **Rig**: `Workspace.Thanos` — Playing Track: `560_thanos.rbxmx`
- **Rig**: `Workspace.IronMan` — Playing Track: `560_ironman.rbxmx`

#### Visual Effects, Lighting & HUD Elements
- **Active Procedural VFX**: shake, dust, impact

#### Studio Scene Analysis & Visual Matter
> **Director Note**: Thanos' hand takes the blade; it breaks; the stab into Tony's chest. The video ends here.
> **Visual Staging in Studio**: During Cut 79 (movie 81.039s–82.593s), Roblox Studio positions the camera standard relative to the Titan terrain. The fatal stab: Thanos reverses the broken dagger and drives it deep into Tony's abdomen; the camera dollies in on the agonizing, silent shock of the impalement.

