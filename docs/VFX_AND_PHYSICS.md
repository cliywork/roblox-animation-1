# VFX and physics — the quality bar and the tools

## The owner's quality bar (TOP PRIORITY, applies to every shot)

> "High quality output… it may be Roblox but we add realism to Roblox since this is video output
> only… every smoke, sand or dust… when a thing comes fast and hits Thanos' hand, the moment it hits
> I need that physics: after hitting his hand his body has to react to that speed… and blasts
> realism, VFX."

In practice:
- **Smoke, dust, sand, blasts look real**: textured flipbook particles in layers (fireball +
  rolling smoke + ground dust wave + sparks + rock chunks + shockwave + light flash + camera shake),
  never plain neon balls on their own.
- **Every impact has a body reaction** that matches its speed and direction (see Physics below).
  A hit with no reaction is a bug.
- **Contacts touch.** A punch, grab, pin or stab must land on the other body (IK, measured).
- **Nothing floats or sinks.** Feet, knees, bodies lying down sit on the ground (y = 1.95).
- **Small human details**: settling, weight shifts, a head that lags the body, held poses that breathe.
- Best available assets. Sources so far: the Roblox Creator Store and Roblox's AI mesh generator,
  inserted inside Studio. Anything downloaded from outside Roblox needs the owner's OK per file
  (say the file, source and size).

## Particle assets (`roblox_pipeline/VFXAssets.lua`)

| Key | Image id | Use | Blend |
|---|---|---|---|
| `smokeSoft` | rbxassetid://13026594575 (8×8 loop) | all smoke, dust, exhaust, energy haze (tint it) | normal; additive + tinted for glowing energy |
| `fireball` | rbxassetid://15855570024 (8×8 one-shot) | explosion fireballs, thruster flame | **additive** (black background) |
| `fireballAlt` | rbxassetid://13651663811 (8×8 one-shot) | short energy/impact bursts | **additive** |

- **Rejected:** Creator Store 79643461976843 "Smoke Flipbook" (opaque background → hard squares).
- Store **decal ids are not image ids**: resolve with `InsertService:LoadAsset(id)` and read the
  Decal's `Texture`. Vet a new texture in a lab (live emitter against the Titan lighting) before use.
- The fire sheets are **baked orange**. For coloured energy (purple beam splash, blue) use
  `smokeSoft` with `LightEmission = 1` and a tint.
- Source decals for the lab: `ServerStorage.VFXLab`.

## Director particle toolkit (`Director.client.lua`)

Reusable building blocks; call them from an FX kind's update:
- `emitter(parent, assetKey, props)`: ParticleEmitter preset from VFXAssets.
- `explosion(pos, s)`: a ground blast: fireball, rolling smoke, dust wave, sparks, light, shockwave, chunks.
- `energyHit(pos, s, color, sparksOnly)`: hit on a body: hot burst + sparks + smoke puff + light.
  `sparksOnly` for torn metal (no fireball).
- `dustHit(pos, s)`: feet/body hitting the ground: low dust burst + ring + small chunks.
- `chunks(pos, n, s, up)`: physics rock chunks (real parts that fly, tumble, bounce).
- `shockwave(pos, radius, color, dur)`, `flashLight(att, color, brightness, range, dur)`.
- `addShake(t, amp, decay)`: camera shake, deterministic in movie time (scrub = playback).
- `crossed(state, key, t, tau)`: fire a one-shot burst when the timeline crosses t (also when a
  scrub lands just after t, so you can screenshot it).
- Trails, emitters and physics chunks only run in **live** playback (`fxLive`); a frozen scrub
  shows the parts but not trails. Final look = live playback (what the owner records).

## FX kinds (`FX` list in scene.py → `FX_KINDS` in the Director)

All times are movie seconds. `"Rig.Part"` strings target the BasePart child of that rig.

