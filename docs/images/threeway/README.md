# Three-way set (movie | python line | Roblox Studio)

# agent should make sure if any python 3d line or roblox studio image got any fixes update them in here

> **Mandatory Camera Setup Reference**: Consult [`realvideo-camera.md`](../../../realvideo-camera.md) for the complete 79-cut breakdown of the reference video footage, including exact timings, camera angles, motions, and action matter. Every camera in Roblox must conform to it.

> **Mandatory Camera Setup Reference**: Consult [`realvideo-camera.md`](../../../realvideo-camera.md) for the complete 79-cut breakdown of the reference video footage, including exact timings, camera angles, motions, and action matter. Every camera in Roblox must conform to it.

## Folders and naming

| Folder | What it holds | File name | Made by |
|---|---|---|---|
| `real/` | MOVIE frame at the shot's middle moment | `<shot>.jpg` (e.g. `465.jpg`) | `analysis/tools/build_threeway_set.py real` (from `reference/`) |
| `python_line/` | Stick-figure render of the same moment (`roblox_pipeline/preview.py`) | `<shot>.jpg` | `analysis/tools/build_threeway_set.py python` |
| `roblox/` | Roblox Studio capture at the same frame (scrub frame, `[SCRUB]` label on top) | `<shot>.jpg` | copied in from the Studio capture; replace the file to update it |
| `chunk_sheets/` | MOVIE \| PYTHON LINE \| ROBLOX STUDIO, one row per shot, at most 12 rows per sheet | `chunk_<n>_<name>.jpg`, or `chunk_<n>_<name>_part1.jpg` / `_part2.jpg` when a chunk has more than 12 shots | `analysis/tools/build_threeway_set.py sheets` |

Shot ids are three digits (`010` ... `560`). Shot `213` has a Studio capture too.
The movie time and frame of each shot are in `analysis/threeway_all/moments.json` and in the table below.

## Reference video (the MOVIE column)

The movie frames come from three files in `reference/`. All are 23.976 fps. The black letterbox bars are
cropped automatically (`analysis/tools/make_analysis.py`, `active_rows`).

| File in `reference/` | Movie time it covers | Frames in file | Used for |
|---|---|---|---|
| `Iron Man vs Thanos - Battle of Titan Scene Avengers Infinity War_5.88sec clip for claude.mp4` | 0 to 5.881 s | 141 | shot time t < 5.888 s. File frame = round(t x 23.976) |
| `Iron Man vs Thanos -05.888sec-18.10seconds.mp4` | 5.888 to 18.07 s | 292 | shot time 5.888 s up to 15.856 s. File frame = round((t - 5.888) x 23.976) |
| `Iron Man vs Thanos - 18sec.1 -1min22sec.6 full video  .mp4` | 15.856 to 81.547 s | 1575 | shot time t >= 15.856 s. File frame = round((t - 15.856) x 23.976) |

- The full video is the only file that reaches the end of the scene. It starts at movie 15.856 s and ends at 81.547 s.
  Its first frame is not movie 0, so do not read a frame number from it as the movie frame.
- The two short clips are used only for the start. Above 15.856 s the full video is used even where a clip still runs.
- The code that picks the file for each time is `movie_frame()` in `analysis/tools/threeway.py`.
- `reference/compare/` also sits in that folder. It is not used by this set.

## How to update one image (for the next AI)

1. Fix the shot in Studio, scrub to its frame, and capture it.
2. Save the capture as `roblox/<shot>.jpg` (overwrite the old one). Only that one file changes.
3. Rebuild the sheets: `python analysis/tools/build_threeway_set.py sheets`
   (about one minute; it rewrites all `chunk_sheets/` files from the three folders).
4. If the stick figure is wrong, fix `roblox_pipeline/preview.py` or `scene.py`, then run
   `python analysis/tools/build_threeway_set.py python sheets`.
5. Never edit the sheets by hand. They are rebuilt from the folders.

To rebuild everything (movie frames, stick figures, sheets): `python analysis/tools/build_threeway_set.py`.
Run these from the repo root (`3d Animation/`).

## Chunks

