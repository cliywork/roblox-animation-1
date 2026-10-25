import json
import os

with open('scratch_all_79_cuts_mapped.json') as f:
    cuts = json.load(f)

# Detail descriptions for all 79 cuts
# Let's define the comprehensive matter for each cut
cut_details = [
    # Cut 1
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Medium-Wide Shot (Low-Angle Frontal)",
        "camera_movement": "Static with subtle upward gaze",
        "characters": "Thanos",
        "action": "Thanos stands tall on the dusty red terrain of Titan with the ruined sky behind him. He raises his left arm displaying the golden Infinity Gauntlet (holding the Power, Space, Reality, and Soul stones). The gauntlet is raised toward chest/head level as he prepares for conflict."
    },
    # Cut 2
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Extreme Close-Up (ECU)",
        "camera_movement": "Smooth lateral pan tracking right along extending arm",
        "characters": "Thanos (Left Arm & Gauntlet)",
        "action": "Extreme close-up framing Thanos' broad left shoulder on screen-left edge as his arm extends forward toward screen-center. His massive golden gauntlet opens its palm wide toward the sky, catching a blinding sunlight glint / sunburst flare off the golden knuckles and embedded Infinity Stones."
    },
    # Cut 3
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Medium Close-Up (MCU, Low-Angle)",
        "camera_movement": "Static with quick upward head tilt follow",
        "characters": "Thanos",
        "action": "Thanos is positioned on the left third of the frame, his left gauntleted hand raised in the lower-right foreground. He suddenly cocks his head and shifts his gaze upward toward the sky as an approaching sonic roar announces Iron Man's arrival."
    },
    # Cut 4
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Extreme Wide Aerial Shot (Looking Up)",
        "camera_movement": "Upward sky tilt tracking high-speed transit",
        "characters": "Iron Man (Mark 50) & Titan Sky",
        "action": "The desolate crimson-orange sky of Titan stretches across the frame with derelict alien structures looming in silhouette. Iron Man streaks across the upper atmosphere horizontally from screen-left to screen-right at supersonic speed, trailing dual bright cyan-blue thruster plumes before banking sharply downward toward the battlefield."
    },
    # Cut 5
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Wide Battlefield Shot (Low Angle)",
        "camera_movement": "Smooth forward dolly push-in (~28 studs to cowboy stance)",
        "characters": "Iron Man (Thanos in distant background)",
        "action": "Iron Man drops out of the sky like a comet, slamming boots-first into the dusty soil with a heavy plume of orange dust and shockwave smoke. He absorbs the impact with bent knees, rises smoothly into a defensive cowboy thigh-up stance, and stares down Thanos across the battlefield."
    },
    # Cut 6
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Inside-the-Mask HUD Close-Up (Square-On Frontal)",
        "camera_movement": "Subtle floating handheld micro-creep",
        "characters": "Tony Stark (Inside HUD)",
        "action": "Frontal close-up inside the Mark 50 helmet. Tony's determined, intense eyes fill 65% of the frame surrounded by glowing blue holographic HUD displays, targeting brackets, and suit diagnostics. He glares straight ahead through the visor at Thanos without blinking."
    },
    # Cut 7
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Close-Up (CU)",
        "camera_movement": "Static",
        "characters": "Thanos",
        "action": "Thanos looks across the rubble at Iron Man with heavy, calm recognition. His armored collar and massive jaw are framed slightly left of center as his lips part to speak his single-word acknowledgment: 'Stark.'"
    },
    # Cut 8
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Inside-the-Mask HUD Close-Up",
        "camera_movement": "Static micro-creep",
        "characters": "Tony Stark (Inside HUD)",
        "action": "Tony Stark's face illuminated by amber and blue HUD readouts. His brow furrows in surprise and tension as he responds to Thanos: 'You know me?'"
    },
    # Cut 9
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Close-Up (CU)",
        "camera_movement": "Slow, deliberate dolly push-in (~0.8 studs closer)",
        "characters": "Thanos",
        "action": "Thanos maintains intense eye contact, his expression somber and reflective rather than mocking. He answers with gravitas: 'I do. You're not the only one cursed with knowledge.' The slow creep of the camera emphasizes his tragic, philosophical conviction."
    },
    # Cut 10
    {
        "chunk": "Chunk 1: Standoff and Dialogue",
        "shot_type": "Inside-the-Mask HUD Close-Up",
        "camera_movement": "Slow creep-in, followed by target-lock cluster snapping",
        "characters": "Tony Stark (Inside HUD)",
        "action": "Tony's jaw sets with icy anger as he delivers his resolute retort: 'My only curse is you.' Simultaneously, holographic red/blue target-locking reticles lock onto Thanos' coordinates, signaling the immediate escalation into battle."
    },
    # Cut 11
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Medium Close-Up (MCU, Low-Angle Tilted Up)",
        "camera_movement": "Static with slight upward follow",
        "characters": "Iron Man",
        "action": "Iron Man's nanotech suit instantly morphs: multiple cluster missile pods sprout from his collar and shoulders, angling skyward. A barrage of micro-missiles ignites simultaneously, ejecting white smoke trails and blazing orange exhaust fire directly into the air."
    },
    # Cut 12
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Extreme Wide Shot (Low Angle)",
        "camera_movement": "Low static angle gazing upward at the missile trajectory",
        "characters": "Iron Man (distant center) & Missiles",
        "action": "Iron Man appears small on the distant rubble as scores of launched micro-missiles curl upward into the high atmosphere in graceful white smoke arcs before arcing downward toward Thanos."
    },
    # Cut 13
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Medium Cowboy Shot",
        "camera_movement": "Static with slight low push",
        "characters": "Thanos",
        "action": "Thanos stands defiantly with his right arm tucked back near his hip and his golden gauntlet held in the lower-right foreground. Looking up at the incoming missile barrage descending from the upper sky, he smirks and taunts: 'Come on!'"
    },
    # Cut 14
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "High-Angle Aerial Three-Quarter Shot",
        "camera_movement": "Fast dive tracking push-in following the rockets",
        "characters": "Incoming Missiles & Thanos",
        "action": "The camera trails directly behind the swarm of missiles as they converge on Thanos at high speed. In the center of the frame, Thanos raises both massive arms in a protective cross-guard to shield his face just as the first rockets strike."
    },
    # Cut 15
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Wide Ground-Level 35-Degree Profile Shot",
        "camera_movement": "Static wide with camera vibration / explosion shockwaves",
        "characters": "Thanos engulfed in Detonations & Smoke",
        "action": "Consecutive high-explosive missile impacts detonate across Thanos' defensive guard, generating a violent succession of fireballs, shockwave dust rings, and a towering black-and-grey smoke cloud completely engulfing Thanos."
    },
    # Cut 16
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Low Ground-Level Wide Frontal Tracking Shot",
        "camera_movement": "Fast backward dolly tracking Iron Man charging forward",
        "characters": "Iron Man",
        "action": "Blasting directly through the lingering smoke cloud, Iron Man skims inches above the Titan soil pitched forward at 50 degrees. Cyan repulsor thrusters on his boots and hands blaze fiercely, with a heavy blue nanotech foot-anchor clamp deployed beneath his feet ready for impact."
    },
    # Cut 17
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Low-Angle Side-Profile Tracking Shot (+25 deg Tilt)",
        "camera_movement": "High-speed lateral tracking following the bounce",
        "characters": "Iron Man & Thanos",
        "action": "Iron Man delivers a brutal two-footed dropkick directly into Thanos' chest/guard. The kinetic recoil launches Iron Man backward in an acrobatic reverse somersault flip through the air, his back thrusters stabilizing his flight path."
    },
    # Cut 18
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Ground-Level Static Macro Shot",
        "camera_movement": "Static with ground impact jolt",
        "characters": "Iron Man's Boots & Dirt Surface (Thanos foot left)",
        "action": "Iron Man's armored boots drop straight into the frame, slamming into the loose Titan gravel and kicking up a violent dust wave. Mechanical nanotech anchor blades instantly shoot out from the soles and clamp deep into the ground, locking his stance rigid for the follow-up attack. Thanos' planted foot is visible in the background left."
    },
    # Cut 19
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Telephoto Medium Shot Past Thanos' Arm",
        "camera_movement": "Static telephoto compression",
        "characters": "Iron Man (Thanos in foreground silhouette)",
        "action": "Framed past Thanos' massive reaching arm, Iron Man coils in a 3/4 athletic combat stance. Red-and-gold nanotech streams rapidly pool onto both forearms, materializing into heavy silver battering-ram cannons primed to strike."
    },
    # Cut 20
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Side-Rear Tracking Close-Up",
        "camera_movement": "High-speed forward-left tracking rush",
        "characters": "Iron Man & Thanos",
        "action": "Iron Man ignites massive horizontal blue thruster exhausts behind his back and cannons, rocketing forward screen-left. He drives both battering rams with overwhelming force directly into Thanos' chest at 28.15s, triggering a brilliant radial kinetic flash and sparks."
    },
    # Cut 21
    {
        "chunk": "Chunk 2: Missiles, Kick, and Charge",
        "shot_type": "Wide Battlefield Shot from Behind Iron Man",
        "camera_movement": "Tracking dolly pushing forward with the rush",
        "characters": "Iron Man driving Thanos back",
        "action": "Twin blue cannon exhausts point toward the camera as Iron Man's sustained rocket boost forces the massive Titan backward several yards across the rocky plateau, carving deep trenches into the earth."
    },
    # Cut 22
    {
        "chunk": "Chunk 3: Helmet Tear and Skidding",
        "shot_type": "Over-the-Shoulder (OTS) Medium Close-Up",
        "camera_movement": "Fast dynamic tilt-up following Thanos' arm movement",
        "characters": "Iron Man & Thanos",
        "action": "Iron Man lands a short left hook into Thanos' ribcage at 29.95s, but Thanos shrugs off the blow. Thanos' massive bare right hand reaches up, clamps over Iron Man's helmet, and with tremendous crushing strength rips the helmet straight off Tony's head."
    },
    # Cut 23
    {
        "chunk": "Chunk 3: Helmet Tear and Skidding",
        "shot_type": "Tight Frontal Close-Up",
        "camera_movement": "Slight upward tilt looking up into Tony's eyes",
        "characters": "Tony Stark (Unmasked)",
        "action": "Tony Stark's exposed face is revealed, hair disheveled. He looks upward with shock and disbelief as torn fragments of his gold-and-red helmet fly past the camera."
    },
    # Cut 24
    {
        "chunk": "Chunk 3: Helmet Tear and Skidding",
        "shot_type": "Over-the-Shoulder Medium Shot",
        "camera_movement": "Violent jerk / shake on hit impact",
        "characters": "Thanos & Tony Stark",
        "action": "Thanos grips Tony's armored shoulder with his left gauntlet to hold him in place, draws back his right fist, and delivers a brutal punch / headbutt directly into Tony's jaw, sending sparks flying."
    },
    # Cut 25
    {
        "chunk": "Chunk 3: Helmet Tear and Skidding",
        "shot_type": "Low-Angle Frontal Close-Up",
        "camera_movement": "Rapid tilt following Tony's head recoil",
        "characters": "Tony Stark (Helmet Reforming)",
        "action": "Reeling backward from the impact, Tony's suit instantly responds: liquid nanotech flows rapidly from his neck armor upward over his chin, nose, and eyes, fully reconstructing the helmet in a fraction of a second."
    },
    # Cut 26
    {
        "chunk": "Chunk 3: Helmet Tear and Skidding",
        "shot_type": "Ground-Level Tracking Shot",
        "camera_movement": "Fast lateral tracking following Iron Man skidding",
        "characters": "Iron Man (skidding in dust)",
        "action": "Thanos delivers a follow-through hammer blow that flings Iron Man violently screen-right. Iron Man crashes face-down into the red dirt, sliding and carving a long trail through the gravel and dust before skidding to a halt."
    },
    # Cut 27
    {
        "chunk": "Chunk 3: Helmet Tear and Skidding",
        "shot_type": "Wide Static Medium Shot",
        "camera_movement": "Static framing Thanos occupying 70% frame height",
        "characters": "Thanos (alone on rubble)",
        "action": "Thanos stands victorious on the plateau. He looks down at his Infinity Gauntlet, notices a small piece of nanotech debris wedged between the knuckle plates, calmly plucks it out with his fingertips, flicks it away, and lets out a low, mocking chuckle."
    },
    # Cut 28
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Low-Angle Tight Close-Up",
        "camera_movement": "Subtle slow push-in",
        "characters": "Iron Man (kneeling)",
        "action": "Iron Man pushes up from one knee, his newly-reformed helmet angled upward. Through the visor slits, his gaze is defiant and focused as nanotech finishes sealing the armor over his chest."
    },
    # Cut 29
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Wide Battlefield Shot",
        "camera_movement": "Static wide perspective capturing the full arena",
        "characters": "Thanos & Iron Man",
        "action": "Thanos raises the Infinity Gauntlet. The purple Power Stone blazes with blinding violet light. At 37.0s, Thanos unleashes a massive, continuous torrent of purple plasma energy directly toward Iron Man."
    },
    # Cut 30
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Side Profile Medium Shot",
        "camera_movement": "Static",
        "characters": "Iron Man deploying Shield",
        "action": "In a deep braced athletic stance, Iron Man thrusts his left arm forward. Nanotech armor flows outward, instantly materializing a broad, curved nanotech tower shield to intercept the incoming blast."
    },
    # Cut 31
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Low Ground-Level Wide Angle",
        "camera_movement": "Static with intense screen-shake",
        "characters": "Purple Beam impacting Shield",
        "action": "The searing purple energy beam slams violently into the face of Iron Man's shield, detonating a massive radial blast of violet plasma and showering the surrounding ground in purple sparks."
    },
    # Cut 32
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Side-View Tracking Shot",
        "camera_movement": "Smooth backward tracking keeping Iron Man centered",
        "characters": "Iron Man bracing against Beam",
        "action": "The continuous purple torrent pushes relentlessly against the shield. Iron Man digs his boots into the rock, carving deep burning furrows as he is shoved backward by the tremendous kinetic force of the Power Stone."
    },
    # Cut 33
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Tight Over-the-Shoulder Close-Up",
        "camera_movement": "Static high-tension frame",
        "characters": "Iron Man & Shield interior",
        "action": "Violet energy waves flood violently around both sides of the shield, illuminating Tony's helmet in blinding magenta and purple light as he strains every servo to hold the shield steady."
    },
    # Cut 34
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Side Wide Shot",
        "camera_movement": "Fast pan-tilt following Iron Man's breakout",
        "characters": "Iron Man breaking out of Beam",
        "action": "Realizing the shield cannot hold indefinitely, Iron Man flings the shield away, ducks under the beam trajectory, and ignites his boot and back thrusters to launch into a low, high-speed forward sprint toward Thanos."
    },
    # Cut 35
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Dynamic Medium Tracking Shot",
        "camera_movement": "Fast lateral tracking following barrel roll",
        "characters": "Iron Man boosting forward",
        "action": "Iron Man executes an airborne diagonal barrel roll (~35 degrees) skimming feet above the ground, focused cyan thruster jets propelling him rapidly closing the distance to Thanos."
    },
    # Cut 36
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Extreme Close-Up Ground Insert Angle",
        "camera_movement": "High-speed ground tracking",
        "characters": "Iron Man's boot skimming ground",
        "action": "Extreme close-up of Iron Man's lower leg and repulsor boot skimming millimeters above the dirt surface at full boost, kicking up dust plumes."
    },
    # Cut 37
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Medium Two-Shot Past Thanos",
        "camera_movement": "Quick tracking tilt following Iron Man's dive",
        "characters": "Thanos grabbing at Iron Man",
        "action": "Thanos sweeps his left arm to swat the incoming avenger out of the air. Iron Man ducks under Thanos' reach, diving boots-first straight onto the outstretched Infinity Gauntlet."
    },
    # Cut 38
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Ground-Level Close-Up",
        "camera_movement": "Static with ground impact thud",
        "characters": "Iron Man pinning Gauntlet",
        "action": "Iron Man's heavy armored boots slam directly onto the back of the Infinity Gauntlet, driving Thanos' left hand flat against the rock. Nanotech ground clamps instantly deploy, pinning the gauntlet immovably to the earth."
    },
    # Cut 39
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Wide Dynamic Shot",
        "camera_movement": "Quick dynamic pan/tilt tracking body rotation",
        "characters": "Thanos pinned / Iron Man winding up",
        "action": "With Thanos pinned down on one knee and unable to use the gauntlet, Iron Man leverages his position and whips his entire torso around into a rapid 360-degree rotational spin to build maximum momentum."
    },
    # Cut 40
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Tight Close-Up Tracking Right Arm",
        "camera_movement": "Rotational whip pan matching the arm swing",
        "characters": "Right Fist weapon morphing",
        "action": "As Tony's right arm swings through the arc, liquid nanotech surges from his chest and shoulder down his arm, morphing his fist into a gigantic, dense, blue-energized battering ram mallet."
    },
    # Cut 41
    {
        "chunk": "Chunk 4: Purple Power Stone Beam and Counter-Blow",
        "shot_type": "Frontal Angle / OTS Shot",
        "camera_movement": "Static with massive screen-shake on impact",
        "characters": "The Blow to Thanos' Face",
        "action": "At 45.39s, the blue-glowing battering ram fist completes its swing and smashes squarely into the right side of Thanos' jaw, violently snapping Thanos' head sideways in an explosion of blue sparks and shockwaves."
    },
    # Cut 42
    {
        "chunk": "Chunk 5: Drop of Blood and Face-Off",
        "shot_type": "Low-Angle Close-Up (Front-Left)",
        "camera_movement": "Static with slow subtle push-in",
        "characters": "Thanos (dazed from blow)",
        "action": "The ring of the massive impact still echoes. Thanos sits with head bowed, panting heavily from the force of the strike. Slowly, he raises his right hand up to his left brow to touch where the blow landed."
    },
    # Cut 43
    {
        "chunk": "Chunk 5: Drop of Blood and Face-Off",
        "shot_type": "Extreme Close-Up (ECU Macro)",
        "camera_movement": "Static macro shot",
        "characters": "Thanos' Fingertip with Blood",
        "action": "Macro focus on Thanos' massive purple fingertips. On the tip of his index finger rests a single glistening bead of dark crimson blood—proof that the Mad Titan can bleed."
    },
    # Cut 44
    {
        "chunk": "Chunk 5: Drop of Blood and Face-Off",
        "shot_type": "Close-Up (CU)",
        "camera_movement": "Slow smooth push-in",
        "characters": "Thanos smiling",
        "action": "A thin streak of crimson blood trickles down Thanos' left cheek from a cut on his brow. He slowly looks up from his finger to meet Iron Man's gaze. His expression softens into a dark, amused half-smile: 'All that for a drop of blood.'"
    },
    # Cut 45
    {
        "chunk": "Chunk 5: Drop of Blood and Face-Off",
        "shot_type": "Symmetrical Wide Side-On Two-Shot (YouTube Thumbnail)",
        "camera_movement": "Perfectlyn static wide tableau",
        "characters": "Thanos & Iron Man in Face-Off",
        "action": "A tense, iconic standoff: Thanos rests on one knee on screen-left, and Iron Man stands defiant on screen-right amidst the Titan ruins, staring each other down in a silent split-second pause before violence resumes."
    },
    # Cut 46
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Ground-Level Low Angle",
        "camera_movement": "Static with sudden motion burst",
        "characters": "Thanos sweeping Iron Man's legs",
        "action": "Thanos suddenly lunges forward with explosive speed, sweeping his heavy armored leg across the ground and taking Iron Man's feet out from under him."
    },
    # Cut 47
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Wide Dynamic Angle (Dutch Tilt -22 deg)",
        "camera_movement": "Fast lateral tracking following body in air",
        "characters": "Iron Man hurled flipping through air",
        "action": "Iron Man is violently upended, sent flipping horizontally head-over-heels through the air toward screen-right against the tilted Titan horizon."
    },
    # Cut 48
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Low Ground-Level Angle",
        "camera_movement": "Static with ground impact vibration",
        "characters": "Iron Man slamming into dirt",
        "action": "Iron Man slams brutally onto his back in the rocky soil, skidding face-up through loose dirt and gravel before coming to a stop."
    },
    # Cut 49
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Low-Angle Two-Shot Past Tony's Head",
        "camera_movement": "Upward tracking tilt matching Thanos' stride",
        "characters": "Thanos advancing with cocked fist",
        "action": "Tony's helmeted head lies vulnerable in the lower foreground as Thanos strides menacingly over him, towering against the sky with his bare right fist cocked back."
    },
    # Cut 50
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Inside-the-Mask HUD Close-Up",
        "camera_movement": "Handheld micro-shake",
        "characters": "Tony Stark (Inside HUD)",
        "action": "Tony looks up in terror through the HUD as Thanos' shadow looms completely over him; warning alarms flash red across his vision."
    },
    # Cut 51
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Top-Down High Angle",
        "camera_movement": "Static overhead gaze",
        "characters": "Tony scrambling to block",
        "action": "Flat on his back, Tony scrambles desperately to cross both armored forearms over his face in a frantic defensive cross-guard."
    },
    # Cut 52
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Inside-the-Mask HUD Close-Up",
        "camera_movement": "Violent sideways camera jerk / glitch effect",
        "characters": "Tony Stark (Inside HUD, Punch 1 lands)",
        "action": "Thanos' first massive punch hammers into Tony's guard, shattering suit diagnostics and violently snapping Tony's head sideways under a flashing holographic HUD."
    },
    # Cut 53
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Low Ground Profile View",
        "camera_movement": "Static with slight push",
        "characters": "Iron Man propped on back",
        "action": "Iron Man lies propped on his back and side against the dusty ground, dazed and struggling to push himself upright against the burning golden horizon."
    },
    # Cut 54
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Inside-the-Mask HUD Close-Up",
        "camera_movement": "Static tight framing",
        "characters": "Tony Stark grimacing with blood",
        "action": "Tony grimaces in intense agony with eyes clenched shut as fresh blood trickles down his brow inside the damaged helmet."
    },
    # Cut 55
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Extreme Close-Up Ground View",
        "camera_movement": "Static tight insert",
        "characters": "Iron Man helmet pinned in dirt",
        "action": "Tony's red-and-gold helmet lies pinned flat sideways against the rough gravel, unable to evade Thanos' descending fist."
    },
    # Cut 56
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Overhead High-Angle Down Purple Arm",
        "camera_movement": "High-speed downward plunge tracking fist",
        "characters": "Overhead Punch 2 descending",
        "action": "Thanos drives his massive purple right fist straight down from top-left, accelerating directly into the center of Iron Man's pinned helmet with crushing velocity."
    },
    # Cut 57
    {
        "chunk": "Chunk 6: Beatdown and Broken Helmet",
        "shot_type": "Extreme Close-Up on Shattered Helmet",
        "camera_movement": "Static with dust and particle drift",
        "characters": "Shattered Faceplate & Exposed Bruised Face",
        "action": "Punch 2 smashes through the helmet, tearing away the gold faceplate completely to expose Tony Stark's bruised, bleeding forehead, swollen eye, and battered face."
    },
    # Cut 58
    {
        "chunk": "Chunk 7: Point-Blank Blast, Recovery, and March",
        "shot_type": "Wide Static Low-Angle Shot",
        "camera_movement": "Static with massive screen-shake on blast detonation",
        "characters": "Thanos lifting and blasting Iron Man",
        "action": "Thanos seizes Tony by the chest collar, lifts his battered body completely off the ground with one arm, raises the Infinity Gauntlet point-blank against Tony's chest, and unleashes a blinding purple Power Stone concussive blast at 61.6s."
    },
    # Cut 59
    {
        "chunk": "Chunk 7: Point-Blank Blast, Recovery, and March",
        "shot_type": "Low Static Shot behind Rubble",
        "camera_movement": "Static framed past rocks",
        "characters": "Iron Man tumbling to a halt",
        "action": "Hurled dozens of yards through the air, Iron Man crashes violently into the rocky terrain, tumbling repeatedly before skidding to a complete halt flat on his back in the center of the frame."
    },
    # Cut 60
    {
        "chunk": "Chunk 7: Point-Blank Blast, Recovery, and March",
        "shot_type": "Wide Tracking Shot",
        "camera_movement": "Smooth forward-right tracking with Thanos' heavy steps",
        "characters": "Thanos marching toward Tony",
        "action": "Thanos lowers his smoking gauntlet and begins a slow, deliberate march across the battlefield toward the fallen Avenger. In the distant background, Tony slowly begins to stir amidst the rubble."
    },
    # Cut 61
    {
        "chunk": "Chunk 7: Point-Blank Blast, Recovery, and March",
        "shot_type": "Low-Angle Shot beside Rubble",
        "camera_movement": "Low Dutch angle (-8 deg) tilted upward",
        "characters": "Iron Man firing arm repulsor",
        "action": "Pushing himself up onto one knee with agonizing effort, Tony raises his right gauntlet and fires a single, high-intensity blue repulsor energy beam straight at Thanos."
    },
    # Cut 62
    {
        "chunk": "Chunk 7: Point-Blank Blast, Recovery, and March",
        "shot_type": "Medium-Wide Tracking Shot",
        "camera_movement": "Backward tracking moving with Thanos' advance",
        "characters": "Thanos deflecting beam with Gauntlet",
        "action": "Without breaking stride, Thanos raises the golden Infinity Gauntlet, effortlessly deflecting the repulsor beam into the sky while walking straight through an arc of bright blue sparks."
    },
    # Cut 63
    {
        "chunk": "Chunk 7: Point-Blank Blast, Recovery, and March",
        "shot_type": "Medium Close-Up on Kneeling Iron Man",
        "camera_movement": "Static with subtle tilt up",
        "characters": "Iron Man's nanotech armor regenerating",
        "action": "Kneeling on one knee, Tony draws on the suit's remaining nanotech reserves. Red and gold armor plating flows across his shattered chest and collar, repairing the breach and reforming over his heart in preparation for a final stand."
    },
    # Cut 64
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Medium-Close Front-Right Three-Quarter Angle",
        "camera_movement": "Static with dynamic energy flare",
        "characters": "Iron Man unleashing Dual Fire-Lasers",
        "action": "Still on one knee, Iron Man thrusts both hands forward toward screen-left and unleashes twin searing, high-temperature yellow fire-lasers from palm emitters, flooding the frame with blinding golden-orange light."
    },
    # Cut 65
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Over-the-Shoulder Wide Shot behind Tony",
        "camera_movement": "Forward dolly tracking Thanos through flames",
        "characters": "Twin Fire-Lasers converging on Thanos",
        "action": "Dual streams of blazing fire converge directly upon Thanos' chest. Thanos continues his inexorable forward march directly through the torrent of flames, shielding his face with his gauntlet."
    },
    # Cut 66
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Medium Close-Up Profile",
        "camera_movement": "Static tight framing",
        "characters": "Iron Man straining at maximum output",
        "action": "Profile of Tony Stark gritting his teeth in pure physical and mental strain, channeling 100% of the suit's remaining energy into the burning dual lasers."
    },
    # Cut 67
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Frontal Medium Shot",
        "camera_movement": "Backward tracking moving with Thanos",
        "characters": "Thanos marching into Fire-Lasers",
        "action": "Thanos marches straight toward the camera into the convergent fire streams. The violet Power Stone on his raised gauntlet glows through the firestorm as he closes the final few feet."
    },
    # Cut 68
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Side-View Two-Shot",
        "camera_movement": "Fast lateral tracking",
        "characters": "Thanos knocking away twin beams",
        "action": "Reaching point-blank range, Thanos brings both massive fists down in a violent double hammer strike, violently swatting both of Iron Man's laser-firing hands downward and cutting off the beams."
    },
    # Cut 69
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Over-the-Shoulder Shot behind Iron Man",
        "camera_movement": "Quick tracking jerk on hit impact",
        "characters": "Thanos striking Tony's face (Punch 1)",
        "action": "With Iron Man's arms knocked aside, Thanos steps in and drives his left gauntleted fist straight into Tony's jaw at 73.74s, sending Tony stumbling backward."
    },
    # Cut 70
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Low-Angle Medium Two-Shot",
        "camera_movement": "Quick tilt-up tracking Thanos' second strike",
        "characters": "Thanos swinging Punch 2 / Tony cross-block",
        "action": "Thanos swings a heavy second right hook. Tony recovers his footing and desperately throws both arms up in an X-shaped cross-guard to intercept the blow, sparking heavily on impact at 74.58s."
    },
    # Cut 71
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Tight Close-Up Two-Shot",
        "camera_movement": "Static tight tension framing",
        "characters": "Gauntlet pressing down onto crossed forearms",
        "action": "Thanos' heavy golden gauntlet bears down with crushing force onto Tony's crossed forearms, slowly forcing Iron Man's defense downward through sheer brute strength."
    },
    # Cut 72
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Over-the-Shoulder Tony onto Thanos' Face",
        "camera_movement": "Static tight CU",
        "characters": "Thanos grimacing and pressing down",
        "action": "Thanos grimaces with cold, overwhelming resolve, putting all his colossal weight and muscle into crushing Tony's guard down."
    },
    # Cut 73
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Extreme Wide Landscape Shot",
        "camera_movement": "Static wide tableau",
        "characters": "Both combatants struggling in ruins",
        "action": "A wide view emphasizing the isolation and scale of the struggle on the ruined alien world, with Thanos towering over and bearing down upon the kneeling armored figure of Iron Man."
    },
    # Cut 74
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Medium Two-Shot Struggle",
        "camera_movement": "Dynamic handheld push",
        "characters": "Iron Man initiating counter-attack",
        "action": "Pinned beneath Thanos' grip, Tony shifts his weight and channels the suit's very last reserve of nanotech down to his left arm for a desperate surprise strike."
    },
    # Cut 75
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Low Close-Up on Tony Stark's Left Forearm",
        "camera_movement": "Static with dynamic blade extension",
        "characters": "Nanotech Dagger / Sword forming from arm",
        "action": "Liquid nanotech rapidly pools and solidifies from Tony's left forearm armor, extending forward into a razor-sharp, glowing blue-tinged nanotech blade / dagger ready to stab."
    },
    # Cut 76
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Medium Close-Up on Blade Thrust",
        "camera_movement": "Fast tracking follow matching blade thrust",
        "characters": "Tony thrusting blade / Thanos catching it",
        "action": "Tony thrusts the nanotech dagger upward toward Thanos' throat, but Thanos anticipates the move, his bare hand shooting out and catching the blade mid-thrust."
    },
    # Cut 77
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Wide Shot of Struggle over Blade",
        "camera_movement": "Static with violent physical shaking",
        "characters": "Struggle over the nanotech blade",
        "action": "Thanos pins Iron Man firmly down, gripping the nanotech blade with both hands as Tony desperately tries to force it forward with every ounce of strength."
    },
    # Cut 78
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Tight Close-Up on Tony Stark's Face",
        "camera_movement": "Static tight framing",
        "characters": "Tony Stark's agony and struggle",
        "action": "Tony grunts in breathless agony and despair as his grip weakens and Thanos' overwhelming strength turns the weapon against him."
    },
    # Cut 79
    {
        "chunk": "Chunk 8: Dual Fire-Lasers, Hand Struggle, and The Stab",
        "shot_type": "Medium Close-Up on Blade and Impact",
        "camera_movement": "Sudden shudder / freeze on stab penetration",
        "characters": "Thanos snaps blade and stabs Tony",
        "action": "With a swift, brutal twist, Thanos snaps the nanotech blade off Tony's forearm armor, turns the jagged point around, and plunges it straight through Tony's chest armor into his abdomen. Tony gasps in shock as Thanos stands over him. (The reference video ends on this final frame at 01:21.547 / 81.547s)."
    }
]

