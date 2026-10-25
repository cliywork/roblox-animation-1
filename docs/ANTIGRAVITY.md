# Antigravity brief: fix one chunk

Use this with the chunk sheet and Argon's change list. Read it once per session, then follow the steps.

## You are given
1. A chunk sheet: `docs/images/threeway/chunk_sheets/chunk_<n>_<name>.jpg` (or `_part1` / `_part2`).
   One row per shot: MOVIE | PYTHON LINE | ROBLOX STUDIO.
2. The same three images for each shot, as single files:
   `docs/images/threeway/real/<shot>.jpg`, `python_line/<shot>.jpg`, `roblox/<shot>.jpg`.
3. Argon's change list (format below).
4. The chunk's section in `docs/FIXES.md`.
5. **`realvideo-camera.md`**: The **MANDATORY camera scene setup reference** (79 cuts, pinpoint timings, framing, angles, camera motions, and action matter). Every camera setup in Roblox must conform to this.

Read first: `AGENTS.md`, `realvideo-camera.md`, `docs/WORKFLOW.md`, `docs/VERIFICATION.md` (scrub recipe), `docs/images/threeway/README.md`.

## What Argon should give you (one line per shot)
`shot | what the movie shows | what Roblox shows | fix type | exact target`

- **fix type**: `camera`, `pose`, `FX`, `light`, or `contact`.
- **exact target**: a number or a clear position, e.g. "camera 3 studs closer, lower to ankle height",
  "right hand 0.8 studs further forward", "beam colour blue (40,130,255)". Not "make it better".

If a shot has no target, do not guess: report it and skip it.

## Per shot, in this order
1. Compare the three images for the shot. Confirm the problem is what Argon says. If not, say so.
2. Check `realvideo-camera.md` for the shot's mandatory camera framing, angle, and camera motion.
3. Fix the **wireframe first**: change the pose or camera in the python render until
   `python_line/<shot>.jpg` matches the movie frame closely. Run `roblox_pipeline/preview.py` for that moment.
4. Implement the same change:
   - camera, pose, timing: `roblox_pipeline/scene.py` only (cameras must match `realvideo-camera.md`).
   - FX, light, colour: `roblox_pipeline/Director.client.lua` (or `scene.py` for FX entries).
   - Never hand-edit `SceneData.lua` or `shots/*.rbxmx`.
5. Build: `cd roblox_pipeline` then `python scene.py`. It takes 2–3 minutes, so run it in the background.
   Check the build printed no traceback.
6. Check the change arrived in Studio (Edit datamodel, `ReplicatedStorage.SceneData.Source`).
   Rojo can lag 10–60 seconds. Rojo is run by the owner; never start a second Rojo server.
7. Capture the shot in Studio (Roblox MCP):
   - `list_roblox_studios` to get the `studio_id` (it changes after a restart).
   - `start_stop_play(true)`, wait about 10 s for `N/N tracks preloaded`.
   - From a **Server** `execute_luau`: `game.ReplicatedStorage:SetAttribute("ScrubFrame", round(t * 23.976))`, then wait 1.2 s.
   - `screen_capture`. The top-left label shows the frame and shot. Check it.
   - Save the capture to `docs/images/threeway/roblox/<shot>.jpg` (overwrite).
   - After the chunk: `start_stop_play(false)`.
8. If the wireframe changed, the stick figure must be redrawn too:
   `python analysis/tools/build_threeway_set.py python` (this rewrites `python_line/`).
9. Rebuild the sheets: `python analysis/tools/build_threeway_set.py sheets`.

## Rules
- **Camera setup is mandatory from `realvideo-camera.md`**: Camera framing, perspective, FOV, motion, and exact cut timings must strictly conform to `realvideo-camera.md`. No agent may guess camera setups.
- `scene.py` is the source of truth for poses, cameras and timing. The Director is for effects and look only.
- Movie frame is the truth. Wireframes are schematic.
- Every "fixed" claim needs a Studio capture from this session. If you did not capture it, say "not checked".
- Say which it was for each fix: camera, pose, or FX/light. If you fixed a camera problem, do not also
  claim a pose fix.
- Never replace the owner's models in `Workspace.IronMan` / `Workspace.Thanos`.
- Back up before a risky edit: copy to `roblox_pipeline/backup/`. Keep only the newest 3 per file.
- Do not delete files. Do not download anything without asking.
- The reference video ends at movie 81.547 s. Shot 560 has no movie frame.

## Traps seen before
- **Flat brown or grey screen** = the Director errored, or the camera is inside a rig. Read
  `get_console_output` for a parse error. A parse error means the whole Director is off.
- **Mask face**: the open mask-face problem is in `docs/FIXES.md` (mask face visibility). Do not
  change face decals for other shots to fix it.
- `Edit` datamodel is not available during Play. Stop play before reading it.
- "Target is not reachable" is transient: wait and retry.
- The shot panel can appear and cover the capture when the scene is not running. Restart play.

## Report back (one table per chunk)
| shot | problem | cause (camera / pose / FX / light) | change made | capture file | checked in Studio |
|---|---|---|---|---|---|

Then: the files you changed, the sheet path you rebuilt, and anything you did not finish.
Update `docs/POLISH.md` only for the shots you checked in Studio.