| kind | example fields | what it draws |
|---|---|---|
| `nanoshot` | t, dur, target, frm, local, pull, hand, fling | the nanotech piece flying into Thanos' palm (010), stuck there, pulled out and flung (220) |
| `pods` | t, grow, t1, target | launcher pods growing on Iron Man's back (110) |
| `missiles` | target, at, n, seed, launch0/1, hit0/1 | missile barrage with smoke trails, each ending in `explosion()` (115–130) |
| `flare` | t, dur | screen-space lens streak |
| `dust` | t, t1, at | lingering barrage dust + haze (130) |
| `thruster` | part, dir, t, t1, size | boot/palm flame + exhaust particles |
| `kickdisc` | rig, t, t1 | blue device under the boots for the kick (140–150) |
| `impact` | t, at, offset, size, color, dur, light | `light>0` → energyHit (body hit); `light=0` → dustHit (ground). Adds shake |
| `anchors` | rig, t, t1 | ground claws from the boots (160, 290) |
| `cannons` | rig, t, grow, t1, jet0, jet1 | arm cannons forming + blue jets (170–185) |
| `helmet` | rig, t0, t, t1, grow, fling | helmet crushed (t0), torn off as physics plates (t), nanotech rebuild (t1..t1+grow) |
| `skid` | part, t, t1 | dust + grit along the ground under a sliding body |
| `shake` | t, amp [, t1, every, each] | camera jolt, or a sustained rumble |
| `tint` | t, t1, color, alpha | colour wash over the frame (energy light in close shots) |
| `beam` | src, dst, t0, t, hit, t1 | Power Stone beam: charge, bolt + glow + crackling arcs + lights, splash at the shield |
| `shield` | rig, face, t, grow, t1, fling | nanotech kite shield on the left forearm; flung away as plates |
| `fistgun` | part, t, grow, glow, hit, t1, at | nanotech weapon piling onto the fist, blue glow, blast at the hit |
| `mark` | part, offset, size, t, grow, color | a wet mark stuck to a part (blood on brow / fingertip); fractions of part size |

To add a new kind: write `buildX(fx)` / `updateX(state, tau)` in the Director, register it in
`FX_KINDS`, add entries to `FX` in scene.py. Keep it deterministic in `tau` so scrubbing works.

Still to build for upcoming beats: purple beam **throw** (01:00.3), Iron Man's **hand repulsor**
beam and Thanos blocking it with his palm while walking, **armour regrowth**, **twin yellow
"fire laser" beams** (01:07.8, see the reference), the **nanotech sword** growing from the armour
(01:17.9, owner explicitly asked the agent to model it), the sword **breaking** (01:20.5) and the
**stab** (01:21).

## Helmet HUD (inside-the-mask shots)

`hud="mask"` on a shot: near-black vignette, cyan holographic glow, glass streaks, readouts, cool
grade, a face light, the helmet pieces hidden. `hud="lock"` adds the blue→orange target cluster
(shot 100). The HUD camera must sit **in front of Tony's face** (head-relative offset along the
direction his face points). When he is lying on his back, his face points **up**: the camera goes
above his face looking down, not at +Z.

## Physics: hit reactions (`react()` in scene.py)

Every impact gets a damped-spring reaction added on top of the animation:
`FIGHT_HITS += [(t_hit, "ironman"|"thanos", part, push_direction_rig_space, degrees)]`.
- The struck part is kicked along the push direction; each joint further up the chain (hand → arm
  → shoulder → chest, foot → leg → hips) reacts later, smaller and slower; the head lags the chest
  with a small opposite nod. Peaks are in degrees at the struck joint.
- Scale: glancing 8–12°, solid punch 14–20°, a hit to the head 30–40°, the final blow 38°.
- Hit both sides: the struck body **and** the striker's fist/foot (recoil, ~12–16°).
- `react` is applied to every shot slice that contains the hit (or started up to 0.8 s after it),
  so reactions carry across cuts.

## Physics: contacts (`reach()` two-bone IK)

- Solve every touch onto the target part at that exact movie time:
  `reach(pose, rig, side, target_world, pole, palm)` → `(pose, shortfall_studs)`.
- The print-out after `python scene.py` lists shortfalls. Above **~0.5 studs** it reads as a miss
  on screen: move the body closer (channels), lean the torso, or lower the body (TH_DROP); don't
  just accept it.
- Targets: aim at the part surface (offset ~0.2–0.4 studs above the part centre for the owner's
  taller Iron Man). For self-contact (Thanos touching his own brow) target his own head.
- After moving a body, re-check both the contact **and** the ground (y = 1.95).

## Ground and bodies

- Ground y = 1.95. Part **centres** (scene.CENTER, via world_point) should sit ≥ ~0.2 above it for
  feet, ~0.4–0.5 for a body lying down; nothing below 1.95.
- `kneel()`: front thigh near level, front shin angled forward, back knee on the ground. With
  Thanos at TH_DROP −0.8 his front foot is at ~2.17 and back knee at ~2.43 (correct).
- Lying face up = pitch 90 (+360k); face down = 270. Use IM_H to lift the body so it rests on the ground.