assert len(cut_details) == len(cuts)

# Build markdown content
md_lines = [
    "# Real Video Reference — Camera Cut List & Shot Breakdown",
    "",
    "> **Source Reference Video Files** (from `docs/images/threeway/README.md` & `reference/`):",
    "> - Clip 1: `Iron Man vs Thanos - Battle of Titan Scene Avengers Infinity War_5.88sec clip for claude.mp4` (Movie 0.000s – 5.881s, Frames 0–140)",
    "> - Clip 2: `Iron Man vs Thanos -05.888sec-18.10seconds.mp4` (Movie 5.881s – 15.849s, Frames 141–379)",
    "> - Clip 3: `Iron Man vs Thanos - 18sec.1 -1min22sec.6 full video  .mp4` (Movie 15.849s – 81.547s, Frames 380–1954)",
    "> - **Timeline Frame Rate**: 23.97602 fps (SMPTE Film standard)",
    "> - **Total Duration**: 01:21.547 (81.547 seconds, 1955 continuous frames)",
    "> - **Total Camera Cuts**: **79 Cuts** (counted every time the camera switches angle, perspective, or framing)",
    "",
    "---",
    "",
    "## Executive Summary & Cut Statistics",
    "",
    "| Chunk # | Scene Title | Movie Time Range | Reference Frames | Number of Cuts | Key Highlights |",
    "|---|---|---|---|:---:|---|",
    "| **Chunk 1** | Standoff and Dialogue | 00:00.000 – 00:18.101 | Frames 0 – 433 | **10 cuts** (Cuts 1–10) | Gauntlet raise, Iron Man supersonic landing, iconic dialogue ('Stark', 'You know me', 'Cursed with knowledge') |",
    "| **Chunk 2** | Missiles, Kick & Charge | 00:18.101 – 00:29.404 | Frames 434 – 704 | **11 cuts** (Cuts 11–21) | Pod launch, 'Come on!', 2-cut missile explosions (130a/130b), dropkick flip, ground lock, cannon ram charge |",
    "| **Chunk 3** | Helmet Tear & Skidding | 00:29.404 – 00:35.244 | Frames 705 – 844 | **6 cuts** (Cuts 22–27) | Helmet ripped off, bare Tony stunned, headbutt/punch, nanotech reform, skid in dust, Thanos laughs |",
    "| **Chunk 4** | Power Stone Beam & Counter | 00:35.244 – 00:45.545 | Frames 845 – 1091 | **14 cuts** (Cuts 28–41) | Purple beam torrent, nanotech tower shield, barrel roll boost, boot pin on gauntlet, 360-spin ram smash |",
    "| **Chunk 5** | Drop of Blood & Face-off | 00:45.545 – 00:52.761 | Frames 1092 – 1264 | **4 cuts** (Cuts 42–45) | Dazed Thanos, fingertip with crimson blood, 'All that for a drop of blood', iconic thumbnail face-off |",
    "| **Chunk 6** | Beatdown & Broken Helmet | 00:52.761 – 01:00.310 | Frames 1265 – 1445 | **12 cuts** (Cuts 46–57) | Leg sweep, horizontal flip, Tony pinned, Thanos brutal punches 1 & 2, gold faceplate shattered |",
    "| **Chunk 7** | Point-Blank Blast & March | 01:00.310 – 01:07.776 | Frames 1446 – 1624 | **6 cuts** (Cuts 58–63) | Point-blank purple blast, tumble into rubble, Thanos march, arm repulsor fire, chest nanotech regeneration |",
    "| **Chunk 8** | Dual Fire-Lasers & The Stab | 01:07.776 – 01:21.547 | Frames 1625 – 1954 | **16 cuts** (Cuts 64–79) | Searing fire-lasers, beam swat knock-away, crossed-arm struggle, nanotech sword reveal, sword break, and the chest stab |",
    "| **TOTAL** | **Entire Battle of Titan Scene** | **00:00.000 – 01:21.547** | **1955 Frames** | **79 CUTS** | **100% frame-accurate camera cut breakdown** |",
    "",
    "---",
    "",
    "## Master Camera Cut Table (1 to 79)",
    "",
    "| Cut # | Shot ID | Start Time | End Time | Duration | Ref Frames | Framing / Camera Angle | Scene Summary / Matter |",
    "|:---:|:---:|:---:|:---:|:---:|:---:|---|---|",
]

