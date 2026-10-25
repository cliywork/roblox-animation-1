# Workflow: how one chunk gets fixed (Argon review + Antigravity build)

The loop, per chunk (a few shots, one three-way sheet):

1. **Three-way sheet** (`docs/images/threeway/chunk_sheets/`): MOVIE | PYTHON LINE | ROBLOX STUDIO, one row per shot.
   Single images per shot are in `real/`, `python_line/` and `roblox/`. After any change, rebuild with
   `python analysis/tools/build_threeway_set.py sheets`. Naming and reference files: `docs/images/threeway/README.md`.
2. **Argon** reads the sheet and writes the change list (one line per shot: what is wrong, fix type, exact target).
3. **Antigravity** takes the sheet + Argon's list + `docs/FIXES.md` for that chunk + `docs/ANTIGRAVITY.md` (the brief) + **`realvideo-camera.md` (mandatory camera scene setup reference)**, then:
   a. draws a python wireframe of the fixed pose/camera (`roblox_pipeline/preview.py`) and compares it with the movie frame;
   b. if the wireframe does not match the fix, redraws it, until it matches closely;
   c. only then implements the change in `scene.py` / `Director.client.lua`, runs `python scene.py` (2–3 min, run in background);
   d. captures Roblox Studio at the same moment (`ScrubFrame` on the Server, then `screen_capture`);
   e. compares real movie vs Roblox. If the difference is a **camera** problem (framing, distance, angle, movement), fix the camera strictly according to the mandatory setup specifications in `realvideo-camera.md`.
      Otherwise fix the pose/FX/light. Report which it was.
4. Record the result in `docs/POLISH.md` (Polish 1 cell, or a new Polish table). Mark only what was checked in Studio.

## Rules
- **Camera setup is mandatory from `realvideo-camera.md`**: Camera framing, angle, motion, and exact cut timings must strictly conform to the 79-cut breakdown in `realvideo-camera.md`.
- Scene data (`scene.py`) is the only place for poses, cameras and timing. Director code only for effects and look.
- Every claim needs a Studio capture. Wireframes are schematic; the movie frame is the truth.
- Build in the background (2–3 min). Never back up into the live folders; copy to `roblox_pipeline/backup/` first.
- Studio: the `studio_id` changes after a restart (call `list_roblox_studios`). Rojo: the owner clicks Connect.

## Files
| File | Use |
|---|---|
| `realvideo-camera.md` | **MANDATORY camera scene setup reference** (79 cuts, pinpoint timings, angles, camera motions, and scene matter) |
| `docs/ANTIGRAVITY.md` | the brief for the build agent: steps, rules, report format |
| `docs/images/threeway/chunk_sheets/` | the sheets (movie / python line / Roblox) |
| `docs/images/threeway/real/`, `python_line/`, `roblox/` | single images per shot, named `<shot>.jpg` |
| `docs/FIXES.md` | per chunk: what is wrong, what it should be, the fix to make |
| `docs/POLISH.md` | timeline of polish passes (done / open) |
| `docs/STATUS.md`, `docs/VERIFICATION.md` | state and checks |
| `analysis/threeway_all/` | wireframe renders, moment list, the Studio capture list |
| `analysis/tools/` | `threeway.py`, `compare_studio.py`, `measure_look.py`, `make_analysis.py` |
