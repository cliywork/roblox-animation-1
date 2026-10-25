# Pipeline — how the project is built

## Folders

```
3d Animation/
  AGENTS.md, CLAUDE.md        entry point for agents
  realvideo-camera.md         MANDATORY camera scene setup reference (all 79 cuts, timings, angles, motions)
  docs/                       this handoff pack
  shot_log.csv                the original 62-shot plan (shot, movie in/out, action, vfx, camera)
  reference/                  the movie reference clips (see "Reference videos")
  colab_cells.py              Google Colab GVHMR motion-capture cells (SETUP + one SHOT cell per take)
  roblox_pipeline/            everything that builds the Roblox scene (Rojo project root)
    scene.py                  THE EDIT: poses, timeline, cameras, FX, subtitles  ->  shots/ + SceneData.lua
    rbxmx_io.py               read/write KeyframeSequence .rbxmx files
    smpl_to_r15.py            GVHMR (SMPL) capture -> R15 KeyframeSequence (R15 joint tree lives here)
    preview.py                stick-figure render of the planned cameras beside reference frames (offline check)
    shot_table.py             writes docs/SHOTS.md from scene.py
    captures/                 raw mocap clips (only 050 is used; 010/030 kept for reference)
    shots/                    GENERATED animations, one KeyframeSequence per shot per rig
    SceneData.lua             GENERATED timeline/camera/FX data (do not edit)
    ShotPlayer.server.lua     server: cast setup, animation playback, scrub / PlayFrom
    Director.client.lua       client: camera, letterbox, overlay, subtitles, HUD, lights, ALL VFX
    ShotButtons.client.lua    on-screen shot panel (P = play scene, F replay, Q/E prev/next)
    VFXAssets.lua             vetted particle textures (image ids + flipbook layout)
    Costumes.lua              built costume for plain dummies (unused while the owner's models are cast)
    titan_set.lua             Titan battlefield builder (terrain, wreckage, sky, lighting)
    default.project.json      Rojo mapping
```

Rojo maps: `SceneData`, `VFXAssets` → ReplicatedStorage · `shots/` (as `Shots`), `TitanSetBuilder`,
`Costumes` → ServerStorage · `ShotPlayer` → ServerScriptService · `Director`, `ShotButtons` →
StarterPlayer.StarterPlayerScripts.

## Data flow

```
realvideo-camera.md (79 cuts) ──(mandates camera framing, angles, motions, timings)──┐
                                                                                     ▼
reference video ──(frame sheets, cut detection)──────────────────────────► decisions in scene.py

captures/*.rbxmx (mocap) ─┐
hand-keyed poses ─────────┼─► scene.py build_shots() ─► shots/NNN_rig.rbxmx ─┐
TIMELINE / FX / SUBS ─────┘                         └─► SceneData.lua ──────┤
                                                                            ▼ Rojo
                        Studio: ShotPlayer plays animations on the rigs, Director moves the
                        camera, draws HUD/subtitles/overlay and every effect, all from SceneData.
```

Run `python scene.py` inside `roblox_pipeline/` after every edit (takes ~5 s). It prints contact
shortfalls (`contact`, `pin`, `hit`, `punch`, `brow touch` lines): anything above ~0.5 studs is a
visible miss and must be fixed.

## Camera scene setup (Mandatory Reference: `realvideo-camera.md`)

All camera placements, field of view (FOV), framing angles, camera movements, and cut timings in `scene.py` must strictly follow **`realvideo-camera.md`**.
- It provides all **79 cuts** of the real video reference with pinpoint timings (seconds + mm:ss.ms), frame indices, shot framing, camera motion, and action matter.
- In `scene.py`, timeline camera entries are defined under `TIMELINE`:
  ```python
  dict(shot="425", start=58.774, dur=0.5, play={"IronMan": "425_ironman", "Thanos": "425_thanos"},
       hud="mask" | "lock" (optional), hide="Thanos" | "IronMan" (optional: cheat a rig out of frame),
       note="what the shot must show",
       cam=[dict(t=0.0, pos=(target, offset), look=(target, offset), fov=35), dict(t=dur, ...)])
  ```