for i in range(len(cuts)):
    c = cuts[i]
    d = cut_details[i]
    md_lines.append(f"| **{c['cut_num']}** | `{c['shot_id']}` | `{c['t_start_str']}` ({c['t_start']:.3f}s) | `{c['t_end_str']}` ({c['t_end']:.3f}s) | {c['dur']:.3f}s ({c['n_frames']} fr) | f{c['f_start']}–f{c['f_end']} | {d['shot_type']} | {d['action'][:95]}... |")

md_lines.extend([
    "",
    "---",
    "",
    "## Comprehensive Detailed Cut Breakdown",
    "",
    "Every camera cut is documented with exact millisecond timings, 23.976 fps film frames, camera framing, camera motion, characters, and key visual/physical action matter for downstream agents.",
    ""
])

current_chunk = ""
for i in range(len(cuts)):
    c = cuts[i]
    d = cut_details[i]
    
    if d['chunk'] != current_chunk:
        current_chunk = d['chunk']
        md_lines.extend([
            f"### {current_chunk}",
            ""
        ])
    
    md_lines.extend([
        f"#### Cut {c['cut_num']}: Shot `{c['shot_id']}` ({c['t_start_str']} – {c['t_end_str']})",
        f"- **Pinpoint Timing**: Start `{c['t_start_str']}` ({c['t_start']:.3f}s) → End `{c['t_end_str']}` ({c['t_end']:.3f}s)",
        f"- **Duration**: `{c['dur']:.3f} seconds` ({c['n_frames']} frames at 23.976 fps)",
        f"- **Reference Frames**: `Frame {c['f_start']} to Frame {c['f_end']}` (continuous movie timeline index)",
        f"- **Camera Shot Type & Angle**: {d['shot_type']}",
        f"- **Camera Motion**: {d['camera_movement']}",
        f"- **Characters Visible**: {d['characters']}",
        f"- **Action / Scene Matter**:",
        f"  > {d['action']}",
        ""
    ])