| Chunk | Movie time | Shots | Sheet(s) |
|---|---|---|---|
| 1 standoff and dialogue | 0 to 18.1 s | 010 to 100 | `chunk_1_standoff_dialogue.jpg` |
| 2 missiles | 18.1 to 29.4 s | 110 to 185 | `chunk_2_missiles.jpg` |
| 3 helmet | 29.4 to 35.3 s | 190 to 230 | `chunk_3_helmet.jpg` |
| 4 beam | 35.3 to 45.6 s | 240 to 310 | `chunk_4_beam_part1.jpg`, `chunk_4_beam_part2.jpg` |
| 5 drop and blood | 45.6 to 52.8 s | 320 to 360 | `chunk_5_drop_blood.jpg` |
| 6 beatdown | 52.8 to 58.8 s | 370 to 430 | `chunk_6_beatdown.jpg` |
| 7 blast and walk | 58.8 to 67.8 s | 435 to 460 | `chunk_7_blast_walk.jpg` |
| 8 lasers and stab | 67.8 to 82.6 s | 465 to 560 | `chunk_8_lasers_stab_part1.jpg`, `chunk_8_lasers_stab_part2.jpg` |

## Known gaps

- **Shot 560 (81.82 s, frame 1962) has no movie frame.** The reference video ends at 81.547 s, so
  `real/560.jpg` is black. The sheet row shows the black cell. Do not trust a comparison for 560 in the movie column.
- The stick figure for 530 and 555 is very small or partly off-frame. That is the render, not a sheet error.

## Times

The middle moment of each shot (`moments.json`). Frame = round(t x 23.976): this is the movie-timeline frame,
not the index inside a reference file (see "Reference video" above). The Studio scrub uses the same frame number.