- `target` is `"Rig.Part"` (follows the part; offset is in world studs × the rig's SizeRatio) or
  `"World"` (offset is an absolute world point).
- The Director dollies every camera back along its line of sight by **PULLBACK = 1.3**. To put the
  real camera at world point C looking at L, write `pos = L + (C − L) / 1.3` (World targets), or
  divide part-relative offsets by 1.3 and by the rig's SizeRatio (**Thanos 0.75, Iron Man 1.07**
  with the owner's models).
- `fov` is the vertical FOV of the 1920×1010 movie frame. Frame height at distance D is
  `2·D·tan(fov/2)`; plan D from the size you want, don't guess.

## Environment and tools

- **Rojo 7.7.1** (`~/.aftman/bin/rojo.exe`). Start it from `roblox_pipeline/`:
  `~/.aftman/bin/rojo.exe serve default.project.json`, then click **Connect** in Studio's Rojo
  plugin. A Rojo server started as an agent background task dies when the agent session ends; the
  owner prefers running it in their own terminal. "Address already in use" = one is already running.
- Rojo sync can lag a few seconds. Before testing, confirm in the **Edit** datamodel that the new
  source arrived (e.g. `ReplicatedStorage.SceneData.Source:find('shot = "425"')`).
- **Roblox Studio MCP** gives the agent `execute_luau`, `screen_capture`, `start_stop_play`, etc.
  The `studio_id` changes whenever Studio restarts: call `list_roblox_studios` first. If the server
  fails with a protocol-version error after a Studio auto-update, reconnect the MCP server (or start
  a new agent session); the launcher is `%LOCALAPPDATA%\Roblox\mcp.bat`, or configured for Antigravity
  in `%USERPROFILE%\.gemini\antigravity\mcp_config.json`.
- Python 3.13 (WindowsApps) with numpy, scipy, opencv (`cv2`). No ffmpeg; use cv2 for frames.
- **Lighting.Technology must be Future** (owner set it; scripts can't read or set it).

## Reference videos (in `reference/`)

| File | Covers | Frame 0 is movie time |
|---|---|---|
| `…_5.88sec clip for claude.mp4` | 0–5.88 s | 0.000 |
| `Iron Man vs Thanos -05.888sec-18.10seconds.mp4` | 5.888–18.1 s | 5.888 (clip frame 0 = movie frame 141) |
| `Iron Man vs Thanos - 18sec.1 -1min22sec.6 full video  .mp4` | 15.856–82.6 s | **15.856** (despite the name) |

All clips are 23.976 fps, 1920×1010 (letterboxed). For the full video:
**movie t = 15.856 + clip_frame / 23.976**, movie frame = round(t × 23.976). Seek with
`CAP_PROP_POS_FRAMES`, never `CAP_PROP_POS_MSEC` (inaccurate).

## Stage and coordinates (studs)

- Ground along the fight line renders at **y = STAGE_Y = 1.95** (terrain surface; measured).
- **Thanos** rig: mark (0, 1.95, 0), yaw 0 → faces world **−Z**, scale **1.35**. His left is −X.
- **Iron Man** rig: mark (0, 1.95, −40), yaw 180 → faces world **+Z**. Scale 1.0.
- Rig-local convention in scene.py: body faces −Z, character's left is −X, up +Y.
- Thanos rig → world: world = rig × 1.35 (no turn). Iron Man rig → world: world_x = −rig_x,
  world_z = −40 − rig_z (yaw 180). `world_point(rig, pose, part)` / `to_rig(rig, world)` do this
  for you. Use them; hand conversions have caused sign bugs.
- HumanoidRootPart stays **anchored on the mark**; all motion is on LowerTorso (animation). So
  camera targets for a moving character must be `LowerTorso` / `UpperTorso` / `Head`, never the root.

## scene.py API (what you use when building a chunk)

Pose building (rig space, directions are unit-ish vectors):
- `make_pose(torso=(yaw, lean), head=(pitch, yaw[, roll]), L_up, L_lo, L_hand, L_palm, R_…, stance)`
- `orient(q, part, direction, palm=None)`, `set_head`, `with_head(pose, pitch, yaw, roll)`
- `limbs(base, arms=(upper, lower), legs=(thigh, shin), palm)`: mirrored left/right
- `arm(pose, side, up, lo, hand=None, palm=None)`: one arm, `kneel(pose)`: down on the right knee
- `moved(pose, d, h, pitch, x, yaw)`: whole body forward/up/pitch(back)/side/turn
- `blend(a, b, w)`, `keyed([(t, pose)…], dur)` for simple shots

Continuous multi-cut action (used from shot 140 on). This is the pattern for every new chunk:
- `IM_POSES`, `TH_POSES`: `[(movie_t, pose)]` key lists; `at_keys(t, keys)` blends them.
- Channels (`chan(t, [(t, value)…])`): Iron Man `IM_D`, `IM_D2`, `IM_H`, `IM_PITCH`, `IM_X`,
  `IM_YAW`, `IM_WX`/`IM_WZ` (world offsets); Thanos `TH_BACK`, `TH_STEP`, `TH_DROP`, `TH_YAW`,
  `TH_WX`/`TH_WZ`.
- `im_fight(t)`, `th_fight(t)` return the pose at movie time t. `FIGHT_SHOTS` slices them per shot.
- **Contacts** (IK): `reach(pose, rig, side, target_world, pole, palm)` solves a two-bone arm onto a
  world point and returns `(pose, shortfall)`. Hits/grabs are solved onto the other rig's part at
  that exact time (`CONTACTS`, the pin loop, the punch blocks). Print shortfalls; fix > 0.5.
- **Hit reactions**: `FIGHT_HITS` entries `(t, rig, part, push_dir_rig, degrees)` are applied with
  `react()` to every slice that contains the hit (see VFX_AND_PHYSICS.md).

## Studio runtime (what the Lua does)

- **ShotPlayer.server.lua**: finds `Workspace.IronMan` / `Workspace.Thanos` (renames Dummies if
  missing), paints Iron Man's red Metal plates as SmoothPlastic (Metal goes black on Titan), tags
  the faceplate `HideInHUD`, measures height → `SizeRatio`, places each rig by its lowest body part
  on the mark, settles it in a standing pose, **preloads every track** (lazy loading made short
  shots miss their cuts), plays the scene on the movie timeline.
  - `ReplicatedStorage` attribute **`ScrubFrame`** = movie frame → freeze everything on that frame.
  - attribute **`PlayFrom`** = movie seconds → play live from there (clears itself).
- **Director.client.lua**: camera from SceneData, letterbox to the movie aspect, overlay
  `FRAME / time / SHOT`, subtitles, helmet HUD, per-character key lights, `hide`, all FX, camera shake.
- **titan_set.lua**: run once in EDIT mode: `require(game.ServerStorage.TitanSetBuilder:Clone())`.
  Rebuilds terrain, `Workspace.TitanSet`, lighting (OutdoorAmbient 140,116,92, EnvDiffuse 0.8,
  EnvSpecular 1). Results live in the place file: the owner must save.

## The cast

- `Workspace.IronMan`: owner's detailed Mark 50 (R15). Helmet model + faceplate tagged `HideInHUD`
  (hidden in HUD shots and by the helmet-break FX). Its hair accessory is invisible.
- `Workspace.Thanos`: owner's model, re-rigged by an agent (added HumanoidRootPart + LeftHand, 15
  Motor6Ds from the rig attachments, gauntlet sub-model welded to LeftHand at its original offset).
- Both keep armour in sub-Models named like body parts: always pick the **BasePart** child when you
  look up `Rig.Part` (Director `findPart` does this).
- Originals and old dummies: `ServerStorage.UserModelBackup`.

## Recipe: building the next chunk

1. **Check `realvideo-camera.md`**: Consult the mandatory camera cut breakdown for the chunk's exact
   timings, frames, camera framing, angles, camera motions, and scene matter.
2. Read the owner's beat sheet (`docs/STORY_BEATS.md`) and compare with the reference frames.
3. Add the cuts to `FIGHT_SHOTS`; add pose keys/channels to `IM_POSES`/`TH_POSES` etc. Keep the
   action continuous across cuts.
4. Solve every touch with `reach()`; add every impact to `FIGHT_HITS`. Run `python scene.py`;
   fix shortfalls and check no body part sinks below y = 1.95 (see VERIFICATION.md).
5. Write cameras in `scene.py` conforming strictly to `realvideo-camera.md` using the PULLBACK formula.
6. Add FX entries (`FX += [...]`) for every hit, dust, energy and glow. Add subtitles.
7. Studio: confirm sync → playtest → scrub each shot at the reference frames → screenshot → compare
   → fix → repeat. Then one live `PlayFrom` pass for particles/trails.
8. Update `docs/STATUS.md` and `docs/POLISH.md` and report to the owner.
