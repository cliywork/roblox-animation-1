# AGENTS.md — start here

You are continuing a **shot-for-shot Roblox recreation of the Iron Man vs Thanos "Battle of Titan"
fight** (Avengers: Infinity War, movie time 0:00–1:22.6) for a YouTube video. The output is a
**video recorded from Roblox Studio**, not a game, so realism wins over normal Roblox conventions.

Read these, in order, before touching anything:

| File | What it gives you |
|---|---|
| [realvideo-camera.md](realvideo-camera.md) | **MANDATORY camera scene setup reference.** All 79 cuts of the real video reference with pinpoint timings, frame ranges, framing/angles, camera motion, and scene matter. Every camera in Roblox must conform to this. |
| [docs/STATUS.md](docs/STATUS.md) | What is built, what is verified, open problems |
| [docs/POLISH.md](docs/POLISH.md) | **Timeline of polish passes.** Polish 1 filled where done; empty rows still need work |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | **The fix loop: sheet to Argon to Antigravity to Studio to compare. Start here** |
| [docs/FIXES.md](docs/FIXES.md) | **What is wrong in each chunk, and the fix to make** |
| [docs/STORY_BEATS.md](docs/STORY_BEATS.md) | The owner's beat sheet (0:00–1:22.6) and how beats map to shots |
| [docs/PIPELINE.md](docs/PIPELINE.md) | Files, data flow, coordinates, scene.py API, how to build a chunk |
| [docs/VFX_AND_PHYSICS.md](docs/VFX_AND_PHYSICS.md) | The quality bar, FX kinds, particle assets, hit reactions, IK contacts |
| [docs/VERIFICATION.md](docs/VERIFICATION.md) | How to check a shot against the movie, the owner's taste, known traps |
| [docs/SHOTS.md](docs/SHOTS.md) | Generated table of every shot (`python roblox_pipeline/shot_table.py`) |
| [docs/images/threeway/](docs/images/threeway/) | **Three-way sheets per chunk (movie / wireframe / Roblox)** |
| [analysis/](analysis/) | Reference frames, cut lists, compare tools (`analysis/tools/`) |

## The rules that matter most

1. **`realvideo-camera.md` is the MANDATORY camera scene setup reference for Roblox.**
   Every shot's camera perspective, FOV, framing angle, camera motion, and cut timing in `roblox_pipeline/scene.py`
   and `Director.client.lua` must strictly conform to the 79-cut breakdown in `realvideo-camera.md`. No agent may
   guess camera angles or invent timings; every camera setup must follow its corresponding cut in `realvideo-camera.md`.
2. **`roblox_pipeline/scene.py` is the single source of truth.** Never hand-edit `SceneData.lua`
   or `shots/*.rbxmx`; edit `scene.py` and run `python scene.py` (from `roblox_pipeline/`).
   Rojo syncs the outputs into Studio.
3. **Work in ~5-second chunks of movie time**, cut by cut, matched to the reference video.
   The owner asked for chunks to be done back to back **without asking**, with a short report
   after each one. Ask only when truly blocked (Studio not connected, a decision only they can make).
4. **Verify in Studio, not in your head.** Every shot gets scrubbed to exact movie frames and
   screenshotted next to the same reference frame. "Should look right" is not acceptable.
5. **Quality bar is the top priority:** real-looking smoke/dust/blasts, bodies that react to the
   speed of every hit, contacts that actually touch. See VFX_AND_PHYSICS.md.
6. **Anything that changes the owner's place** (terrain, lighting, models in Workspace) is saved in
   the .rbxl, not in git/Rojo. Tell the owner, and remind them to save the place.
7. The cast are **the owner's own models** (`Workspace.IronMan`, `Workspace.Thanos`). Do not replace
   them. Backups live in `ServerStorage.UserModelBackup`.