md_lines.extend([
    "---",
    "",
    "## Technical Notes for Downstream Animation & Pipeline Agents",
    "",
    "1. **Relationship between Movie Cuts and Pipeline Shots (`scene.py`)**:",
    "   - In the pipeline, **Shot 130** was implemented as a single continuous 3.086-second camera push-in. In the real reference video, this sequence consists of **two distinct camera cuts**: **Cut 14 (`Shot 130a`)** (top-down diving behind missiles) and **Cut 15 (`Shot 130b`)** (wide profile view of the blast explosions and dust cloud). Downstream agents referencing video footage should note both cuts.",
    "2. **Continuous Frame Index Mapping**:",
    "   - `t < 5.881s` (Cut 1 to Cut 5): File frames `0..140` in `*5.88sec clip*.mp4`. Global frame = file frame.",
    "   - `5.881s <= t < 15.849s` (Cut 6 to Cut 9): File frames `0..238` in `*05.888sec-18.10seconds*.mp4`. Global frame = file frame + 141.",
    "   - `t >= 15.849s` (Cut 10 to Cut 79): File frames `0..1574` in `*18sec.1 -1min22sec.6 full video*.mp4`. Global frame = file frame + 380.",
    "3. **Physical Interactions & Contact Verification**:",
    "   - All punches, weapon impacts, foot locks, and struggles have been verified against exact frame boundaries. High-energy impact peaks (e.g., Cut 20 battering ram at 28.15s, Cut 41 fist smash at 45.39s, Cut 52 punch 1 at 56.14s, Cut 56 punch 2 at 58.77s, Cut 79 stab at 81.04s) correspond to physical contact moments.",
    "4. **Video End Boundary**:",
    "   - The reference file ends at 81.547 seconds (frame 1954). In film release timing, the stab penetration lingers for another ~1.0 second before cutting to Thanos' dialogue with Doctor Strange.",
    ""
])

content = "\n".join(md_lines)

with open('realvideo-camera.md', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully wrote realvideo-camera.md ({len(content)} bytes, {len(md_lines)} lines)")
