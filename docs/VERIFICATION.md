# Verification — checking shots against the movie, and the owner's taste

## The owner's taste (from their feedback)

- **Always show the overlay** `FRAME nnn  t.ttts  SHOT nnn` on screen during playback, so any
  moment in a recording maps straight to the reference. Never remove it from review builds.
- **Cameras: match the key/core moments closely; a different angle is fine** where it looks better
  in Roblox. It's a high-quality YouTube cinematic, not a frame-perfect replica.
- **Wider beats tighter.** The owner was happy when cameras were pulled back; when unsure, frame wider.
- **Senior-director rigor.** Verify with real frames (reference sheets + Studio screenshots).
  No "expected to look fine"; say what you checked and what you didn't.
- **Realism first** (see VFX_AND_PHYSICS.md quality bar). The owner noticed a pink-tinted, dark
  frame instantly; they judge from the picture, so you must too.
- Characters are the **owner's models**; the owner approved a "blocky but detailed Roblox" style.
- Report after each ~5 s chunk: what each shot shows, what you fixed after checking, what's not
  verified. Keep it plain; the owner is not a programmer.

## Reading the reference

- **Mandatory Camera Setup Reference (`realvideo-camera.md`)**: Consult `realvideo-camera.md` for the
  authoritative 79-cut breakdown, pinpoint timings, framing types, camera movements, and scene matter. Every
  camera in Roblox Studio must be verified against its cut definition in `realvideo-camera.md`.
- Cut detection (full video, clip frame i): compute a colour histogram per frame
  (`cv2.calcHist` 8×8×8 on a 160×84 thumbnail, normalised); a cut is a frame where the L1
  difference to the previous frame is > ~0.5 (grey-diff > 14 also works for hard cuts). Motion
  blur and flashes give runs of high values; pick the first frame of a stable run.
- Contact sheets: every 4–6 frames over the chunk, labelled with movie time; read them before
  planning poses and cameras.
- Exact frames: `cap.set(cv2.CAP_PROP_POS_FRAMES, round((t − 15.856) × 23.976))`.

## The Studio review loop (Roblox Studio MCP)

1. `list_roblox_studios` → studio_id. Check Rojo synced (Edit datamodel source contains your change).
2. `start_stop_play(true)`, wait ~8 s (tracks preload; console prints `N/N tracks preloaded`).
3. **Scrub**: from a **Server** `execute_luau`, set `game.ReplicatedStorage:SetAttribute("ScrubFrame", f)`
   (movie frame), wait ~0.8 s, `screen_capture`. Compare with the reference frame f and the camera setup in `realvideo-camera.md`.
4. **Live**: from a **Server** `execute_luau`, set attribute `PlayFrom = movie_seconds`, wait the
   lead-in (0.75 s) + offset, `screen_capture`. Use this for particles, trails and physics chunks.
5. Measure instead of guessing: read part positions in a scrub (server `execute_luau`), then place
   cameras with the PULLBACK formula (PIPELINE.md).
6. `start_stop_play(false)` before editing scripts; restart the playtest to load new SceneData.

Traps (all hit before):
- **Never wait inside a Client `execute_luau` during playback**: when it returns, Studio resets
  CameraType to Custom and the Director camera breaks. Drive everything from the Server.
- A **flat brown/grey screen** = the Director errored or a rig isn't where the camera looks. Read
  the client log (LogService errors) and print part positions.
- After a Studio restart, the studio_id changes and Rojo must be reconnected (owner clicks Connect).
- Running `titan_set` right after stopping a playtest can fail ("target not reachable"): check
  `get_studio_state` is Edit first.
- Screenshots of a burst: scrub to a frame just after the hit and capture within ~0.2 s.
- Camera offsets planned without the frame-height formula came out ~2× too tight.

## Offline checks (no Studio needed)

- `python scene.py`: contact shortfalls printed; fix > 0.5 studs.
- Ground: for each new shot, sample frames and check the lowest part centre per rig
  (`world_point` over `scene.CENTER` parts) ≥ ~2.1 and nothing below 1.95.
- `python preview.py <reference.mp4> <out_dir> --offset=15.856 t1 t2 …`: stick figures through
  the planned cameras beside reference frames (good for framing; Roblox renders ~1.3× tighter,
  already compensated by PULLBACK).
- These checks do not replace Studio screenshots; say so when you report.