| Shot | t (s) | Frame | Chunk | real | python_line | roblox |
|---|---|---|---|---|---|---|
| 010 | 0.42 | 10 | 1 | `real/010.jpg` | `python_line/010.jpg` | `roblox/010.jpg` |
| 020 | 1.54 | 37 | 1 | `real/020.jpg` | `python_line/020.jpg` | `roblox/020.jpg` |
| 030 | 2.44 | 59 | 1 | `real/030.jpg` | `python_line/030.jpg` | `roblox/030.jpg` |
| 040 | 3.21 | 77 | 1 | `real/040.jpg` | `python_line/040.jpg` | `roblox/040.jpg` |
| 050 | 4.84 | 116 | 1 | `real/050.jpg` | `python_line/050.jpg` | `roblox/050.jpg` |
| 060 | 6.87 | 165 | 1 | `real/060.jpg` | `python_line/060.jpg` | `roblox/060.jpg` |
| 070 | 8.52 | 204 | 1 | `real/070.jpg` | `python_line/070.jpg` | `roblox/070.jpg` |
| 080 | 9.81 | 235 | 1 | `real/080.jpg` | `python_line/080.jpg` | `roblox/080.jpg` |
| 090 | 13.14 | 315 | 1 | `real/090.jpg` | `python_line/090.jpg` | `roblox/090.jpg` |
| 100 | 16.98 | 407 | 1 | `real/100.jpg` | `python_line/100.jpg` | `roblox/100.jpg` |
| 110 | 18.71 | 449 | 2 | `real/110.jpg` | `python_line/110.jpg` | `roblox/110.jpg` |
| 115 | 19.96 | 479 | 2 | `real/115.jpg` | `python_line/115.jpg` | `roblox/115.jpg` |
| 120 | 21.03 | 504 | 2 | `real/120.jpg` | `python_line/120.jpg` | `roblox/120.jpg` |
| 130 | 22.99 | 551 | 2 | `real/130.jpg` | `python_line/130.jpg` | `roblox/130.jpg` |
| 140 | 25.01 | 600 | 2 | `real/140.jpg` | `python_line/140.jpg` | `roblox/140.jpg` |
| 150 | 26.01 | 624 | 2 | `real/150.jpg` | `python_line/150.jpg` | `roblox/150.jpg` |
| 160 | 26.95 | 646 | 2 | `real/160.jpg` | `python_line/160.jpg` | `roblox/160.jpg` |
| 170 | 27.68 | 664 | 2 | `real/170.jpg` | `python_line/170.jpg` | `roblox/170.jpg` |
| 180 | 28.31 | 679 | 2 | `real/180.jpg` | `python_line/180.jpg` | `roblox/180.jpg` |
| 185 | 29.02 | 696 | 2 | `real/185.jpg` | `python_line/185.jpg` | `roblox/185.jpg` |
| 190 | 29.95 | 718 | 3 | `real/190.jpg` | `python_line/190.jpg` | `roblox/190.jpg` |
| 200 | 30.81 | 739 | 3 | `real/200.jpg` | `python_line/200.jpg` | `roblox/200.jpg` |
| 210 | 31.35 | 752 | 3 | `real/210.jpg` | `python_line/210.jpg` | `roblox/210.jpg` |
| 213 | 31.75 | 761 | 3 | `real/213.jpg` | `python_line/213.jpg` | `roblox/213.jpg` |
| 216 | 32.37 | 776 | 3 | `real/216.jpg` | `python_line/216.jpg` | `roblox/216.jpg` |
| 220 | 34.04 | 816 | 3 | `real/220.jpg` | `python_line/220.jpg` | `roblox/220.jpg` |
| 230 | 35.56 | 853 | 3 | `real/230.jpg` | `python_line/230.jpg` | `roblox/230.jpg` |
| 240 | 36.61 | 878 | 4 | `real/240.jpg` | `python_line/240.jpg` | `roblox/240.jpg` |
| 250 | 37.61 | 902 | 4 | `real/250.jpg` | `python_line/250.jpg` | `roblox/250.jpg` |
| 255 | 38.21 | 916 | 4 | `real/255.jpg` | `python_line/255.jpg` | `roblox/255.jpg` |
| 260 | 39.15 | 939 | 4 | `real/260.jpg` | `python_line/260.jpg` | `roblox/260.jpg` |
| 262 | 40.42 | 969 | 4 | `real/262.jpg` | `python_line/262.jpg` | `roblox/262.jpg` |
| 265 | 41.45 | 994 | 4 | `real/265.jpg` | `python_line/265.jpg` | `roblox/265.jpg` |
| 270 | 42.07 | 1009 | 4 | `real/270.jpg` | `python_line/270.jpg` | `roblox/270.jpg` |
| 275 | 42.57 | 1021 | 4 | `real/275.jpg` | `python_line/275.jpg` | `roblox/275.jpg` |
| 280 | 43.15 | 1035 | 4 | `real/280.jpg` | `python_line/280.jpg` | `roblox/280.jpg` |
| 290 | 43.80 | 1050 | 4 | `real/290.jpg` | `python_line/290.jpg` | `roblox/290.jpg` |
| 295 | 44.32 | 1063 | 4 | `real/295.jpg` | `python_line/295.jpg` | `roblox/295.jpg` |
| 300 | 44.78 | 1074 | 4 | `real/300.jpg` | `python_line/300.jpg` | `roblox/300.jpg` |
| 310 | 45.28 | 1086 | 4 | `real/310.jpg` | `python_line/310.jpg` | `roblox/310.jpg` |
| 320 | 47.16 | 1131 | 5 | `real/320.jpg` | `python_line/320.jpg` | `roblox/320.jpg` |
| 340 | 49.18 | 1179 | 5 | `real/340.jpg` | `python_line/340.jpg` | `roblox/340.jpg` |
| 350 | 50.93 | 1221 | 5 | `real/350.jpg` | `python_line/350.jpg` | `roblox/350.jpg` |
| 360 | 52.52 | 1259 | 5 | `real/360.jpg` | `python_line/360.jpg` | `roblox/360.jpg` |
| 370 | 52.91 | 1269 | 6 | `real/370.jpg` | `python_line/370.jpg` | `roblox/370.jpg` |
| 375 | 53.54 | 1284 | 6 | `real/375.jpg` | `python_line/375.jpg` | `roblox/375.jpg` |
| 380 | 54.35 | 1303 | 6 | `real/380.jpg` | `python_line/380.jpg` | `roblox/380.jpg` |
| 390 | 54.92 | 1317 | 6 | `real/390.jpg` | `python_line/390.jpg` | `roblox/390.jpg` |
| 395 | 55.33 | 1327 | 6 | `real/395.jpg` | `python_line/395.jpg` | `roblox/395.jpg` |
| 400 | 55.83 | 1339 | 6 | `real/400.jpg` | `python_line/400.jpg` | `roblox/400.jpg` |
| 405 | 56.38 | 1352 | 6 | `real/405.jpg` | `python_line/405.jpg` | `roblox/405.jpg` |
| 410 | 57.17 | 1371 | 6 | `real/410.jpg` | `python_line/410.jpg` | `roblox/410.jpg` |
| 415 | 57.92 | 1389 | 6 | `real/415.jpg` | `python_line/415.jpg` | `roblox/415.jpg` |
| 420 | 58.44 | 1401 | 6 | `real/420.jpg` | `python_line/420.jpg` | `roblox/420.jpg` |
| 425 | 59.07 | 1416 | 6 | `real/425.jpg` | `python_line/425.jpg` | `roblox/425.jpg` |
| 430 | 59.84 | 1435 | 6 | `real/430.jpg` | `python_line/430.jpg` | `roblox/430.jpg` |
| 435 | 61.28 | 1469 | 7 | `real/435.jpg` | `python_line/435.jpg` | `roblox/435.jpg` |
| 440 | 62.82 | 1506 | 7 | `real/440.jpg` | `python_line/440.jpg` | `roblox/440.jpg` |
| 445 | 64.07 | 1536 | 7 | `real/445.jpg` | `python_line/445.jpg` | `roblox/445.jpg` |
| 450 | 65.14 | 1562 | 7 | `real/450.jpg` | `python_line/450.jpg` | `roblox/450.jpg` |
| 455 | 65.95 | 1581 | 7 | `real/455.jpg` | `python_line/455.jpg` | `roblox/455.jpg` |
| 460 | 67.07 | 1608 | 7 | `real/460.jpg` | `python_line/460.jpg` | `roblox/460.jpg` |
| 465 | 68.16 | 1634 | 8 | `real/465.jpg` | `python_line/465.jpg` | `roblox/465.jpg` |
| 470 | 69.53 | 1667 | 8 | `real/470.jpg` | `python_line/470.jpg` | `roblox/470.jpg` |
| 475 | 71.10 | 1705 | 8 | `real/475.jpg` | `python_line/475.jpg` | `roblox/475.jpg` |
| 480 | 72.27 | 1733 | 8 | `real/480.jpg` | `python_line/480.jpg` | `roblox/480.jpg` |
| 485 | 73.14 | 1754 | 8 | `real/485.jpg` | `python_line/485.jpg` | `roblox/485.jpg` |
| 490 | 73.89 | 1772 | 8 | `real/490.jpg` | `python_line/490.jpg` | `roblox/490.jpg` |
| 505 | 74.69 | 1791 | 8 | `real/505.jpg` | `python_line/505.jpg` | `roblox/505.jpg` |
| 520 | 75.48 | 1810 | 8 | `real/520.jpg` | `python_line/520.jpg` | `roblox/520.jpg` |
| 525 | 76.23 | 1828 | 8 | `real/525.jpg` | `python_line/525.jpg` | `roblox/525.jpg` |
| 530 | 76.96 | 1845 | 8 | `real/530.jpg` | `python_line/530.jpg` | `roblox/530.jpg` |
| 535 | 77.71 | 1863 | 8 | `real/535.jpg` | `python_line/535.jpg` | `roblox/535.jpg` |
| 540 | 78.61 | 1885 | 8 | `real/540.jpg` | `python_line/540.jpg` | `roblox/540.jpg` |
| 545 | 79.54 | 1907 | 8 | `real/545.jpg` | `python_line/545.jpg` | `roblox/545.jpg` |
| 550 | 80.21 | 1923 | 8 | `real/550.jpg` | `python_line/550.jpg` | `roblox/550.jpg` |
| 555 | 80.80 | 1937 | 8 | `real/555.jpg` | `python_line/555.jpg` | `roblox/555.jpg` |
| 560 | 81.82 | 1962 | 8 | `real/560.jpg` | `python_line/560.jpg` | `roblox/560.jpg` |

## Old files

- `chunk_1_standoff_dialogue.jpg` ... `chunk_8_lasers_stab.jpg` (directly in this folder) are the earlier sheets, built
  from captures taken at slightly different times for shots 120, 545, 550, 555 and 560. They are superseded by
  `chunk_sheets/`. They are kept until you say to remove them.
- `analysis/threeway_all/studio/` holds the earlier Studio copies (`captures.txt` lists them). `roblox/` replaces them.
- `analysis/threeway_all/wire/` holds the older 4-row wireframe sheets. `python_line/` replaces them: one render per shot, at the exact moment.
