-- Director (synced by Rojo into StarterPlayer > StarterPlayerScripts)
-- Runs the scene camera and effects from SceneData in sync with the server's animation timeline.
--   Letterbox matches the movie frame (1920x1010). FOVs in SceneData are for that frame.
--   Overlay shows MOVIE time + movie FRAME number (23.976 fps) so any moment in a recording
--   can be matched to the reference exactly. T = toggle overlay.
--   Scrub mode: the scene frozen on one movie frame (server sends a fixed time).
--   [ / ] = step one frame back / forward while scrubbing.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local StarterGui = game:GetService("StarterGui")

-- Hide default Roblox CoreGui (Chat, Leaderboard, Backpack, Emotes)
task.spawn(function()
	for _ = 1, 20 do
		local ok = pcall(function()
			StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.All, false)
		end)
		if ok then
			break
		end
		task.wait(0.2)
	end
end)

local Scene = require(ReplicatedStorage:WaitForChild("SceneData"))
local sceneStart = ReplicatedStorage:WaitForChild("SceneStart")
local shotControl = ReplicatedStorage:WaitForChild("ShotControl")
local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local MOVIE_FPS = 23.976
local GROUND = Scene.rigs.Thanos.pos.Y                 -- stage surface (both rigs stand on it)

-- ------------------------------------------------------------------ overlay
local gui = Instance.new("ScreenGui")
gui.Name = "Director"
gui.IgnoreGuiInset = true
gui.ResetOnSpawn = false
gui.DisplayOrder = 10
gui.Enabled = false
gui.Parent = player:WaitForChild("PlayerGui")

local function bar()
	local f = Instance.new("Frame")
	f.BackgroundColor3 = Color3.new(0, 0, 0)
	f.BorderSizePixel = 0
	f.Parent = gui
	return f
end
local topBar, bottomBar = bar(), bar()

local label = Instance.new("TextLabel")
label.BackgroundTransparency = 0.4
label.BackgroundColor3 = Color3.new(0, 0, 0)
label.TextColor3 = Color3.fromRGB(255, 220, 80)
label.Font = Enum.Font.Code
label.TextSize = 22
label.TextXAlignment = Enum.TextXAlignment.Left
label.Size = UDim2.fromOffset(560, 30)
label.Parent = gui
local showLabel = false   -- the yellow frame/shot readout is hidden for the final video; T shows it again for review

local subtitle = Instance.new("TextLabel")             -- Y = toggle subtitles
subtitle.BackgroundTransparency = 1
subtitle.TextColor3 = Color3.new(1, 1, 1)
subtitle.TextStrokeTransparency = 0.3
subtitle.Font = Enum.Font.GothamMedium
subtitle.TextSize = 28
subtitle.AnchorPoint = Vector2.new(0.5, 1)
subtitle.Size = UDim2.new(0.9, 0, 0, 40)
subtitle.Parent = gui
local showSubs = true

local function subtitleAt(tau)
	for _, s in ipairs(Scene.subs or {}) do
		if tau >= s.t0 and tau < s.t1 then
			return s.text
		end
	end
	return ""
end

local hud                                              -- helmet HUD frame, built below

-- ------------------------------------------------------------------ helpers
local function ease(u)
	u = math.clamp(u, 0, 1)
	return u * u * (3 - 2 * u)
end

-- the body PART by that name: custom models often keep armour in sub-models named like the parts
local function bodyPart(rig, name)
	for _, c in ipairs(rig:GetChildren()) do
		if c.Name == name and c:IsA("BasePart") then
			return c
		end
	end
	return nil
end

local function findPart(path)
	if not path or type(path) ~= "string" then
		return nil, 1
	end
	local rigName, partName = string.match(path, "^(.-)%.(.+)$")
	if not rigName or not partName then
		return nil, 1
	end
	local rig = workspace:FindFirstChild(rigName)
	return rig and bodyPart(rig, partName), rig and rig:GetAttribute("SizeRatio") or 1
end

local function resolve(spec)
	if spec[1] == "World" then                                -- an absolute point (static set-ups)
		return spec[2]
	end
	local part, ratio = findPart(spec[1])
	return (part and part.Position or Vector3.zero) + spec[2] * ratio
end

local function shotAt(tau)
	local current = Scene.shots[1]
	for _, shot in ipairs(Scene.shots) do
		if shot.start <= tau then
			current = shot
		end
	end
	return current
end

local function cameraAt(shot, localT)
	-- mask shots with a face camera: the lens sits in front of Tony's face along the head's own forward axis, with the
	-- head's own up as screen up, so his face stays upright and centred whether he stands or lies on his back
	-- (world offsets rolled it ~40 degrees). yaw turns the face toward screen right, roll tilts it.
	local fc = shot.face
	local head = fc and findPart("IronMan.Head")
	if head then
		local cf = head.CFrame * CFrame.Angles(0, math.rad(fc.yaw or 0), 0) * CFrame.Angles(math.rad(fc.pitch or 0), 0, 0)
		local pos = head.Position + cf.LookVector * (fc.dist or 2.8)
		-- aim a little ABOVE the head centre so the features (eyes high, mouth low) both sit inside the visor frame
		local view = CFrame.lookAt(pos, head.Position + head.CFrame.UpVector * 0.25, cf.UpVector) * CFrame.Angles(0, 0, math.rad(fc.roll or 0))
		return view, shot.cam[1].fov
	end
	local keys = shot.cam
	local k0, k1 = keys[1], keys[1]
	for i, k in ipairs(keys) do
		if k.t <= localT then
			k0, k1 = k, keys[i + 1] or k
		end
	end
	local u = (k1 == k0) and 0 or ease((localT - k0.t) / (k1.t - k0.t))
	local pos = resolve(k0.pos):Lerp(resolve(k1.pos), u)
	local look = resolve(k0.look):Lerp(resolve(k1.look), u)
	pos = look + (pos - look) * (Scene.pullback or 1)      -- dolly back along the line of sight
	local roll = (k0.roll or 0) + ((k1.roll or 0) - (k0.roll or 0)) * u
	local view = CFrame.lookAt(pos, look)
	if roll ~= 0 then
		view = view * CFrame.Angles(0, 0, math.rad(roll))
	end
	return view, k0.fov + (k1.fov - k0.fov) * u
end

-- letterbox to the movie aspect; returns how much taller the viewport is than the frame
local function layoutFrame()
	local vp = camera.ViewportSize
	local frameH = math.min(vp.Y, vp.X / Scene.aspect)
	local barH = math.floor((vp.Y - frameH) / 2 + 0.5)
	topBar.Size, topBar.Position = UDim2.new(1, 0, 0, barH), UDim2.new(0, 0, 0, 0)
	bottomBar.Size, bottomBar.Position = UDim2.new(1, 0, 0, barH), UDim2.new(0, 0, 1, -barH)
	label.Position = UDim2.fromOffset(12, math.max(barH + 8, 54))
	subtitle.Position = UDim2.new(0.5, 0, 1, -(barH + 24))
	if hud then
		hud.Position, hud.Size = UDim2.fromOffset(0, barH), UDim2.new(1, 0, 1, -2 * barH)
	end
	return vp.Y / frameH
end

-- ------------------------------------------------------------------ effects
local fxFolder = nil

local function newPart(props)
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	for k, v in pairs(props) do
		p[k] = v
	end
	p.Parent = fxFolder
	return p
end

-- ------------------------------------------------------------------ particle toolkit
-- Realistic layers built from the vetted flipbooks in VFXAssets: fireballs (additive), rolling
-- smoke, ground dust, sparks, physical rock chunks, shockwave rings, flash light, camera shake.
-- Particles live in real time, so bursts fire when the timeline crosses their moment (live
-- playback); a scrubbed frame just after a hit gets the burst too, aged as far as the capture.
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")
-- Trails, emitters and physics chunks only run during live playback (a scrub would smear them).
local fxLive = true
local VFX = require(ReplicatedStorage:WaitForChild("VFXAssets"))
local SPARK = "rbxasset://textures/particles/sparkles_main.dds"

local function kp(t, v)
	return NumberSequenceKeypoint.new(t, v)
end

local function ckp(t, c)
	return ColorSequenceKeypoint.new(t, c)
end

local function grow(a, b)                                     -- size over life a -> b
	return NumberSequence.new({ kp(0, a), kp(1, b) })
end

local SMOKE_FADE = NumberSequence.new({ kp(0, 0.2), kp(0.6, 0.55), kp(1, 1) })
local FIRE_FADE = NumberSequence.new({ kp(0, 0), kp(0.7, 0.3), kp(1, 1) })

local function emitter(parent, asset, props)
	local e = Instance.new("ParticleEmitter")
	local a = asset and VFX[asset]
	if a then
		e.Texture, e.FlipbookLayout, e.FlipbookMode = a.image, a.layout, a.mode
		e.LightEmission, e.LightInfluence = a.additive and 1 or 0, a.additive and 0 or 1
	end
	e.Rate, e.Enabled = 0, false
	e.Rotation, e.RotSpeed = NumberRange.new(0, 360), NumberRange.new(-30, 30)
	for k, v in pairs(props) do
		e[k] = v
	end
	e.Parent = parent
	return e
end

local function anchorAt(pos, life)
	local p = newPart({ Transparency = 1, Size = Vector3.one * 0.1, CFrame = CFrame.new(pos) })
	local a = Instance.new("Attachment")
	a.Parent = p
	Debris:AddItem(p, life or 9)
	return a
end

local function flashLight(att, color, brightness, range, dur)
	local l = Instance.new("PointLight")
	l.Color, l.Brightness, l.Range, l.Shadows = color, brightness, range, false
	l.Parent = att
	TweenService:Create(l, TweenInfo.new(dur, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
end

-- rock chunks thrown by a blast: real physics parts that arc, tumble and bounce off the ground
local ROCK = { Color3.fromRGB(58, 48, 40), Color3.fromRGB(72, 60, 50), Color3.fromRGB(44, 38, 33) }
local function chunks(pos, n, s, up)
	if not fxLive then
		return
	end
	local rng = Random.new()
	for _ = 1, n do
		local size = rng:NextNumber(0.18, 0.55) * s
		local c = Instance.new("Part")
		c.Size = Vector3.new(size, size * rng:NextNumber(0.5, 0.9), size * rng:NextNumber(0.7, 1.3))
		c.CFrame = CFrame.new(pos + Vector3.new(0, 0.4, 0)) * CFrame.Angles(rng:NextNumber(0, 6), rng:NextNumber(0, 6), 0)
		c.Material, c.Color = Enum.Material.Slate, ROCK[rng:NextInteger(1, #ROCK)]
		c.CanQuery, c.CanTouch, c.Anchored = false, false, false
		c.Parent = fxFolder
		local dir = Vector3.new(rng:NextNumber(-1, 1), 0, rng:NextNumber(-1, 1))
		dir = dir.Magnitude > 0 and dir.Unit or Vector3.xAxis
		c.AssemblyLinearVelocity = dir * rng:NextNumber(8, 20) * s + Vector3.new(0, rng:NextNumber(10, 22) * (up or 1), 0)
		c.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-15, 15), rng:NextNumber(-15, 15), rng:NextNumber(-15, 15))
		Debris:AddItem(c, 3.5)
	end
end

local function shockwave(pos, radius, color, dur)
	local ring = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.12, 0.5, 0.5), Color = color,
		Material = Enum.Material.SmoothPlastic, Transparency = 0.35,
		CFrame = CFrame.new(pos) * CFrame.Angles(0, 0, math.rad(90)) })
	TweenService:Create(ring, TweenInfo.new(dur, Enum.EasingStyle.Quart, Enum.EasingDirection.Out),
		{ Size = Vector3.new(0.05, radius * 2, radius * 2), Transparency = 1 }):Play()
	Debris:AddItem(ring, dur + 0.1)
end

-- camera shake: decaying, deterministic in tau, so scrub and playback agree
local shakes = {}
local function addShake(t, amp, decay)
	table.insert(shakes, { t = t, amp = amp, decay = decay or 7 })
end

local function shakeAt(tau)
	local a = 0
	for _, s in ipairs(shakes) do
		local e = tau - s.t
		if e >= 0 and e < 1.5 then
			a += s.amp * math.exp(-e * s.decay)
		end
	end
	if a < 1e-3 then
		return CFrame.new()
	end
	return CFrame.new(math.noise(tau * 23, 1.3) * a * 0.35, math.noise(tau * 23, 7.1) * a * 0.35, 0)
		* CFrame.Angles(math.rad(math.noise(tau * 19, 3.7) * a * 2.2), math.rad(math.noise(tau * 19, 9.2) * a * 2.2), 0)
end

-- the big one: a missile / blast hitting the ground at pos
local function explosion(pos, s)
	local a = anchorAt(pos, 9)
	emitter(a, "fireball", { Size = grow(1.8 * s, 5 * s), Lifetime = NumberRange.new(0.55, 0.85), Speed = NumberRange.new(2 * s, 7 * s),
		SpreadAngle = Vector2.new(180, 180), Drag = 5, Brightness = 1.2, Transparency = FIRE_FADE, ZOffset = 1,
		Color = ColorSequence.new(Color3.fromRGB(255, 170, 100), Color3.fromRGB(200, 80, 30)) }):Emit(6)
	emitter(a, "smokeSoft", { Size = grow(2 * s, 7.5 * s), Lifetime = NumberRange.new(2.2, 3.4), Speed = NumberRange.new(3 * s, 7 * s),
		EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(65, 65), Drag = 2.8, Acceleration = Vector3.new(0, 0.4, 0),
		Transparency = SMOKE_FADE, Color = ColorSequence.new(Color3.fromRGB(70, 60, 52), Color3.fromRGB(118, 102, 86)) }):Emit(7)
	emitter(a, "smokeSoft", { Size = grow(1.6 * s, 8 * s), Lifetime = NumberRange.new(1.6, 2.6), Speed = NumberRange.new(14 * s, 22 * s),
		EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(84, 84), Drag = 4, Acceleration = Vector3.new(0, -3, 0),
		Transparency = SMOKE_FADE, Color = ColorSequence.new(Color3.fromRGB(120, 100, 80)) }):Emit(10)        -- the ground dust wave
	emitter(a, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.35 * s, 0), Lifetime = NumberRange.new(0.35, 0.9),
		Speed = NumberRange.new(18 * s, 34 * s), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -35, 0), Drag = 1.5,
		Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NumberSequence.new(-1.5),
		Color = ColorSequence.new(Color3.fromRGB(255, 220, 160), Color3.fromRGB(255, 140, 60)) }):Emit(28)
	flashLight(a, Color3.fromRGB(255, 170, 100), 2.5, 14 * s, 0.35)
	shockwave(pos + Vector3.new(0, 0.15, 0), 9 * s, Color3.fromRGB(150, 128, 104), 0.45)
	chunks(pos, 6, s)
end

-- an energy hit on a body (kick, cannon slam): bright burst, sparks, a light smoke puff
local function energyHit(pos, s, color, sparksOnly)
	local a = anchorAt(pos, 6)
	if not sparksOnly then
		emitter(a, "fireballAlt", { Size = grow(1.2 * s, 4 * s), Lifetime = NumberRange.new(0.25, 0.4), Speed = NumberRange.new(math.min(1, 4 * s), 4 * s),
		SpreadAngle = Vector2.new(180, 180), Drag = 6, Brightness = 3, Transparency = FIRE_FADE, ZOffset = 2,
		Color = ColorSequence.new(Color3.new(1, 1, 1), color) }):Emit(5)
	end
	emitter(a, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.25 * s, 0), Lifetime = NumberRange.new(0.25, 0.6),
		Speed = NumberRange.new(20 * s, 36 * s), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, -25, 0), Drag = 2,
		Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NumberSequence.new(-1.5),
		Color = ColorSequence.new(Color3.new(1, 1, 1), color) }):Emit(22)
	emitter(a, "smokeSoft", { Size = grow(1 * s, 4 * s), Lifetime = NumberRange.new(1, 1.6), Speed = NumberRange.new(math.min(2, 5 * s), 5 * s),
		SpreadAngle = Vector2.new(180, 180), Drag = 3, Transparency = SMOKE_FADE,
		Color = ColorSequence.new(Color3.fromRGB(150, 150, 160)) }):Emit(6)
	flashLight(a, color, sparksOnly and 2 or 8, 14 * s, 0.3)
end

-- boots hitting the ground: a low dust burst rolling outward, a few chunks
local function dustHit(pos, s)
	local a = anchorAt(pos, 6)
	emitter(a, "smokeSoft", { Size = grow(1 * s, 5 * s), Lifetime = NumberRange.new(1.2, 2), Speed = NumberRange.new(8 * s, 14 * s),
		EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(86, 86), Drag = 4, Acceleration = Vector3.new(0, -2, 0),
		Transparency = SMOKE_FADE, Color = ColorSequence.new(Color3.fromRGB(118, 98, 78)) }):Emit(18)
	shockwave(pos + Vector3.new(0, 0.1, 0), 3.5 * s, Color3.fromRGB(130, 110, 90), 0.35)
	chunks(pos, 4, s * 0.6, 0.5)
end

-- fires once when the timeline crosses t (or a scrub lands just after it)
local function crossed(state, key, t, tau)
	state.last = state.last or {}
	local before = state.last[key]
	state.last[key] = tau
	return tau >= t and tau - t < 0.6 and (before == nil or before < t)
end

-- Iron Man's nanotech piece: a palm-sized dark red plate with six gripping spokes and a glowing core (the reference
-- shows a red mechanism clamped over Thanos' palm), pink trail while flying, flash on hit. It lies on the hand's +X face:
-- the poses aim +X at the camera as the 'palm' (the owner's gauntlet model's true palm is +Y).
local function buildNanoshot(fx)
	local _, ratio = findPart(fx.target)
	local s = ratio
	local plate = newPart({ Size = Vector3.new(0.1, 1.2, 1.1) * s, Color = Color3.fromRGB(110, 14, 22), Material = Enum.Material.Metal })
	local core = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 0.34 * s,
		Color = Color3.fromRGB(190, 230, 255), Material = Enum.Material.Neon })
	local spokes = {}
	for i = 1, 6 do
		spokes[i] = newPart({ Size = Vector3.new(0.08, 0.09, 0.62) * s, Color = Color3.fromRGB(150, 22, 30), Material = Enum.Material.Metal })
	end
	local glow = Instance.new("PointLight")
	glow.Color, glow.Range, glow.Brightness = Color3.fromRGB(170, 210, 255), 6 * s, 2
	glow.Parent = core
	local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
	a0.Position, a1.Position = Vector3.new(0, 0.25, 0) * s, Vector3.new(0, -0.25, 0) * s
	a0.Parent, a1.Parent = plate, plate
	local trail = Instance.new("Trail")
	trail.Attachment0, trail.Attachment1 = a0, a1
	trail.Color = ColorSequence.new(Color3.fromRGB(255, 180, 50), Color3.fromRGB(255, 50, 20))
	trail.LightEmission, trail.Lifetime = 1, 0.18
	trail.Transparency = NumberSequence.new(0.05, 1)
	trail.Parent = plate
	local flareLight = Instance.new("PointLight")
	flareLight.Color, flareLight.Range, flareLight.Brightness = Color3.fromRGB(255, 140, 40), 14 * s, 0
	flareLight.Parent = plate
	local flash = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 0.2, Color = Color3.fromRGB(255, 140, 40),
		Material = Enum.Material.Neon, Transparency = 1 })
	local flashLight = Instance.new("PointLight")
	flashLight.Color, flashLight.Range, flashLight.Brightness = Color3.fromRGB(255, 140, 40), 14 * s, 0
	flashLight.Parent = flash
	local streak = newPart({ Size = Vector3.new(0.2, 0.2, 5.5) * s, Color = Color3.fromRGB(255, 130, 40),
		Material = Enum.Material.Neon, Transparency = 1 })
	addShake(fx.t + fx.dur, 0.12, 9)
	return { fx = fx, plate = plate, core = core, glow = glow, spokes = spokes, trail = trail, flareLight = flareLight, flash = flash, flashLight = flashLight, streak = streak, scale = s }
end

local function updateNanoshot(n, tau)
	local fx = n.fx
	local hand = findPart(fx.target)
	if not hand then
		return
	end
	local attached = hand.CFrame * CFrame.new(fx.localOffset * n.scale)
	local hit = fx.t + fx.dur
	local visible = tau >= fx.t
	n.plate.Transparency, n.core.Transparency = visible and 0 or 1, visible and 0 or 1
	if n.glow then n.glow.Enabled = visible end
	n.trail.Enabled = visible and tau < hit + 0.05
	n.flareLight.Brightness = (visible and tau < hit) and 8 or 0

	if tau >= fx.t and tau <= hit + 0.04 then
		local head = findPart("Thanos.Head")
		if head then
			local u = math.clamp((tau - fx.t) / fx.dur, 0, 1)
			n.streak.Transparency = 0
			n.streak.CFrame = CFrame.new(head.Position.X - 1.4 * n.scale, head.Position.Y + 0.15, head.Position.Z - 6.0 + u * 12.0)
		else
			n.streak.Transparency = 1
		end
	else
		n.streak.Transparency = 1
	end

	local cf = CFrame.identity
	if tau < hit then
		local u = math.clamp((tau - fx.t) / fx.dur, 0, 1)
		local from = attached.Position + fx.from * n.scale
		local pos = from:Lerp(attached.Position, u * u)            -- accelerates into the hand
		cf = CFrame.lookAt(pos, attached.Position) * CFrame.Angles(0, math.rad(90), 0)
	elseif not fx.pull or tau < fx.pull then
		cf = attached                                                -- stuck to the palm
	else
		-- pulled out by his other hand, held a moment, then flung away tumbling (ballistic)
		local other = findPart(fx.hand)
		local release = fx.pull + 0.3
		if tau < release and other then
			cf = other.CFrame * CFrame.new(0, -0.25 * n.scale, 0) * CFrame.Angles(0.4, 0, 0.8)
		else
			n.releaseAt = n.releaseAt or (other and other.Position or attached.Position)
			local e = tau - release
			local pos = n.releaseAt + fx.fling * e + Vector3.new(0, -40, 0) * (0.5 * e * e)
			local gone = e > 1.2 or pos.Y < GROUND
			if gone then
				n.plate.Transparency, n.core.Transparency = 1, 1
				if n.glow then n.glow.Enabled = false end
				cf = CFrame.new(0, -500, 0)
			else
				n.plate.Transparency, n.core.Transparency = 0, 0
				cf = CFrame.new(pos) * CFrame.Angles(e * 17, e * 11, e * 7)
			end
		end
		if tau < release then
			n.releaseAt = nil
		end
		if crossed(n, "pull", fx.pull, tau) then                     -- tearing it out of the gauntlet
			energyHit(attached.Position, 0.3 * n.scale, Color3.fromRGB(230, 140, 255))
		end
	end
	n.plate.CFrame = cf
	n.core.CFrame = cf * CFrame.new(0.07 * n.scale, 0, 0)
	for i, sp in ipairs(n.spokes) do                              -- spokes clamp outward over the palm
		sp.CFrame = cf * CFrame.Angles(math.rad(60 * i), 0, 0) * CFrame.new(0.07 * n.scale, 0, -0.4 * n.scale)
		sp.Transparency = n.plate.Transparency
	end
	if crossed(n, "hit", hit, tau) then                              -- sparks off the gauntlet as it strikes
		energyHit(attached.Position, 0.45 * n.scale, Color3.fromRGB(230, 140, 255))
	end
	local f = (tau - hit) / 0.18                                     -- impact flash, 0.18 s
	if f >= 0 and f <= 1 then
		n.flash.CFrame = attached
		n.flash.Size = Vector3.one * (0.3 + 3.2 * f) * n.scale
		n.flash.Transparency = 0.15 + 0.85 * f
		n.flashLight.Brightness = 8 * (1 - f)
	else
		n.flash.Transparency, n.flashLight.Brightness = 1, 0
	end
end


-- Five missile pods on Iron Man's chest (movie 110): two high on the collar ridge, two mid-chest, one low left.
-- slot = { across the chest (-1 left .. 1 right), up the chest (-1 .. 1), tilt sign }, measured on the frame
local POD_SLOTS = {
	{ -0.33, 0.95, -1 },
	{ 0.42, 0.95, 1 },
	{ -0.22, 0.10, -1 },
	{ 0.69, 0.20, 1 },
	{ -0.93, -0.75, -1 },
}

local function podCFrame(torso, slot, out)
	local sx, sy, sz = torso.Size.X, torso.Size.Y, torso.Size.Z
	return torso.CFrame * CFrame.new(slot[1] * sx / 2, slot[2] * sy / 2 + 0.12 * out, -sz * 0.5 - 0.02)
		* CFrame.Angles(math.rad(-15), math.rad(slot[3] * 12), 0)
end

local function buildPods(fx)
	local pods = {}
	for i, slot in ipairs(POD_SLOTS) do
		local housing = newPart({ Size = Vector3.new(0.65, 0.35, 0.65), Color = Color3.fromRGB(80, 75, 70), Material = Enum.Material.Metal })
		local tubes = newPart({ Size = Vector3.new(0.55, 0.28, 0.15), Color = Color3.fromRGB(30, 28, 26), Material = Enum.Material.Metal })
		local flare = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 0.22, Color = Color3.fromRGB(170, 215, 255), Material = Enum.Material.Neon, Transparency = 1 })
		local light = Instance.new("PointLight")
		light.Color, light.Range, light.Brightness = Color3.fromRGB(150, 200, 255), 8, 0
		light.Parent = flare
		local fire = emitter(flare, "fireball", { Size = grow(0.35, 1.1), Lifetime = NumberRange.new(0.12, 0.25),
			Speed = NumberRange.new(8, 16), EmissionDirection = Enum.NormalId.Back,
			Color = ColorSequence.new(Color3.fromRGB(255, 230, 130), Color3.fromRGB(255, 100, 30)), Rate = 90 })
		local smoke = emitter(flare, "smokeSoft", { Size = grow(0.25, 1.4), Lifetime = NumberRange.new(0.4, 0.8),
			Speed = NumberRange.new(4, 8), EmissionDirection = Enum.NormalId.Back,
			Color = ColorSequence.new(Color3.fromRGB(210, 200, 190)), Rate = 50 })
		pods[i] = { slot = slot, housing = housing, tubes = tubes, flare = flare, light = light, fire = fire, smoke = smoke, delay = fx.grow * 0.4 * (i - 1) }
	end
	return { fx = fx, pods = pods }
end

local function updatePods(state, tau)
	local fx = state.fx
	local torso = findPart(fx.target)
	for _, p in ipairs(state.pods) do
		local out = math.clamp((tau - fx.t - p.delay) / (fx.grow * 0.5), 0, 1)
		local shown = torso and out > 0 and tau < fx.t1
		p.housing.Transparency, p.tubes.Transparency = shown and 0 or 1, shown and 0 or 1
		local firing = shown and (tau >= fx.t + 0.30)
		p.flare.Transparency = firing and 0.2 or 1
		p.light.Brightness = firing and 5 or 0
		p.fire.Enabled = firing
		p.smoke.Enabled = firing
		if shown then
			local cf = podCFrame(torso, p.slot, ease(out))
			p.housing.CFrame = cf
			p.tubes.CFrame = cf * CFrame.new(0, 0, -0.28)
			p.flare.CFrame = cf * CFrame.new(0, 0, -0.45)
		end
	end
end

local function bezier(a, b, c, d, s)
	local u = 1 - s
	return a * u ^ 3 + b * 3 * u * u * s + c * 3 * u * s * s + d * s ^ 3
end

-- One missile per pod: climbs from the pod, curls through the sky, dives onto Thanos, explodes.
local function buildMissiles(fx)
	local list = {}
	for i = 1, fx.n do
		local rng = Random.new(fx.seed * 100 + i)
		-- a smooth energy pod: a stretched sphere (no flat ends, no sharp edges), a soft glow shell and a rounded blue energy stream
		local head = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.new(1.5, 0.16, 0.16), Color = Color3.fromRGB(10, 70, 255), Material = Enum.Material.Neon })   -- thin jet body
		local light = Instance.new("PointLight")
		light.Color, light.Range, light.Brightness = Color3.fromRGB(40, 110, 255), 6, 2
		light.Parent = head
		local energy = emitter(head, nil, { Texture = "rbxasset://textures/particles/sparkles_main.dds", LightEmission = 1, Size = grow(0.10, 0.3),
			Lifetime = NumberRange.new(0.12, 0.25), Speed = NumberRange.new(2, 5), EmissionDirection = Enum.NormalId.Back,
			SpreadAngle = Vector2.new(20, 20), Transparency = NumberSequence.new({ kp(0, 0.1), kp(1, 1) }),
			Color = ColorSequence.new(Color3.fromRGB(200, 240, 255), Color3.fromRGB(40, 120, 255)), Rate = 30 })
		local trails = {}
		local fire = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = Color3.fromRGB(255, 170, 80),
			Material = Enum.Material.Neon, Transparency = 1 })
		local flash = Instance.new("PointLight")
		flash.Color, flash.Range, flash.Brightness = Color3.fromRGB(255, 160, 90), 14, 0
		flash.Parent = fire
		local puff = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = Color3.fromRGB(92, 78, 62),
			Material = Enum.Material.Sand, Transparency = 1 })                      -- matte: no shiny highlight
		-- the smoke trail: real billowing particles left behind in the air
		local smoke = emitter(head, "smokeSoft", { Size = grow(0.35, 2.6), Lifetime = NumberRange.new(1.4, 2.2),
			Speed = NumberRange.new(0.3, 1.2), EmissionDirection = Enum.NormalId.Back, SpreadAngle = Vector2.new(12, 12),
			Drag = 1.5, Transparency = NumberSequence.new({ kp(0, 0.35), kp(0.5, 0.65), kp(1, 1) }),
			Color = ColorSequence.new(Color3.fromRGB(196, 188, 178), Color3.fromRGB(140, 128, 116)), Rate = 55 })
		local hitAt = fx.hit0 + (fx.hit1 - fx.hit0) * rng:NextNumber()
		addShake(hitAt, 0.22)
		list[i] = {
			head = head, energy = energy, trails = trails, fire = fire, flash = flash, puff = puff, smoke = smoke,
			launch = fx.launch0 + (fx.launch1 - fx.launch0) * rng:NextNumber(),
			hit = hitAt,
			up = Vector3.new(rng:NextNumber(-24, 24), rng:NextNumber(8, 30), rng:NextNumber(-24, 24)),   -- random spread, not one upward group
			over = Vector3.new(rng:NextNumber(-5, 5), rng:NextNumber(18, 24), rng:NextNumber(-5, 5)),   -- high, almost straight above him, so the last part is a dive from above (movie 21.8-22.2)
			land = Vector3.new(rng:NextNumber(-2.5, 2.5), rng:NextNumber(0.55, 0.95), rng:NextNumber(-2.5, 2.5)),   -- hits his body (chest/shoulders), not the ground
			phase = rng:NextNumber(0, math.pi * 2), slot = POD_SLOTS[(i - 1) % #POD_SLOTS + 1],
		}
	end
	return { fx = fx, list = list }
end

local function missileAt(m, torso, target, tau)
	-- launched from BEHIND his shoulders (movie 19.3-20.2: the blue trails come off his back, then arc over him).
	-- Iron Man faces +Z-ish toward Thanos, so his back is the torso's +Z side (the pods sit on its -Z chest).
	local p0 = (torso.CFrame * CFrame.new(m.slot[1] * torso.Size.X / 2, torso.Size.Y * 0.35, torso.Size.Z * 0.55)).Position
	local p3 = Vector3.new(target.X + m.land.X, GROUND + m.land.Y * (target.Y - GROUND), target.Z + m.land.Z)   -- ground .. chest
	local s = math.clamp((tau - m.launch) / (m.hit - m.launch), 0, 1)
	local w = math.sin(math.pi * s) * 3                                      -- curls, none at either end
	local wobble = Vector3.new(math.sin(m.phase + 9 * s), 0.6 * math.cos(m.phase + 7 * s), math.cos(m.phase + 9 * s)) * w
	return bezier(p0, p0 + m.up, target + m.over, p3, s) + wobble, p3
end

local function buildBlast(fx)
	return { fx = fx }
end

local function updateBlast(state, tau)
	local fx = state.fx
	local target = findPart(fx.at)
	if target and crossed(state, "boom", fx.t, tau) then
		explosion(target.Position + fx.offset, fx.size)
	end
end

local function buildSmokecloud(fx)
	local anchor = newPart({ Transparency = 1, Size = Vector3.one * 0.5, CFrame = CFrame.new(0, -500, 0) })
	local smoke = emitter(anchor, "smokeSoft", { Size = grow(6, 16), Lifetime = NumberRange.new(2.6, 4.0),
		Speed = NumberRange.new(1, 3), SpreadAngle = Vector2.new(180, 180), Drag = 1.2,
		Transparency = NumberSequence.new({ kp(0, 0.05), kp(0.5, 0.12), kp(1, 1) }),
		Color = ColorSequence.new(Color3.fromRGB(96, 86, 76), Color3.fromRGB(44, 40, 38)), Rate = 0 })
	return { fx = fx, anchor = anchor, smoke = smoke }
end

local function updateSmokecloud(state, tau)
	local fx = state.fx
	local target = findPart(fx.at)
	local on = target and tau >= fx.t and tau < fx.t1
	if target then
		state.anchor.CFrame = target.CFrame * CFrame.new(0, 0.5, 0)
	end
	state.smoke.Enabled = on and fxLive
	state.smoke.Rate = on and (fx.rate or 60) or 0
end

local function buildWall(fx)
	local rng = Random.new(77)
	local sz = typeof(fx.size) == "Vector3" and fx.size or Vector3.new(fx.size[1], fx.size[2], fx.size[3])   -- SceneData may send a Vector3
	local slab = newPart({ Size = sz, Color = Color3.fromRGB(118, 100, 84), Material = Enum.Material.Rock, Transparency = 1 })
	local pieces = {}
	for i = 1, 14 do
		local s = rng:NextNumber(2.0, 4.5)
		pieces[i] = { part = newPart({ Size = Vector3.new(s, s * 0.7, s * 0.9), Color = Color3.fromRGB(110, 94, 80), Material = Enum.Material.Rock, Transparency = 1 }),
			vel = Vector3.new(rng:NextNumber(-8, 8), rng:NextNumber(6, 14), rng:NextNumber(-8, 8)), spin = rng:NextNumber(-6, 6) }
	end
	return { fx = fx, slab = slab, pieces = pieces, rng = rng }
end

local function updateWall(state, tau)
	local fx = state.fx
	local target, im = findPart("Thanos.UpperTorso"), findPart("IronMan.UpperTorso")   -- the fighters' torsos (roots sit far apart in the rig)
	if not (target and im) then return end
	if tau >= fx.t and not state.pos and fx.pos then
		-- a fixed world position from the scene (reproducible, no dependence on when it is first seen)
		local p = typeof(fx.pos) == "Vector3" and fx.pos or Vector3.new(fx.pos[1], fx.pos[2], fx.pos[3])
		state.dir = Vector3.new(0, 0, 1)
		state.pos = p
		state.slab.CFrame = CFrame.lookAt(p, p + state.dir)
	elseif tau >= fx.t and not state.pos then
		-- fixed where Thanos stood when the blow landed, on the side away from Iron Man
		local push = Vector3.new(target.Position.X - im.Position.X, 0, target.Position.Z - im.Position.Z).Unit
		state.dir = push
		state.pos = target.Position + push * fx.gap
		state.slab.CFrame = CFrame.lookAt(state.pos, state.pos + push)
	end
	if not state.pos then return end
	if tau < fx.breakT then
		state.slab.Transparency = 0
	elseif not state.broke then
		state.broke = true
		state.slab.Transparency = 1
		explosion(state.pos - state.dir * 1.5, 1.6)     -- dust burst where the wall breaks
		for _, p in ipairs(state.pieces) do
			local off = Vector3.new(state.rng:NextNumber(-2, 2), state.rng:NextNumber(-1, 2), state.rng:NextNumber(-2, 2))
			p.part.CFrame = CFrame.new(state.pos + off)
			p.part.Transparency = 0
			p.part.Anchored = false
			p.part.CanCollide = false
			p.part.AssemblyLinearVelocity = p.vel + state.dir * 14
			p.part.AssemblyAngularVelocity = Vector3.new(p.spin, p.spin, p.spin)
		end
	end
	if state.broke and tau - fx.breakT > 3.5 then
		for _, p in ipairs(state.pieces) do
			p.part.Transparency = 1
		end
	end
end

local function updateMissiles(state, tau)
	local fx = state.fx
	local torso, target = findPart(fx.target), findPart(fx.at)
	if not (torso and target) then
		return
	end
	for _, m in ipairs(state.list) do
		local flying = tau >= m.launch and tau < m.hit
		local pos, p3 = missileAt(m, torso, target.Position, tau)
		m.head.Transparency = flying and 0 or 1
		m.head.PointLight.Enabled = flying
		for _, trail in ipairs(m.trails) do
			trail.Enabled = flying and fxLive
		end
		m.smoke.Enabled = false   -- no smoke on the rockets' tracks (reference)
		if crossed(m, "boom", m.hit, tau) then
			local _, land = missileAt(m, torso, target.Position, m.hit)
			explosion(land, 1)   -- realvideo cut 15 (130b): impacts, fireballs and a smoke cloud engulfing him
		end
		if flying then
			local ahead = missileAt(m, torso, target.Position, tau + 0.01)
			m.head.CFrame = CFrame.lookAt(pos, ahead) * CFrame.Angles(0, math.rad(90), 0)   -- long body (X) along the flight
		else
			m.head.CFrame = CFrame.new(pos)
		end
			m.energy.Enabled = flying and fxLive
			local e = tau - m.hit                                                   -- explosion clock
		if e >= 0 and e < 1.2 then                                              -- gone before 140 (its camera is right here)
			-- only a white-hot core for the first frames; the particles carry the explosion
			local g = math.clamp(e / 0.06, 0, 1)
			m.fire.CFrame = CFrame.new(p3)
			m.fire.Color = Color3.fromRGB(255, 235, 200)
			m.fire.Size = Vector3.one * (0.3 + 1.4 * g)
			m.fire.Transparency = math.clamp((e - 0.03) / 0.12, 0, 1)
			m.flash.Brightness = 0
			m.puff.Transparency = 1
		else
			m.fire.Transparency, m.puff.Transparency, m.flash.Brightness = 1, 1, 0
		end
	end
end

-- A missile whipping past the lens: a horizontal blue streak across the frame.
local fxLayer = Instance.new("Frame")                        -- screen-space FX; cleared with the scene FX
fxLayer.BackgroundTransparency = 1
fxLayer.Size = UDim2.fromScale(1, 1)
fxLayer.ZIndex = 0                                           -- under the letterbox bars and the overlay
fxLayer.Parent = gui

local function buildFlare(fx)
	local band = Instance.new("Frame")
	band.BorderSizePixel = 0
	band.BackgroundColor3 = Color3.fromRGB(110, 190, 255)
	band.AnchorPoint = Vector2.new(0.5, 0.5)
	band.Position, band.Size = UDim2.fromScale(0.5, 0.5), UDim2.fromScale(1, 0.55)
	local g = Instance.new("UIGradient")
	g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.45, 0.35),
		NumberSequenceKeypoint.new(0.5, 0), NumberSequenceKeypoint.new(0.55, 0.35), NumberSequenceKeypoint.new(1, 1) })
	g.Rotation = 90
	g.Parent = band
	band.Parent = fxLayer
	return { fx = fx, band = band }
end

local function updateFlare(state, tau)
	local u = (tau - state.fx.t) / state.fx.dur
	state.band.Visible = u >= 0 and u <= 1
	state.band.BackgroundTransparency = 1 - math.sin(math.pi * math.clamp(u, 0, 1))
end

-- The barrage's dust: many matte brown clouds around Thanos that grow until they fill the top-down
-- frame, plus a screen-space haze so the whole picture goes brown as in the movie.
local function buildDust(fx)
	local rng = Random.new(31)
	local clouds = {}
	for i = 1, 30 do   -- many faint overlapping clouds read as haze, not as separate bubbles
		clouds[i] = {
			part = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = Color3.fromRGB(88, 74, 60):Lerp(
				Color3.fromRGB(120, 102, 82), rng:NextNumber()), Material = Enum.Material.Sand, Transparency = 1 }),
			offset = Vector3.new(rng:NextNumber(-11, 11), rng:NextNumber(0, 6), rng:NextNumber(-11, 11)),
			size = rng:NextNumber(10, 22), delay = rng:NextNumber(0, 0.7), alpha = rng:NextNumber(0.9, 0.96),
		}
	end
	local haze = Instance.new("Frame")
	haze.BorderSizePixel = 0
	haze.BackgroundColor3 = Color3.fromRGB(70, 58, 46)
	haze.Size = UDim2.fromScale(1, 1)
	haze.Parent = fxLayer
	return { fx = fx, clouds = clouds, haze = haze }
end

local function updateDust(state, tau)
	local fx = state.fx
	local target = findPart(fx.at)
	for _, c in ipairs(state.clouds) do
		local u = (tau - fx.t - c.delay) / 0.9
		local shown = target and u > 0 and tau < fx.t1
		if shown then
			c.part.CFrame = CFrame.new(Vector3.new(target.Position.X, GROUND, target.Position.Z) + c.offset)
			c.part.Size = Vector3.one * c.size * (1 - (1 - math.clamp(u, 0, 1)) ^ 2)   -- fast, then settles
			c.part.Transparency = c.alpha + (1 - c.alpha) * math.clamp((tau - (fx.t1 - 0.6)) / 0.6, 0, 1)
		else
			c.part.Transparency = 1
		end
	end
	local rise = math.clamp((tau - fx.t - 0.3) / 0.8, 0, 1)
	local clear = math.clamp((tau - (fx.t1 - 0.6)) / 0.6, 0, 1)
	state.haze.Visible = rise > 0 and clear < 1
	state.haze.BackgroundTransparency = 1 - 0.35 * rise * (1 - clear)
	-- billowing smoke columns over the blast field (the balls underneath only block the view)
	if not state.billow and target then
		state.billow = {}
		local rng = Random.new(77)
		for i = 1, 4 do
			local a = anchorAt(Vector3.new(target.Position.X + rng:NextNumber(-7, 7), GROUND + 1, target.Position.Z + rng:NextNumber(-7, 7)), 30)
			state.billow[i] = emitter(a, "smokeSoft", { Size = grow(4, 10), Lifetime = NumberRange.new(2.5, 3.5), Speed = NumberRange.new(0.5, 1.5),
				EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(60, 60), Drag = 0.8,
				Transparency = NumberSequence.new({ kp(0, 0.55), kp(0.5, 0.7), kp(1, 1) }),
				Color = ColorSequence.new(Color3.fromRGB(86, 72, 60), Color3.fromRGB(122, 104, 84)), Rate = 1.5 })
		end
	end
	for _, e in ipairs(state.billow or {}) do
		e.Enabled = fxLive and tau >= fx.t + 0.2 and tau < fx.t1 - 0.8
	end
end

local function rgb(v)                                         -- SceneData colours arrive as Vector3 0..255
	return Color3.fromRGB(v.X, v.Y, v.Z)
end

local function along(cf, center, dir)                         -- a Cylinder (axis X) pointing along dir
	return CFrame.lookAt(center, center + dir) * CFrame.Angles(0, math.rad(90), 0)
end

-- Boot / palm thruster: a flickering flame leaving the part along fx.dir (part's own axes).
local function buildThruster(fx)
	local flame = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = Color3.fromRGB(255, 140, 80),
		Material = Enum.Material.Neon, Transparency = 1 })
	local core = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = Color3.fromRGB(255, 225, 190),
		Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range = Color3.fromRGB(255, 150, 90), 6
	light.Parent = core
	-- licking flame particles and a heat-haze of thin smoke streaming out of the nozzle
	local fire = emitter(core, "fireball", { Size = grow(0.55 * fx.size, 0.1), Lifetime = NumberRange.new(0.12, 0.22),
		Speed = NumberRange.new(10, 16), EmissionDirection = Enum.NormalId.Front, SpreadAngle = Vector2.new(8, 8),
		Transparency = FIRE_FADE, Brightness = 2, Color = ColorSequence.new(Color3.fromRGB(255, 240, 210), Color3.fromRGB(255, 120, 50)),
		Rate = 70 })
	local trail = emitter(core, "smokeSoft", { Size = grow(0.3 * fx.size, 1.8 * fx.size), Lifetime = NumberRange.new(0.6, 1),
		Speed = NumberRange.new(4, 7), EmissionDirection = Enum.NormalId.Front, SpreadAngle = Vector2.new(10, 10), Drag = 3,
		Transparency = NumberSequence.new({ kp(0, 0.7), kp(1, 1) }), Color = ColorSequence.new(Color3.fromRGB(170, 160, 150)),
		Rate = 25 })
	return { fx = fx, flame = flame, core = core, light = light, fire = fire, trail = trail }
end

local function updateThruster(state, tau)
	local fx = state.fx
	local part = findPart(fx.part)
	local on = part and tau >= fx.t and tau < fx.t1
	state.flame.Transparency, state.core.Transparency, state.light.Enabled = on and 0 or 1, on and 0 or 1, on
	state.fire.Enabled, state.trail.Enabled = on and fxLive, on and fxLive
	if not on then
		state.flame.CFrame = CFrame.new(0, -500, 0)
		state.core.CFrame = CFrame.new(0, -500, 0)
		return
	end
	local dir = part.CFrame:VectorToWorldSpace(fx.dir)
	local base = part.Position + dir * (part.Size * Vector3.new(math.abs(fx.dir.X), math.abs(fx.dir.Y), math.abs(fx.dir.Z))).Magnitude / 2
	local len = fx.size * (1.3 + 0.35 * math.noise(tau * 18, fx.size * 3, #fx.part))
	state.flame.Size = Vector3.new(len, 0.42 * fx.size, 0.42 * fx.size)
	state.flame.CFrame = along(nil, base + dir * len / 2, dir)
	state.core.Size = Vector3.one * 0.5 * fx.size
	state.core.CFrame = CFrame.lookAt(base, base + dir)                     -- particles leave along its Front
	state.light.Brightness = 4
end

-- The blue device under his feet for the two-footed kick (movie 140-150).
local function buildKickdisc(fx)
	local disc = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = Color3.fromRGB(130, 195, 255),
		Material = Enum.Material.Neon, Transparency = 1 })
	local ring = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = Color3.fromRGB(70, 120, 230),
		Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(120, 180, 255), 10, 3
	light.Parent = disc
	return { fx = fx, disc = disc, ring = ring, light = light }
end

local function updateKickdisc(state, tau)
	local fx = state.fx
	local lf, rf, lt = findPart(fx.rig .. ".LeftFoot"), findPart(fx.rig .. ".RightFoot"), findPart(fx.rig .. ".LowerTorso")
	local on = lf and rf and lt and tau >= fx.t and tau < fx.t1
	state.disc.Transparency, state.ring.Transparency, state.light.Enabled = on and 0.05 or 1, on and 0.5 or 1, on
	if not on then
		return
	end
	local feet = (lf.Position + rf.Position) / 2
	local dir = (feet - lt.Position).Unit
	local g = ease((tau - fx.t) / 0.2)
	local center = feet + dir * 0.35
	state.disc.Size = Vector3.new(0.12, 1.8 * g, 1.8 * g)
	state.ring.Size = Vector3.new(0.08, 2.5 * g, 2.5 * g)
	state.disc.CFrame = along(nil, center, dir)
	state.ring.CFrame = along(nil, center - dir * 0.08, dir)
end

-- A hit: a ball that blooms and fades at a part (+ world offset). light = 0 -> matte dust puff.
local function buildImpact(fx)
	local dust = fx.light == 0
	local ball = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = rgb(fx.color),
		Material = dust and Enum.Material.Sand or Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = rgb(fx.color), fx.size * 2.5, 0
	light.Parent = ball
	addShake(fx.t, dust and 0.08 or 0.32, dust and 9 or 6)
	return { fx = fx, ball = ball, light = light, dust = dust }
end

local function updateImpact(state, tau)
	local fx = state.fx
	local part = findPart(fx.at)
	if part and crossed(state, "hit", fx.t, tau) then
		local pos = part.Position + fx.offset
		if state.dust then
			dustHit(Vector3.new(pos.X, GROUND, pos.Z), fx.size / 2.6)
		else
			energyHit(pos, fx.size / 5, rgb(fx.color))
		end
	end
	-- the ball stays only as a quick hot core under the particles
	fx = { offset = fx.offset, size = fx.size * (state.dust and 0.4 or 0.5), dur = fx.dur * 0.5, light = fx.light, t = fx.t }
	local u = (tau - fx.t) / fx.dur
	if not part or u < 0 or u > 1 then
		state.ball.Transparency, state.light.Brightness = 1, 0
		return
	end
	state.ball.CFrame = CFrame.new(part.Position + fx.offset)
	state.ball.Size = Vector3.one * fx.size * (0.15 + 0.85 * (1 - (1 - u) ^ 2))
	state.ball.Transparency = (state.dust and 0.35 or 0.1) + (state.dust and 0.65 or 0.9) * u
	state.light.Brightness = fx.light * (1 - u)
end

-- Ground anchors: three claws per boot dig into the ground as he lands (movie 160).
local function buildAnchors(fx)
	local claws = {}
	for _, foot in ipairs({ "LeftFoot", "RightFoot" }) do
		for _, yaw in ipairs({ -40, 0, 40 }) do
			table.insert(claws, { foot = foot, yaw = yaw, part = newPart({ Size = Vector3.one,
				Color = Color3.fromRGB(110, 28, 32), Material = Enum.Material.Metal, Transparency = 1 }) })
		end
	end
	return { fx = fx, claws = claws }
end

local function updateAnchors(state, tau)
	local fx = state.fx
	local g = ease((tau - fx.t) / 0.2)
	for _, c in ipairs(state.claws) do
		local foot = findPart(fx.rig .. "." .. c.foot)
		local on = foot and tau >= fx.t and tau < fx.t1
		c.part.Transparency = on and 0 or 1
		if on then
			local len = 0.55 * g
			-- from the heel (foot local +Z) angled back and down into the ground
			local cf = foot.CFrame * CFrame.new(0, -foot.Size.Y / 2, foot.Size.Z / 2) * CFrame.Angles(0, math.rad(c.yaw), 0)
				* CFrame.Angles(math.rad(-40), 0, 0)
			c.part.Size = Vector3.new(0.07, 0.07, math.max(len, 0.01))
			c.part.CFrame = cf * CFrame.new(0, 0, len / 2)
		end
	end
end

-- Nanotech forearm sheath: a dark metal wrap over the forearm and fist, lit by cyan vents (movie 170-185).
-- It hugs the arm (about 1.2x its width), it is not a hammer block.
local function buildCannons(fx)
	local arms = {}
	for _, side in ipairs({ "Left", "Right" }) do
		local arm = {
			side = side,
			block = newPart({ Size = Vector3.new(1.05, 1.7, 1.05), Color = Color3.fromRGB(70, 78, 92), Material = Enum.Material.Metal, Transparency = 1 }),
			face = newPart({ Size = Vector3.new(1.0, 0.08, 1.0), Color = Color3.fromRGB(50, 225, 255), Material = Enum.Material.Neon, Transparency = 1 }),
			ventL = newPart({ Size = Vector3.new(0.06, 1.5, 0.45), Color = Color3.fromRGB(50, 225, 255), Material = Enum.Material.Neon, Transparency = 1 }),
			ventR = newPart({ Size = Vector3.new(0.06, 1.5, 0.45), Color = Color3.fromRGB(50, 225, 255), Material = Enum.Material.Neon, Transparency = 1 }),
			jet = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = Color3.fromRGB(80, 180, 255),
				Material = Enum.Material.Neon, Transparency = 1 }),
			halo = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = Color3.fromRGB(120, 160, 255),
				Material = Enum.Material.Neon, Transparency = 1 }),
		}
		local light = Instance.new("PointLight")
		light.Color, light.Range, light.Brightness = Color3.fromRGB(60, 210, 255), 12, 0
		light.Parent = arm.block
		arm.light = light
		table.insert(arms, arm)
	end
	return { fx = fx, arms = arms }
end

local function updateCannons(state, tau)
	local fx = state.fx
	local g = ease((tau - fx.t) / fx.grow)
	for _, a in ipairs(state.arms) do
		local hand, fore = findPart(fx.rig .. "." .. a.side .. "Hand"), findPart(fx.rig .. "." .. a.side .. "LowerArm")
		local on = hand and fore and tau >= fx.t and tau < fx.t1
		a.block.Transparency = on and 0.55 or 1
		a.face.Transparency = on and 0.05 or 1
		a.ventL.Transparency, a.ventR.Transparency = on and 0.05 or 1, on and 0.05 or 1
		local jetting = on and tau >= fx.jet0 and tau < fx.jet1
		a.jet.Transparency, a.halo.Transparency = jetting and 0.35 or 1, jetting and 0.8 or 1
		a.light.Brightness = on and 5 or 0
		if on then
			local up = fore.CFrame.UpVector
			local rot = fore.CFrame - fore.Position
			local size = Vector3.new(1.05, 1.7, 1.05) * (0.6 + 0.4 * g)
			local center = hand.Position + up * 0.15
			a.block.Size, a.block.CFrame = size, CFrame.new(center) * rot
			a.face.Size = Vector3.new(size.X * 0.35, 0.06, size.Z * 0.35)
			a.face.CFrame = CFrame.new(center - up * (size.Y / 2 + 0.02)) * rot
			a.ventL.Size = Vector3.new(0.06, size.Y * 0.7, size.Z * 0.35)
			a.ventL.CFrame = CFrame.new(center - fore.CFrame.RightVector * (size.X / 2 + 0.02)) * rot
			a.ventR.Size = Vector3.new(0.06, size.Y * 0.7, size.Z * 0.35)
			a.ventR.CFrame = CFrame.new(center + fore.CFrame.RightVector * (size.X / 2 + 0.02)) * rot
			if jetting then
				local len = 1.6 * (0.85 + 0.2 * math.noise(tau * 20, #a.side, 0.3))   -- short thruster flame, not a long tube (movie 28.0-28.2)
				local back = center + up * (size.Y / 2 + len / 2)
				a.jet.Size, a.jet.CFrame = Vector3.new(len, 0.24, 0.24), along(nil, back, up)
				a.halo.Size, a.halo.CFrame = Vector3.new(len * 0.85, 0.42, 0.42), along(nil, back - up * len * 0.1, up)
			end
		end
	end
end

-- Iron Man's helmet (the parts tagged HideInHUD): crushed (sparks) at t0, torn off at t (its
-- pieces fly along `fling`, world studs/s), gone until t1, then nanotech flows back over his face:
-- the pieces reappear in a random order over `grow` s while particles stream in onto his head.
local function helmetParts(rig)
	local list = {}
	local model = workspace:FindFirstChild(rig)
	for _, item in ipairs(model and model:GetDescendants() or {}) do
		if item:GetAttribute("HideInHUD") or item.Name == "Iron Man Helmet" or item.Name == "UpperMask" or item.Name == "LowerMask" or (item:IsA("Model") and item.Name == "Model" and item.Parent == model) then
			for _, p in ipairs(item:IsA("BasePart") and { item, unpack(item:GetDescendants()) } or item:GetDescendants()) do
				if p:IsA("BasePart") then
					table.insert(list, p)
				end
			end
		end
	end
	return list
end

local function buildHelmet(fx)
	local rng = Random.new(51)
	local parts = {}
	for _, p in ipairs(helmetParts(fx.rig)) do
		table.insert(parts, { part = p, at = rng:NextNumber(0, 0.75) })
	end
	local shell = newPart({ Transparency = 1, Size = Vector3.one * 2.6, Shape = Enum.PartType.Ball })
	local stream = emitter(shell, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.18, 0.05),
		Lifetime = NumberRange.new(0.12, 0.16), Speed = NumberRange.new(9, 12), Shape = Enum.ParticleEmitterShape.Sphere,
		ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward, ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface,
		Color = ColorSequence.new(Color3.fromRGB(255, 120, 90), Color3.fromRGB(255, 210, 140)) })
	addShake(fx.t, 0.18, 8)
	return { fx = fx, parts = parts, shell = shell, stream = stream, shown = nil }   -- nil: always write the first frame (a scrub can land anywhere)
end

local function updateHelmet(state, tau)
	local fx = state.fx
	local head = findPart(fx.rig .. ".Head")
	if not head then
		return
	end
	if crossed(state, "crush", fx.t0, tau) then
		energyHit(head.Position + Vector3.new(0, 0.5, 0), 0.4, Color3.fromRGB(255, 200, 150))
	end
	if crossed(state, "rip", fx.t, tau) then
		energyHit(head.Position, 0.5, Color3.fromRGB(255, 190, 140), true)   -- torn metal: sparks, no fireball
		if fxLive then                                               -- the torn-off plates, as physics debris
			local rng = Random.new()
			for i = 1, 12 do
				local src = state.parts[(i - 1) % math.max(#state.parts, 1) + 1]
				local size = rng:NextNumber(0.15, 0.42)
				local c = Instance.new("Part")
				c.Size = Vector3.new(size, size * 0.25, size * rng:NextNumber(0.7, 1.3))
				c.CFrame = head.CFrame * CFrame.new(rng:NextNumber(-0.5, 0.5), rng:NextNumber(-0.3, 0.6), rng:NextNumber(-0.6, 0.4))
					* CFrame.Angles(rng:NextNumber(0, 6), rng:NextNumber(0, 6), 0)
				c.Color = src and src.part.Color or Color3.fromRGB(150, 20, 25)
				c.Material = Enum.Material.Metal
				c.CanQuery, c.CanTouch = false, false
				c.Parent = fxFolder
				c.AssemblyLinearVelocity = fx.fling * rng:NextNumber(0.6, 1.2) + Vector3.new(rng:NextNumber(-4, 4), rng:NextNumber(0, 6), rng:NextNumber(-4, 4))
				c.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-25, 25), rng:NextNumber(-25, 25), rng:NextNumber(-25, 25))
				Debris:AddItem(c, 3)
			end
		end
	end
	-- how much of the helmet shows: all before t, none until t1, then piece by piece
	local progress = tau < fx.t and 1 or math.clamp((tau - fx.t1) / fx.grow, 0, 1)
	local inside = tau >= fx.t and progress < 1
	if inside or state.shown ~= true then
		for _, h in ipairs(state.parts) do
			h.part.LocalTransparencyModifier = progress > h.at and 0 or 1
		end
		state.shown = not inside
	end
	state.shell.CFrame = head.CFrame
	state.stream.Enabled = fxLive and tau >= fx.t1 - 0.04 and tau < fx.t1 + fx.grow
	if crossed(state, "rebuild", fx.t1, tau) then
		state.stream:Emit(45)
	end
end

-- dust kicked up along the ground under a sliding body
local function buildSkid(fx)
	local a = anchorAt(Vector3.zero, 1e6)
	local e = emitter(a, "smokeSoft", { Size = grow(0.8, 4.2), Lifetime = NumberRange.new(1, 1.6), Speed = NumberRange.new(2, 5),
		EmissionDirection = Enum.NormalId.Top, SpreadAngle = Vector2.new(70, 70), Drag = 3, Acceleration = Vector3.new(0, 0.6, 0),
		Transparency = NumberSequence.new({ kp(0, 0.4), kp(0.6, 0.7), kp(1, 1) }),
		Color = ColorSequence.new(Color3.fromRGB(122, 102, 82)), Rate = 70 })
	local grit = emitter(a, nil, { Texture = SPARK, Size = grow(0.12, 0.05), Lifetime = NumberRange.new(0.3, 0.6),
		Speed = NumberRange.new(5, 10), SpreadAngle = Vector2.new(60, 60), Acceleration = Vector3.new(0, -30, 0),
		Color = ColorSequence.new(Color3.fromRGB(90, 74, 60)), LightEmission = 0, Rate = 60 })
	return { fx = fx, at = a, dust = e, grit = grit }
end

local function updateSkid(state, tau)
	local part = findPart(state.fx.part)
	local on = part and tau >= state.fx.t and tau < state.fx.t1
	state.dust.Enabled, state.grit.Enabled = on, on
	if part then
		state.at.WorldPosition = Vector3.new(part.Position.X, GROUND + 0.2, part.Position.Z)
	end
	if on and crossed(state, "puff", state.fx.t, tau) then
		state.dust:Emit(40)
		state.grit:Emit(35)
	end
end

-- a camera jolt with no visible effect (a punch to a bare face)
local function buildShake(fx)
	if fx.t1 then                                             -- a sustained rumble: a train of small jolts
		addShake(fx.t, fx.amp, 7)
		local t = fx.t + fx.every
		while t < fx.t1 do
			addShake(t, fx.each, 12)
			t += fx.every
		end
	else
		addShake(fx.t, fx.amp, 7)
	end
	return { fx = fx }
end

-- a colour wash over the frame (energy light filling a close shot)
local function buildTint(fx)
	local f = Instance.new("Frame")
	f.BorderSizePixel = 0
	f.Size = UDim2.fromScale(1, 1)
	f.BackgroundColor3 = rgb(fx.color)
	f.Visible = false
	f.Parent = fxLayer
	return { fx = fx, frame = f }
end

local function updateTint(state, tau)
	local fx = state.fx
	local on = tau >= fx.t and tau < fx.t1
	state.frame.Visible = on
	if on then
		state.frame.BackgroundTransparency = 1 - fx.alpha * (0.8 + 0.2 * math.noise(tau * 9, 2.2))
	end
end

-- Thanos' purple Power Stone beam. Charge glow at the gauntlet from t0; fires at t, its front runs
-- out to the target's shield by `hit`, then holds (hot core + glow + crackling arcs + lights),
-- a churning energy splash where it strikes, until t1.
local PURPLE, PURPLE_HOT = Color3.fromRGB(170, 70, 255), Color3.fromRGB(240, 210, 255)
local ARCS, ARC_SEGS = 5, 14

local function shieldPoint(rigName)                       -- centre of the shield in front of his left forearm
	local hand = findPart(rigName .. ".LeftHand")
	local chest = findPart(rigName .. ".UpperTorso")
	if not (hand and chest) then
		return nil
	end
	local thanos = findPart("Thanos.UpperTorso")
	local face = thanos and (thanos.Position - chest.Position) or chest.CFrame.LookVector
	face = Vector3.new(face.X, 0, face.Z).Unit
	return hand.Position + face * 1.35 + Vector3.new(0, 0.25, 0), face
end

local function buildBeam(fx)
	local core = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = PURPLE_HOT, Material = Enum.Material.Neon, Transparency = 1 })
	local glow = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = PURPLE, Material = Enum.Material.Neon, Transparency = 1 })
	local haze = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = PURPLE, Material = Enum.Material.ForceField, Transparency = 1 })
	local arcs = {}
	for i = 1, ARCS * ARC_SEGS do
		arcs[i] = newPart({ Size = Vector3.one, Color = Color3.fromRGB(205, 150, 255), Material = Enum.Material.Neon, Transparency = 1 })
	end
	local lights = {}
	for i = 1, 3 do
		local a = anchorAt(Vector3.zero, 1e6)
		local l = Instance.new("PointLight")
		l.Color, l.Range, l.Brightness, l.Shadows = PURPLE, 16, 0, false
		l.Parent = a
		lights[i] = { at = a, light = l }
	end
	local charge = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = PURPLE_HOT, Material = Enum.Material.Neon, Transparency = 1 })
	local chargeLight = Instance.new("PointLight")
	chargeLight.Color, chargeLight.Range, chargeLight.Brightness = Color3.fromRGB(225, 120, 255), 24, 0
	chargeLight.Parent = charge
	local chargeFx = emitter(charge, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.4, 0), Lifetime = NumberRange.new(0.25, 0.45),
		Speed = NumberRange.new(4, 9), SpreadAngle = Vector2.new(180, 180), Color = ColorSequence.new(PURPLE_HOT, PURPLE), Rate = 75 })
	local splashAt = anchorAt(Vector3.zero, 1e6)
	local splashLight = Instance.new("PointLight")
	splashLight.Color, splashLight.Range, splashLight.Brightness = Color3.fromRGB(220, 100, 255), 25, 0
	splashLight.Parent = splashAt
	local splash = {
		-- upper deflected cone of roaring violet plasma washing over top of shield
		emitter(splashAt, "smokeSoft", { Size = grow(1.2, 3.2), Lifetime = NumberRange.new(0.35, 0.65), Speed = NumberRange.new(18, 34),
			SpreadAngle = Vector2.new(45, 60), Brightness = 3, LightEmission = 1, LightInfluence = 0, ZOffset = 1,
			Transparency = NumberSequence.new({ kp(0, 0.1), kp(0.5, 0.4), kp(1, 1) }),
			Color = ColorSequence.new(PURPLE_HOT, PURPLE), Rate = 90 }),
		-- high-speed deflected purple sparks and lightning spray
		emitter(splashAt, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.35, 0), Lifetime = NumberRange.new(0.3, 0.7),
			Speed = NumberRange.new(22, 42), SpreadAngle = Vector2.new(70, 70), Acceleration = Vector3.new(0, -10, 0), Drag = 1.5,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NumberSequence.new(-1.8),
			Color = ColorSequence.new(PURPLE_HOT, PURPLE), Rate = 160 }),
		-- lower deflected cone scouring the ground under shield
		emitter(splashAt, "smokeSoft", { Size = grow(1.0, 2.6), Lifetime = NumberRange.new(0.4, 0.8), Speed = NumberRange.new(12, 24),
			SpreadAngle = Vector2.new(60, 60), Drag = 2, Transparency = NumberSequence.new({ kp(0, 0.3), kp(1, 1) }),
			Color = ColorSequence.new(Color3.fromRGB(160, 80, 240)), LightEmission = 0.6, Rate = 50 }),
	}
	addShake(fx.t, 0.15, 8)
	return { fx = fx, core = core, glow = glow, haze = haze, arcs = arcs, lights = lights, charge = charge, chargeLight = chargeLight, chargeFx = chargeFx,
		splashAt = splashAt, splashLight = splashLight, splash = splash }
end

local function seg(part, a, b, width)
	local mid, len = (a + b) / 2, (b - a).Magnitude
	part.Size = Vector3.new(math.max(len, 0.01), width, width)
	part.CFrame = CFrame.lookAt(mid, b) * CFrame.Angles(0, math.rad(90), 0)
end

local function updateBeam(state, tau)
	local fx = state.fx
	local src = findPart(fx.src)
	local dst = shieldPoint(fx.dst)
	local firing = src and dst and tau >= fx.t and tau < fx.t1
	-- charge: a growing hot ball and intense violet PointLight in the gauntlet
	local charging = src and tau >= fx.t0 and tau < fx.t + 0.1
	state.charge.Transparency = charging and 0.05 or 1
	state.chargeFx.Enabled = charging and fxLive or false
	if state.chargeLight then
		state.chargeLight.Enabled = charging
		state.chargeLight.Brightness = charging and 14 or 0
	end
	if charging then
		local g = ease(math.clamp((tau - fx.t0) / math.max(fx.t - fx.t0, 0.01), 0, 1))
		state.charge.Size = Vector3.one * (0.3 + 1.2 * g)
		state.charge.CFrame = src.CFrame
	end
	for _, p in ipairs({ state.core, state.glow, state.haze }) do
		p.Transparency = 1
	end
	for _, p in ipairs(state.arcs) do
		p.Transparency = 1
	end
	for _, l in ipairs(state.lights) do
		l.light.Brightness = 0
	end
	local struck = firing and tau >= fx.hit
	if state.splashLight then
		state.splashLight.Enabled = struck
		state.splashLight.Brightness = struck and 8 or 0
	end
	for _, e in ipairs(state.splash) do
		e.Enabled = struck and fxLive or false
	end
	if not firing then
		return
	end
	local a = src.Position
	local front = a:Lerp(dst, math.clamp((tau - fx.t) / math.max(fx.hit - fx.t, 0.01), 0, 1) ^ 0.8)
	local flick = 0.85 + 0.15 * math.noise(tau * 30, 4.1)
	-- Massive thick Power Stone beam: white-hot core, blazing violet glow, wide plasma sheath
	seg(state.core, a, front, 0.55 * flick)
	seg(state.glow, a, front, 1.85 * flick)
	seg(state.haze, a, front, 3.20 * flick)
	state.core.Transparency, state.glow.Transparency, state.haze.Transparency = 0, 0.40, 0.70
	-- crackling arcs: jagged polylines around the beam, re-drawn ~20 times a second
	local dir = front - a
	local len = dir.Magnitude
	if len > 0.2 then
		local unit = dir.Unit
		local side = unit:Cross(Vector3.yAxis)
		side = side.Magnitude > 1e-3 and side.Unit or Vector3.xAxis
		local up = side:Cross(unit)
		local tick = math.floor(tau * 20)
		for k = 1, ARCS do
			local rng = Random.new(tick * 31 + k)
			local prev = a
			for i = 1, ARC_SEGS do
				local p = a + unit * (len * i / ARC_SEGS)
				if i < ARC_SEGS then
					local r = rng:NextNumber(0.05, 0.32) * (k == 1 and 0.5 or 1)
					local ang = rng:NextNumber(0, math.pi * 2)
					p += (side * math.cos(ang) + up * math.sin(ang)) * r
				end
				local part = state.arcs[(k - 1) * ARC_SEGS + i]
				seg(part, prev, p, k == 1 and 0.05 or 0.028)
				part.Transparency = k == 1 and 0 or 0.25
				prev = p
			end
		end
	end
	for i, l in ipairs(state.lights) do
		l.at.WorldPosition = a:Lerp(front, (i - 0.5) / #state.lights)
		l.light.Brightness = 1.6 * flick
	end
	if len > 0.2 then
		state.splashAt.WorldCFrame = CFrame.lookAt(dst, dst - dir)   -- splash sprays back toward Thanos
	end
	if crossed(state, "hit", fx.hit, tau) then
		energyHit(dst, 0.9, PURPLE)
		shockwave(Vector3.new(dst.X, GROUND + 0.2, dst.Z), 6, PURPLE, 0.4)
	end
end

-- Iron Man's nanotech shield: a tall kite of plates in front of his left forearm, facing the beam.
-- Plates fly in and lock from the top down between t and t+grow; held until t1.
local SHIELD_ROWS = {
	{ w = 2.4, y = 1.35, th = 0.45 },
	{ w = 2.8, y = 0.75, th = 0.45 },
	{ w = 2.7, y = 0.15, th = 0.45 },
	{ w = 2.3, y = -0.45, th = 0.45 },
	{ w = 1.6, y = -1.05, th = 0.42 },
	{ w = 0.9, y = -1.55, th = 0.38 },
}

local function buildShield(fx)
	local plates = {}
	for r, row in ipairs(SHIELD_ROWS) do
		for c = -1, 1, 2 do
			local isRim = (r == 1 or r == #SHIELD_ROWS or c == 1)
			local col = isRim and Color3.fromRGB(215, 175, 80) or Color3.fromRGB(85, 20, 26)
			table.insert(plates, { part = newPart({ Size = Vector3.new(row.w / 2 + 0.05, 0.62, row.th or 0.45), Color = col,
				Material = Enum.Material.Metal, Reflectance = 0.28, Transparency = 1 }),
				offset = Vector3.new(c * (row.w / 4 + 0.02), row.y, -math.abs(c) * 0.12), order = r, curve = c * 16 })
		end
	end
	local spine = newPart({ Size = Vector3.new(0.35, 3.2, 0.35), Color = Color3.fromRGB(215, 175, 80), Material = Enum.Material.Metal, Transparency = 1 })
	return { fx = fx, plates = plates, spine = spine, maxOrder = #SHIELD_ROWS }
end

local function updateShield(state, tau)
	local fx = state.fx
	local center, face = shieldPoint(fx.rig)
	local on = center and tau >= fx.t and tau < fx.t1
	if not on then
		for _, p in ipairs(state.plates) do
			p.part.Transparency = 1
			p.part.CFrame = CFrame.new(0, -500, 0)
		end
		state.spine.Transparency = 1
		state.spine.CFrame = CFrame.new(0, -500, 0)
		return
	end
	local g = math.clamp((tau - fx.t) / fx.grow, 0, 1)
	-- Sloped backward by 25 degrees, angled proudly toward the incoming beam
	local cf = CFrame.lookAt(center, center + face) * CFrame.Angles(math.rad(25), 0, 0)
	for _, p in ipairs(state.plates) do
		local shown = g * state.maxOrder >= p.order - 1
		p.part.Transparency = shown and 0 or 1
		if shown then
			local settle = math.clamp(g * state.maxOrder - (p.order - 1), 0, 1)
			p.part.CFrame = cf * CFrame.new(p.offset * (0.6 + 0.4 * ease(settle)) - Vector3.new(0, 0, 0.15 * (1 - settle))) * CFrame.Angles(0, math.rad(p.curve or 0), 0)
		else
			p.part.CFrame = CFrame.new(0, -500, 0)
		end
	end
	state.spine.Transparency = g > 0.4 and 0 or 1
	state.spine.CFrame = cf * CFrame.new(0, -0.15, -0.12)
	if center and crossed(state, "form", fx.t, tau) then
		energyHit(center, 0.35, Color3.fromRGB(255, 170, 120), true)
	end
	-- flung away at t1: the plates fly off tumbling as physics debris
	if fx.fling and crossed(state, "fling", fx.t1, tau) and fxLive then
		local c, f = shieldPoint(fx.rig)
		if c then
			local base = CFrame.lookAt(c, c + f)
			local rng = Random.new()
			for _, p in ipairs(state.plates) do
				local q = Instance.new("Part")
				q.Size, q.Color, q.Material = p.part.Size, p.part.Color, p.part.Material
				q.CFrame = base * CFrame.new(p.offset)
				q.CanQuery, q.CanTouch = false, false
				q.Parent = fxFolder
				q.AssemblyLinearVelocity = fx.fling + Vector3.new(rng:NextNumber(-2, 2), rng:NextNumber(-1, 2), rng:NextNumber(-2, 2))
				q.AssemblyAngularVelocity = Vector3.new(rng:NextNumber(-6, 6), rng:NextNumber(-6, 6), rng:NextNumber(-6, 6))
				Debris:AddItem(q, 3)
			end
		end
	end
end

-- The nanotech fist weapon: blocks pile onto the fist (t .. t+grow), blue light lines ignite from
-- `glow`, and at `hit` it smashes into the target part with a blue blast.
local BLUE, BLUE_HOT = Color3.fromRGB(80, 160, 255), Color3.fromRGB(200, 235, 255)
local FIST_BLOCKS = {
	-- Stepped mechanical battering ram hammer assembly
	{ Vector3.new(0, 0.15, 0), Vector3.new(0.95, 0.85, 0.95), Color3.fromRGB(120, 20, 26), Enum.Material.SmoothPlastic }, -- wrist collar
	{ Vector3.new(0, -0.25, 0), Vector3.new(1.35, 1.15, 1.35), Color3.fromRGB(145, 24, 30), Enum.Material.SmoothPlastic }, -- main hammer body
	{ Vector3.new(0, -0.75, 0), Vector3.new(1.45, 0.30, 1.45), Color3.fromRGB(195, 150, 45), Enum.Material.Metal },        -- heavy striking bevel face
	{ Vector3.new(0.48, -0.25, 0), Vector3.new(0.35, 0.95, 1.25), Color3.fromRGB(115, 18, 24), Enum.Material.SmoothPlastic }, -- right flank plate
	{ Vector3.new(-0.48, -0.25, 0), Vector3.new(0.35, 0.95, 1.25), Color3.fromRGB(115, 18, 24), Enum.Material.SmoothPlastic }, -- left flank plate
}

local function buildFistgun(fx)
	local blocks, lines = {}, {}
	for i, b in ipairs(FIST_BLOCKS) do
		blocks[i] = { part = newPart({ Size = b[2], Color = b[3], Material = b[4],
			Reflectance = 0.20, Transparency = 1 }), offset = b[1], at = (i - 1) / #FIST_BLOCKS }
	end
	-- 6 distinct exterior neon cyan energy conduits along armor seams
	for i = 1, 6 do
		lines[i] = newPart({ Size = Vector3.new(1.38, 0.10, 0.10), Color = Color3.fromRGB(0, 220, 255), Material = Enum.Material.Neon, Transparency = 1 })
	end
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness, light.Shadows = Color3.fromRGB(0, 200, 255), 12, 0, false
	light.Parent = blocks[2].part
	addShake(fx.hit, 0.5, 6)
	return { fx = fx, blocks = blocks, lines = lines, light = light }
end

local function updateFistgun(state, tau)
	local fx = state.fx
	local hand = findPart(fx.part)
	local on = hand and tau >= fx.t and tau < fx.t1
	local g = on and math.clamp((tau - fx.t) / fx.grow, 0, 1) or 0
	for _, b in ipairs(state.blocks) do
		local shown = on and g > b.at
		b.part.Transparency = shown and 0 or 1
		if shown then
			local settle = ease(math.clamp((g - b.at) * #state.blocks, 0, 1))
			b.part.CFrame = hand.CFrame * CFrame.new(b.offset * settle + Vector3.new(0, 0.5 * (1 - settle), 0))
		end
	end
	local glow = on and math.clamp((tau - fx.glow) / 0.15, 0, 1) or 0
	for i, l in ipairs(state.lines) do
		l.Transparency = glow > 0 and 0.05 or 1
		if hand then
			-- Wrap along outer circumference of hammer body
			local yOff = -0.15 - (i % 3) * 0.22
			local zOff = (i <= 3) and -0.68 or 0.68
			l.CFrame = hand.CFrame * CFrame.new(0, yOff, zOff)
		end
	end
	state.light.Brightness = 6 * glow
	if crossed(state, "hit", fx.hit, tau) then
		local target = findPart(fx.at)
		local p = target and target.Position or (hand and hand.Position)
		if p then
			energyHit(p, 0.8, BLUE)
			shockwave(p, 4, BLUE, 0.3)
		end
	end
end

-- Stoneblast: Point-blank Power Stone blast to Iron Man's chest (shots 435-440)
local function buildStoneblast(fx)
	local charge = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = PURPLE_HOT, Material = Enum.Material.Neon, Transparency = 1 })
	local chargeLight = Instance.new("PointLight")
	chargeLight.Color, chargeLight.Range, chargeLight.Brightness, chargeLight.Shadows = PURPLE, 10, 0, false
	chargeLight.Parent = charge
	local chargeFx = emitter(charge, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.3, 0), Lifetime = NumberRange.new(0.2, 0.4),
		Speed = NumberRange.new(3, 7), SpreadAngle = Vector2.new(180, 180), Color = ColorSequence.new(PURPLE_HOT, PURPLE), Rate = 60 })

	local blastAt = anchorAt(Vector3.zero, 1e6)
	local haze = emitter(blastAt, "smokeSoft", { Size = grow(1.5, 5.0), Lifetime = NumberRange.new(0.5, 0.9), Speed = NumberRange.new(2, 6),
		SpreadAngle = Vector2.new(180, 180), Drag = 3, Transparency = NumberSequence.new({ kp(0, 0.3), kp(0.7, 0.6), kp(1, 1) }),
		Color = ColorSequence.new(Color3.fromRGB(160, 80, 240)), LightEmission = 0.6, Rate = 0 })

	local trailAt = anchorAt(Vector3.zero, 1e6)
	local trail = emitter(trailAt, "smokeSoft", { Size = grow(1.2, 3.5), Lifetime = NumberRange.new(0.3, 0.6), Speed = NumberRange.new(2, 5),
		SpreadAngle = Vector2.new(60, 60), Drag = 2, Transparency = NumberSequence.new({ kp(0, 0.2), kp(0.6, 0.5), kp(1, 1) }),
		Color = ColorSequence.new(PURPLE_HOT, PURPLE), LightEmission = 1, Rate = 80 })

	addShake(fx.t, 0.85, 6)
	return { fx = fx, charge = charge, chargeLight = chargeLight, chargeFx = chargeFx,
		blastAt = blastAt, haze = haze, trailAt = trailAt, trail = trail }
end

local function updateStoneblast(state, tau)
	local fx = state.fx
	local src = findPart(fx.src)
	local target = findPart(fx.target)
	local charging = src and tau >= fx.t0 and tau < fx.t
	state.charge.Transparency = charging and 0.1 or 1
	state.chargeFx.Enabled = charging and fxLive or false
	state.chargeLight.Brightness = charging and (4 * (tau - fx.t0) / (fx.t - fx.t0) * (0.8 + 0.2 * math.noise(tau * 15, 1))) or 0
	if charging then
		local g = ease((tau - fx.t0) / (fx.t - fx.t0))
		state.charge.Size = Vector3.one * (0.25 + 1.1 * g)
		state.charge.CFrame = src.CFrame
	end

	if crossed(state, "blast", fx.t, tau) then
		local pos = (target and target.Position) or (src and src.Position) or Vector3.zero
		energyHit(pos, 2.2, PURPLE)
		shockwave(pos, 7, PURPLE, 0.35)
		local att = anchorAt(pos, 1.0)
		flashLight(att, Color3.fromRGB(240, 210, 255), 12, 30, 0.25)
		if fxLive then
			state.blastAt.WorldPosition = pos
			state.haze:Emit(35)
		end
	end

	local trailing = target and fxLive and tau >= fx.t and tau < fx.t1
	state.trail.Enabled = trailing
	if target then
		state.trailAt.WorldPosition = target.Position
	end
end

-- Repulsor: Iron Man's repulsor beam firing into Thanos' gauntlet (shots 450-455)
local CYAN_CORE = Color3.fromRGB(240, 255, 255)
local CYAN_GLOW = Color3.fromRGB(90, 205, 255)
local CYAN_HAZE = Color3.fromRGB(255, 215, 90)

local function buildRepulsor(fx)
	local core = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = CYAN_CORE, Material = Enum.Material.Neon, Transparency = 1 })
	local glow = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = CYAN_GLOW, Material = Enum.Material.Neon, Transparency = 1 })
	local haze = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = CYAN_HAZE, Material = Enum.Material.ForceField, Transparency = 1 })

	local muzzle = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one, Color = CYAN_CORE, Material = Enum.Material.Neon, Transparency = 1 })
	local muzzleLight = Instance.new("PointLight")
	muzzleLight.Color, muzzleLight.Range, muzzleLight.Brightness, muzzleLight.Shadows = CYAN_GLOW, 14, 0, false
	muzzleLight.Parent = muzzle
	local muzzleFx = emitter(muzzle, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.25, 0), Lifetime = NumberRange.new(0.15, 0.35),
		Speed = NumberRange.new(4, 9), SpreadAngle = Vector2.new(60, 60), Color = ColorSequence.new(CYAN_CORE, CYAN_GLOW), Rate = 70 })

	local splashAt = anchorAt(Vector3.zero, 1e6)
	local splashLight = Instance.new("PointLight")
	splashLight.Color, splashLight.Range, splashLight.Brightness, splashLight.Shadows = CYAN_GLOW, 18, 0, false
	splashLight.Parent = splashAt
	local splash = {
		emitter(splashAt, "smokeSoft", { Size = grow(0.8, 3.2), Lifetime = NumberRange.new(0.2, 0.4), Speed = NumberRange.new(4, 10),
			SpreadAngle = Vector2.new(80, 80), Brightness = 4, LightEmission = 1, LightInfluence = 0, ZOffset = 1,
			Transparency = NumberSequence.new({ kp(0, 0.1), kp(0.6, 0.4), kp(1, 1) }),
			Color = ColorSequence.new(CYAN_CORE, CYAN_GLOW), Rate = 60 }),
		emitter(splashAt, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.25, 0), Lifetime = NumberRange.new(0.2, 0.5),
			Speed = NumberRange.new(16, 28), SpreadAngle = Vector2.new(85, 85), Acceleration = Vector3.new(0, -14, 0), Drag = 2,
			Orientation = Enum.ParticleOrientation.VelocityParallel, Squash = NumberSequence.new(-1.5),
			Color = ColorSequence.new(CYAN_CORE, Color3.fromRGB(255, 180, 60)), Rate = 140 }),
	}
	addShake(fx.t, 0.40, 7)
	return { fx = fx, core = core, glow = glow, haze = haze, muzzle = muzzle, muzzleLight = muzzleLight, muzzleFx = muzzleFx,
		splashAt = splashAt, splashLight = splashLight, splash = splash }
end

local function updateRepulsor(state, tau)
	local fx = state.fx
	local src = findPart(fx.src)
	local dst = findPart(fx.dst)
	local charging = src and tau >= fx.t0 and tau < fx.t
	state.muzzle.Transparency = charging and 0.15 or 1
	state.muzzleFx.Enabled = charging and fxLive or false
	state.muzzleLight.Brightness = charging and (5 * (tau - fx.t0) / (fx.t - fx.t0)) or 0
	if charging then
		state.muzzle.Size = Vector3.one * (0.2 + 0.6 * ((tau - fx.t0) / (fx.t - fx.t0)))
		state.muzzle.CFrame = src.CFrame
	end

	local firing = src and dst and tau >= fx.t and tau < fx.t1
	local p0 = src and src.Position or Vector3.zero
	local p1 = dst and dst.Position or Vector3.zero

	state.core.Transparency = firing and 0.05 or 1
	state.glow.Transparency = firing and 0.25 or 1
	state.haze.Transparency = firing and 0.55 or 1
	state.muzzleLight.Brightness = firing and 8 or (charging and state.muzzleLight.Brightness or 0)
	state.splashLight.Brightness = firing and 7 or 0

	for _, em in ipairs(state.splash) do
		em.Enabled = firing and fxLive or false
	end

	if firing then
		seg(state.core, p0, p1, 0.35)
		seg(state.glow, p0, p1, 0.95)
		seg(state.haze, p0, p1, 1.6)
		state.splashAt.WorldPosition = p1
		state.muzzle.CFrame = src.CFrame
	end
end

-- Nanotech sword (shots 540-560): grows out of Tony's left forearm, passes to Thanos, breaks, stabs
local SWORD_STEEL = Color3.fromRGB(48, 36, 40)
local SWORD_EDGE = Color3.fromRGB(150, 190, 255)

local function buildSword(fx)
	local blade = newPart({ Size = Vector3.new(0.14, 0.5, 3.2), Color = SWORD_STEEL, Material = Enum.Material.Metal, Transparency = 1 })
	local edge = newPart({ Size = Vector3.new(0.04, 0.12, 3.2), Color = SWORD_EDGE, Material = Enum.Material.Neon, Transparency = 1 })
	local guard = newPart({ Size = Vector3.new(0.9, 0.3, 0.3), Color = SWORD_STEEL, Material = Enum.Material.Metal, Transparency = 1 })
	local grip = newPart({ Size = Vector3.new(0.25, 0.25, 1.0), Color = SWORD_STEEL, Material = Enum.Material.Metal, Transparency = 1 })
	addShake(fx.t0, 0.3, 6)
	return { fx = fx, blade = blade, edge = edge, guard = guard, grip = grip }
end

local function updateSword(state, tau)
	local fx = state.fx
	local hand = findPart(tau >= fx.handoff and fx.hand2 or fx.hand)
	local shown = tau >= fx.t0 and tau < fx.t_end and hand ~= nil
	local bladeOn = shown
	local grown = math.clamp((tau - fx.t0) / (fx.t1 - fx.t0), 0, 1)
	state.grip.Transparency = shown and 0 or 1
	state.guard.Transparency = shown and 0 or 1
	state.blade.Transparency = bladeOn and 0 or 1
	state.edge.Transparency = bladeOn and 0 or 1
	-- once Thanos has the sword (fx.aim), the blade points from his hand at Iron Man's chest (reference 80.5-81.0)
	local target = fx.aim and tau >= fx.aim and findPart(fx.aimAt)
	local base = hand.CFrame
	local reach = nil
	if target then
		local dir = (target.Position - hand.Position).Unit
		base = CFrame.lookAt(hand.Position, hand.Position - dir)   -- local +Z (the blade) points toward Iron Man
		reach = (target.Position - hand.Position).Magnitude - 0.2
	end
	if shown then
		state.grip.CFrame = base
		state.guard.CFrame = base * CFrame.new(0, 0, 0.6)
	end
	if bladeOn then
		-- full blade while it grows; after the break (fx.brk) the blade is a short stump, or reaches Iron Man when aimed
		local len = tau < fx.brk and math.max(3.2 * grown, 0.05) or 1.2
		if reach then
			len = math.max(0.5, reach)
		end
		local center = base * CFrame.new(0, 0, 0.6 + len / 2)
		state.blade.Size = Vector3.new(0.14, 0.5, len)
		state.blade.CFrame = center
		state.edge.Size = Vector3.new(0.04, 0.12, len)
		state.edge.CFrame = center
	end
end

local faceVisibleNow = false   -- the expression plate (0-4.2 s) is drawn; the shading plate yields to it
-- Thanos' form shading: a brow ridge, a nose shadow and cheek hollows drawn on a plate in front of the face, so the
-- blocky head reads as a face with depth (the movie's close-ups). Shown when the lens sees the face from the front.
local shade = nil

local function ensureShade(head)
	if shade and shade.plate.Parent then
		return shade
	end
	local plate = newPart({ Size = Vector3.new(1.3, 1.3, 0.02), Transparency = 1 })
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = 200
	gui.LightInfluence = 1
	gui.Adornee = plate
	gui.Parent = plate
	local function soft(w, h, transparency)
		local f = Instance.new("Frame")
		f.AnchorPoint = Vector2.new(0.5, 0.5)
		f.Size = UDim2.fromOffset(w * 200, h * 200)
		f.BackgroundColor3 = Color3.fromRGB(40, 22, 36)
		f.BackgroundTransparency = transparency
		f.BorderSizePixel = 0
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0.5, 0)
		corner.Parent = f
		f.Parent = gui
		return f
	end
	shade = {
		plate = plate, gui = gui,
		brow = soft(0.95, 0.16, 0.86),
		noseL = soft(0.10, 0.4, 0.9), noseR = soft(0.10, 0.4, 0.9),
		cheekL = soft(0.42, 0.5, 0.92), cheekR = soft(0.42, 0.5, 0.92),
	}
	return shade
end

local function updateShade(tau)
	local head = findPart("Thanos.Head")
	if not head or tau < 0 then
		return
	end
	local S = ensureShade(head)
	local c = head:FindFirstChild("FaceCenterAttachment")
	local f = head:FindFirstChild("FaceFrontAttachment")
	local fwdLocal = (c and f) and (f.Position - c.Position) or Vector3.new(0, 0, -1)
	if fwdLocal.Magnitude < 1e-3 then
		fwdLocal = Vector3.new(0, 0, -1)
	end
	local origin = head.CFrame * (c and c.Position or Vector3.zero)
	local fwd = head.CFrame:VectorToWorldSpace(fwdLocal.Unit)
	local toCam = camera.CFrame.Position - origin
	local facing = toCam.Magnitude > 0 and fwd:Dot(toCam.Unit) > 0.85
	S.gui.Enabled = facing and not faceVisibleNow
	if not S.gui.Enabled then
		return
	end
	S.plate.CFrame = CFrame.lookAt(origin + fwd * 0.92, origin + fwd * 2.0, head.CFrame.UpVector)
	local function at(frame, x, y)
		frame.Position = UDim2.fromOffset((x + 0.65) * 200, (0.65 - y) * 200)
	end
	at(S.brow, 0, 0.36)
	at(S.noseL, -0.06, 0.02)
	at(S.noseR, 0.06, 0.02)
	at(S.cheekL, -0.36, -0.22)
	at(S.cheekR, 0.36, -0.22)
end

-- Thanos' face: brows, eyelids and mouth drawn on a transparent plate just in front of the face (a SurfaceGui),
-- so they lie flat on the face from the front and vanish edge-on from the side. Driven by the "face" keys in
-- scene.py (brow: + raise, - glare; lid: 1 open, 0 shut; mouth: - pressed). Hidden when no key is active.
local BROW_COLOR = Color3.fromRGB(45, 32, 36)
local FACE_PPS, FACE_W, FACE_H = 200, 1.3, 1.3
local face = nil

local function faceKeys()
	local keys = {}
	for _, fx in ipairs(Scene.fx or {}) do
		if fx.kind == "face" then
			table.insert(keys, fx)
		end
	end
	table.sort(keys, function(a, b) return a.t < b.t end)
	return keys
end

-- brow, lid and mouth at tau, or nil when the expression is off
local function faceAt(keys, tau)
	local first, last = keys[1], keys[#keys]
	if not first or tau < first.t or (last.off and tau >= last.t) then
		return nil
	end
	local a, b = keys[1], keys[2] or keys[1]
	for i = 1, #keys - 1 do
		if tau >= keys[i].t then
			a, b = keys[i], keys[i + 1]
		end
	end
	local span = b.t - a.t
	local u = span > 0 and math.clamp((tau - a.t) / span, 0, 1) or 0
	local ma, mb = a.mouth or 0, b.mouth or 0
	return a.brow + (b.brow - a.brow) * u, a.lid + (b.lid - a.lid) * u, ma + (mb - ma) * u
end

local function ensureFace(head)
	if face and face.plate.Parent then
		return face
	end
	local plate = newPart({ Size = Vector3.new(FACE_W, FACE_H, 0.02), Transparency = 1 })
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = FACE_PPS
	gui.LightInfluence = 1
	gui.Adornee = plate
	gui.Parent = plate
	local function bar(w, h, color)
		local f = Instance.new("Frame")
		f.AnchorPoint = Vector2.new(0.5, 0.5)
		f.Size = UDim2.fromOffset(w * FACE_PPS, h * FACE_PPS)
		f.BackgroundColor3 = color
		f.BorderSizePixel = 0
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0.5, 0)
		corner.Parent = f
		f.Parent = gui
		return f
	end
	face = {
		plate = plate, gui = gui,
		browL = bar(0.36, 0.07, BROW_COLOR), browR = bar(0.36, 0.07, BROW_COLOR),
		lidL = bar(0.28, 0.14, head.Color), lidR = bar(0.28, 0.14, head.Color),
		mouth = bar(0.46, 0.035, Color3.fromRGB(60, 36, 40)),
	}
	return face
end

-- x right, y up, in studs from the face centre
local function placeOnFace(f, x, y)
	f.Position = UDim2.fromOffset((x + FACE_W / 2) * FACE_PPS, (FACE_H / 2 - y) * FACE_PPS)
end

local function updateFace(tau)
	local head = findPart("Thanos.Head")
	local brow, lid, mouth = faceAt(faceKeys(), tau)
	if not head or not brow then
		if face then
			face.gui.Enabled = false
		end
		faceVisibleNow = false
		return
	end
	local F = ensureFace(head)
	F.gui.Enabled = true
	faceVisibleNow = true
	-- the face frame from the head's attachments: forward points out of the face, up follows the head's tilt
	local c = head:FindFirstChild("FaceCenterAttachment")
	local f = head:FindFirstChild("FaceFrontAttachment")
	local fwdLocal = (c and f) and (f.Position - c.Position) or Vector3.new(0, 0, -1)
	if fwdLocal.Magnitude < 1e-3 then
		fwdLocal = Vector3.new(0, 0, -1)
	end
	local origin = head.CFrame * (c and c.Position or Vector3.zero)
	local fwd = head.CFrame:VectorToWorldSpace(fwdLocal.Unit)
	local up = head.CFrame.UpVector
	F.plate.CFrame = CFrame.lookAt(origin + fwd * 0.92, origin + fwd * 2.0, up)
	-- The owner's Thanos model features custom textured face decals, so we keep the 2D GUI plate off
	F.gui.Enabled = false
	-- brows sit 0.12 studs over the eyes; a glare drops the inner ends
	placeOnFace(F.browL, -0.17, 0.47 + brow * 0.08)
	placeOnFace(F.browR, 0.17, 0.47 + brow * 0.08)
	F.browL.Rotation = -brow * 18
	F.browR.Rotation = brow * 18
	-- eyelids come down from the top of each eye; hidden when fully open
	local h = 0.14 * (1 - lid)
	for _, pair in ipairs({ { F.lidL, -0.16 }, { F.lidR, 0.16 } }) do
		local lidFrame, x = pair[1], pair[2]
		lidFrame.Visible = h > 0.01
		lidFrame.BackgroundColor3 = head.Color
		lidFrame.Size = UDim2.fromOffset(0.28 * FACE_PPS, math.max(h, 0.005) * FACE_PPS)
		placeOnFace(lidFrame, x, 0.42 - h / 2)
	end
	-- mouth: pressed lips are narrower and a little thicker
	F.mouth.Size = UDim2.fromOffset(0.46 * (1 + 0.15 * mouth) * FACE_PPS, (0.035 - 0.012 * mouth) * FACE_PPS)
	placeOnFace(F.mouth, 0, -0.26)
end

-- The film look for the whole scene, measured against the reference (frames 0-5.9 s): the Roblox render was ~35%
-- darker, much more saturated, with crushed blacks and pink skin. Applied when the scene starts, restored after.
-- ambient air: faint dust motes drifting in the backlight, around the camera. Scene-wide, like the movie's dust layer.
local airDust = nil

local function setAirDust(on)
	if not on then
		if airDust then
			airDust.part:Destroy()
			airDust = nil
		end
		return
	end
	if airDust then
		return
	end
	local part = anchorAt(Vector3.zero, 1e6)
	local mote = emitter(part, nil, { Texture = SPARK, LightEmission = 0, LightInfluence = 1,
		Size = NumberSequence.new(0.14), Lifetime = NumberRange.new(4, 6), Rate = 14,
		Speed = NumberRange.new(0.2, 0.6), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.05, 0),
		Color = ColorSequence.new(Color3.fromRGB(200, 170, 130), Color3.fromRGB(120, 100, 80)),
		Transparency = NumberSequence.new({ kp(0, 0.6), kp(0.5, 0.75), kp(1, 1) }) })
	airDust = { part = part, mote = mote }
end

local function updateAirDust(cf)
	if airDust then
		airDust.part.WorldPosition = cf.Position + cf.LookVector * 9
		airDust.mote.Enabled = fxLive
	end
end

local SKIN_FROM, SKIN_TO = Color3.fromRGB(167, 94, 155), Color3.fromRGB(118, 84, 112)
local lookSaved = nil
local sunTable, sunShot = nil, nil

local function applyLook(on)
	local L = game:GetService("Lighting")
	local grade = L:FindFirstChild("TitanGrade")
	if on and not lookSaved then
		lookSaved = { exposure = L.ExposureCompensation, ambient = L.Ambient, outdoor = L.OutdoorAmbient,
			diffuse = L.EnvironmentDiffuseScale, lat = L.GeographicLatitude, clock = L.ClockTime, skin = {} }
		if grade then
			lookSaved.grade = { grade.Brightness, grade.Contrast, grade.Saturation }
			grade.Brightness, grade.Contrast, grade.Saturation = 0.0, 0.06, -0.70
		end
		L.ExposureCompensation = -1.0   -- the sun in front of the lens lights the haze (measured: +0.15 -> L 46.7, -1.5 -> 18.6; movie 25.3)
		L.Ambient = Color3.fromRGB(77, 64, 54)
		-- backlit look: less light from the open sky on the camera side, so faces sit darker and the rims read
		L.OutdoorAmbient = Color3.fromRGB(128, 108, 90)
		L.EnvironmentDiffuseScale = 0.45
		setAirDust(true)
		local th = workspace:FindFirstChild("Thanos")
		-- the gauntlet reads pale yellow-gold; the reference is a dark, worn bronze. Darken its light gold parts.
		local gauntlet = th and th:FindFirstChild("Gauntlet")
		for _, p in ipairs(gauntlet and gauntlet:GetDescendants() or {}) do
			if p:IsA("BasePart") and p.Material ~= Enum.Material.Neon then
				local h, s, v = p.Color:ToHSV()
				if h > 0.06 and h < 0.17 and v > 0.45 then
					lookSaved.skin[p] = p.Color
					p.Color = Color3.fromHSV(h, math.min(s * 1.15, 1), v * 0.62)
				end
			end
		end
		-- the suits: lift Thanos' near-black fabric (p5 3.3 vs movie 9.0), and darken Iron Man's bright gold plates
		for _, name in ipairs({ "Thanos", "IronMan" }) do
			local rig = workspace:FindFirstChild(name)
			for _, p in ipairs(rig and rig:GetDescendants() or {}) do
				if p:IsA("BasePart") and p.Material ~= Enum.Material.Neon and p.Parent.Name ~= "Gauntlet" then
					local h, s, v = p.Color:ToHSV()
					if name == "IronMan" and h > 0.06 and h < 0.17 and v > 0.45 then
						lookSaved.skin[p] = p.Color
						p.Color = Color3.fromHSV(h, math.min(s * 1.1, 1), v * 0.7)
					elseif name == "Thanos" and v < 0.12 and p.Name ~= "Head" then
						lookSaved.skin[p] = p.Color
						p.Color = p.Color:Lerp(Color3.fromRGB(44, 40, 52), 0.5)
					end
				end
			end
		end
		for _, p in ipairs(th and th:GetChildren() or {}) do
			if p:IsA("BasePart") then
				local c = p.Color
				local dist = math.abs(c.R - SKIN_FROM.R) + math.abs(c.G - SKIN_FROM.G) + math.abs(c.B - SKIN_FROM.B)
				if dist < 0.06 then
					lookSaved.skin[p] = c
					p.Color = SKIN_TO
				end
			end
		end
	elseif not on and lookSaved then
		L.ExposureCompensation, L.Ambient = lookSaved.exposure, lookSaved.ambient
		L.OutdoorAmbient, L.EnvironmentDiffuseScale = lookSaved.outdoor, lookSaved.diffuse
		L.GeographicLatitude, L.ClockTime = lookSaved.lat, lookSaved.clock
		setAirDust(false)
		sunShot = nil
		if grade and lookSaved.grade then
			grade.Brightness, grade.Contrast, grade.Saturation = table.unpack(lookSaved.grade)
		end
		for p, c in pairs(lookSaved.skin) do
			p.Color = c
		end
		lookSaved = nil
	end
end

-- backlight cheat: at each shot the sun is moved in front of the lens (low, a little to one side), so whoever is in
-- frame is backlit like the reference. Sun directions for (latitude, clock) are tabulated once; restored on stop.

local function buildSunTable(L)
	sunTable = {}
	local lat0, ct0 = L.GeographicLatitude, L.ClockTime
	for lat = -80, 80, 5 do
		for ct = 5.5, 18.5, 0.25 do
			L.GeographicLatitude, L.ClockTime = lat, ct
			local dir = L:GetSunDirection()
			if dir.Y > 0.12 and dir.Y < 0.45 then
				table.insert(sunTable, { lat = lat, ct = ct, dir = dir })
			end
		end
	end
	L.GeographicLatitude, L.ClockTime = lat0, ct0
end

local function updateSun(shot, cf)
	if not lookSaved or sunShot == shot then
		return
	end
	sunShot = shot
	local L = game:GetService("Lighting")
	if not sunTable then
		buildSunTable(L)
	end
	local look = Vector3.new(cf.LookVector.X, 0, cf.LookVector.Z)
	look = look.Magnitude > 1e-3 and look.Unit or Vector3.zAxis
	local side = look:Cross(Vector3.yAxis)
	local want = (look * 0.9 + side * 0.35 + Vector3.new(0, 0.3, 0)).Unit
	local best, score = nil, -2
	for _, s in ipairs(sunTable) do
		local v = s.dir:Dot(want)
		if v > score then
			best, score = s, v
		end
	end
	if best then
		L.GeographicLatitude, L.ClockTime = best.lat, best.ct
	end
end

-- focus: the lens focuses on whatever the camera looks at; close shots blur the background like the reference
local focusParams = RaycastParams.new()
focusParams.FilterType = Enum.RaycastFilterType.Exclude

local function updateFocus(cf, fov, hud)
	local dof = game:GetService("Lighting"):FindFirstChildOfClass("DepthOfFieldEffect")
	if dof then
		-- no lens blur: the owner reads it as a defect on faces (dialogue close-ups and the mask). Kept off everywhere.
		dof.Enabled = false
	end
end

-- Nanotech armor regeneration shimmer (shot 460)
local function buildNanotech(fx)
	local att = anchorAt(Vector3.zero, 1e6)
	local glowLight = Instance.new("PointLight")
	glowLight.Color, glowLight.Range, glowLight.Brightness, glowLight.Shadows = Color3.fromRGB(120, 220, 255), 6, 0, false
	glowLight.Parent = att
	local shimmer = emitter(att, nil, { Texture = SPARK, LightEmission = 1, Size = grow(0.18, 0), Lifetime = NumberRange.new(0.2, 0.45),
		Speed = NumberRange.new(1.0, 3.5), SpreadAngle = Vector2.new(180, 180), Drag = 2,
		Color = ColorSequence.new({ ckp(0, Color3.fromRGB(255, 215, 100)), ckp(0.5, Color3.fromRGB(100, 220, 255)), ckp(1, Color3.fromRGB(255, 60, 60)) }), Rate = 45 })
	return { fx = fx, att = att, glowLight = glowLight, shimmer = shimmer }
end

local function updateNanotech(state, tau)
	local fx = state.fx
	local part = findPart(fx.part)
	local active = part and tau >= fx.t0 and tau < fx.t1
	state.shimmer.Enabled = active and fxLive or false
	state.glowLight.Brightness = active and (2.5 * (0.8 + 0.2 * math.sin(tau * 12))) or 0
	if part then
		state.att.WorldPosition = part.Position
	end
end

-- Dual fire-laser streams (shots 465-480)
local FIRE_CORE = Color3.fromRGB(255, 252, 220)
local FIRE_ORANGE = Color3.fromRGB(255, 215, 70)   -- yellow, as the reference shows (was orange)
local FIRE_HAZE = Color3.fromRGB(220, 50, 10)

local function buildFirelaser(fx)
	local function makeBeam()
		local c = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = FIRE_CORE, Material = Enum.Material.Neon, Transparency = 1 })
		local g = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = FIRE_ORANGE, Material = Enum.Material.Neon, Transparency = 1 })
		local h = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.one, Color = FIRE_HAZE, Material = Enum.Material.Neon, Transparency = 1 })
		return c, g, h
	end
	local c1, g1, h1 = makeBeam()
	local c2, g2, h2 = makeBeam()

	local m1 = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 0.4, Color = FIRE_CORE, Material = Enum.Material.Neon, Transparency = 1 })
	local ml1 = Instance.new("PointLight")
	ml1.Color, ml1.Range, ml1.Brightness, ml1.Shadows = FIRE_ORANGE, 16, 0, false
	ml1.Parent = m1

	local m2 = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 0.4, Color = FIRE_CORE, Material = Enum.Material.Neon, Transparency = 1 })
	local ml2 = Instance.new("PointLight")
	ml2.Color, ml2.Range, ml2.Brightness, ml2.Shadows = FIRE_ORANGE, 16, 0, false
	ml2.Parent = m2

	local splashAt = anchorAt(Vector3.zero, 1e6)
	local splashLight = Instance.new("PointLight")
	splashLight.Color, splashLight.Range, splashLight.Brightness, splashLight.Shadows = FIRE_ORANGE, 24, 0, false
	splashLight.Parent = splashAt

	local splash = {
		emitter(splashAt, "sparks", { Size = grow(0.35, 0.05), Lifetime = NumberRange.new(0.25, 0.6),
			Speed = NumberRange.new(18, 38), SpreadAngle = Vector2.new(90, 90), Acceleration = Vector3.new(0, -18, 0),
			Color = ColorSequence.new(FIRE_CORE, FIRE_ORANGE), Rate = 220 }),
		emitter(splashAt, "smoke", { Size = grow(1.5, 4.0), Lifetime = NumberRange.new(0.6, 1.2),
			Speed = NumberRange.new(4, 12), SpreadAngle = Vector2.new(60, 60), Transparency = SMOKE_FADE,
			Color = ColorSequence.new(Color3.fromRGB(80, 50, 40), Color3.fromRGB(40, 30, 30)), Rate = 50 }),
	}
	for t = fx.t, fx.t1, 0.12 do
		addShake(t, 0.35, 8)
	end
	return { fx = fx, c1 = c1, g1 = g1, h1 = h1, c2 = c2, g2 = g2, h2 = h2,
		m1 = m1, ml1 = ml1, m2 = m2, ml2 = ml2, splashAt = splashAt, splashLight = splashLight, splash = splash }
end

local function updateFirelaser(state, tau)
	local fx = state.fx
	local firing = tau >= fx.t and tau < fx.t1
	local src1 = findPart(fx.src1 or "IronMan.RightHand")
	local src2 = findPart(fx.src2 or "IronMan.LeftHand")
	local dst = findPart(fx.dst or "Thanos.UpperTorso")
	local p_dst = dst and dst.Position or Vector3.zero

	state.c1.Transparency = firing and 0.05 or 1
	state.g1.Transparency = firing and 0.25 or 1
	state.h1.Transparency = firing and 0.55 or 1
	state.c2.Transparency = firing and 0.05 or 1
	state.g2.Transparency = firing and 0.25 or 1
	state.h2.Transparency = firing and 0.55 or 1

	state.ml1.Brightness = firing and 8 or 0
	state.ml2.Brightness = firing and 8 or 0
	state.splashLight.Brightness = firing and 9 or 0

	for _, em in ipairs(state.splash) do
		em.Enabled = firing and fxLive or false
	end

	if firing then
		if src1 then
			local p1 = src1.Position
			seg(state.c1, p1, p_dst, 0.38)
			seg(state.g1, p1, p_dst, 1.05)
			seg(state.h1, p1, p_dst, 1.8)
			state.m1.CFrame = src1.CFrame
		end
		if src2 then
			local p2 = src2.Position
			seg(state.c2, p2, p_dst, 0.38)
			seg(state.g2, p2, p_dst, 1.05)
			seg(state.h2, p2, p_dst, 1.8)
			state.m2.CFrame = src2.CFrame
		end
		state.splashAt.WorldPosition = p_dst
	end
end


-- ------------------------------------------------------------------ Chunk 2 FX Handlers
-- Shot 130: Massive multi-stud orange-yellow explosion fireball engulfing Thanos on left-center
local function buildFireball(fx)
	local core = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * (fx.size or 18), Color = Color3.fromRGB(255, 150, 30),
		Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(255, 140, 30), 45, 0
	light.Parent = core
	local flame = emitter(core, "fireball", { Size = grow(4, 20), Lifetime = NumberRange.new(0.8, 1.6),
		Speed = NumberRange.new(8, 24), SpreadAngle = Vector2.new(180, 180),
		Color = ColorSequence.new(Color3.fromRGB(255, 240, 140), Color3.fromRGB(255, 80, 20)), Rate = 180 })
	local smoke = emitter(core, "smokeSoft", { Size = grow(6, 28), Lifetime = NumberRange.new(2.5, 4.5),
		Speed = NumberRange.new(4, 15), SpreadAngle = Vector2.new(180, 180), Drag = 1.5,
		Color = ColorSequence.new(Color3.fromRGB(45, 40, 36), Color3.fromRGB(20, 18, 16)), Rate = 100 })
	return { fx = fx, core = core, light = light, flame = flame, smoke = smoke }
end

local function updateFireball(state, tau)
	local fx = state.fx
	local target = findPart(fx.at)
	local on = target and tau >= fx.t and tau < fx.t1
	local e = tau - fx.t
	state.core.Transparency = on and math.clamp(0.05 + e * 0.35, 0, 1) or 1
	state.light.Brightness = on and math.max(0, 14 * (1 - e / (fx.t1 - fx.t))) or 0
	state.flame.Enabled = on and (e < 1.4)
	state.smoke.Enabled = on
	if on and target then
		state.core.CFrame = target.CFrame * CFrame.new(0, 1.5, 0)
	end
end

-- Shot 115: Bright firing launch glow around Iron Man at bottom-center
local function buildLaunchflash(fx)
	local flash = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 4, Color = Color3.fromRGB(255, 185, 60),
		Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(255, 175, 50), fx.size or 26, 0
	light.Parent = flash
	local smoke = emitter(flash, "smokeSoft", { Size = grow(1.2, 6), Lifetime = NumberRange.new(1.2, 2.2),
		Speed = NumberRange.new(3, 8), SpreadAngle = Vector2.new(60, 60),
		Color = ColorSequence.new(Color3.fromRGB(220, 210, 200)), Rate = 60 })
	return { fx = fx, flash = flash, light = light, smoke = smoke }
end

local function updateLaunchflash(state, tau)
	local fx = state.fx
	local rig = workspace:FindFirstChild(fx.rig)
	local root = rig and rig:FindFirstChild("HumanoidRootPart")
	local on = root and tau >= fx.t and tau < fx.t1
	state.flash.Transparency = on and 0.2 or 1
	state.light.Brightness = on and 9 or 0
	state.smoke.Enabled = on
	if on and root then
		state.flash.CFrame = root.CFrame * CFrame.new(0, -1, 0)
	end
end

-- Shot 150: Cyan back-thruster glow on UpperTorso during somersault flip
local function buildBackthruster(fx)
	local ventL = newPart({ Size = Vector3.new(0.35, 0.35, 0.5), Color = Color3.fromRGB(50, 220, 255), Material = Enum.Material.Neon, Transparency = 1 })
	local ventR = newPart({ Size = Vector3.new(0.35, 0.35, 0.5), Color = Color3.fromRGB(50, 220, 255), Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(60, 210, 255), 15, 0
	light.Parent = ventL
	return { fx = fx, ventL = ventL, ventR = ventR, light = light }
end

local function updateBackthruster(state, tau)
	local fx = state.fx
	local torso = findPart(fx.rig .. ".UpperTorso")
	local on = torso and tau >= fx.t and tau < fx.t1
	state.ventL.Transparency, state.ventR.Transparency = on and 0.1 or 1, on and 0.1 or 1
	state.light.Brightness = on and 7 or 0
	if on and torso then
		state.ventL.CFrame = torso.CFrame * CFrame.new(-0.55, 0.4, 0.6)
		state.ventR.CFrame = torso.CFrame * CFrame.new(0.55, 0.4, 0.6)
	end
end

-- Shot 180: Radial blue-white impact bloom & horizontal blue thruster jet beams streaming from Iron Man's back
local function buildRamimpact(fx)
	local bloom = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * (fx.size or 14), Color = Color3.fromRGB(205, 235, 255),
		Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(190, 225, 255), 30, 0
	light.Parent = bloom
	local beamL = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.new(2.2, 0.26, 0.26), Color = Color3.fromRGB(70, 180, 255), Material = Enum.Material.Neon, Transparency = 1 })
	local beamR = newPart({ Shape = Enum.PartType.Cylinder, Size = Vector3.new(2.2, 0.26, 0.26), Color = Color3.fromRGB(70, 180, 255), Material = Enum.Material.Neon, Transparency = 1 })
	local sparks = emitter(bloom, "smokeSoft", { Size = grow(0.5, 4.0), Lifetime = NumberRange.new(0.3, 0.6),
		Speed = NumberRange.new(14, 32), SpreadAngle = Vector2.new(180, 180),
		Color = ColorSequence.new(Color3.fromRGB(220, 240, 255), Color3.fromRGB(110, 180, 255)), Rate = 160 })
	addShake(fx.t, 0.48, 8)
	return { fx = fx, bloom = bloom, light = light, beamL = beamL, beamR = beamR, sparks = sparks }
end

local function updateRamimpact(state, tau)
	local fx = state.fx
	local target, torso = findPart(fx.at), findPart("IronMan.UpperTorso")
	local on = target and tau >= fx.t and tau < fx.t + (fx.dur or 0.45)
	local e = tau - fx.t
	state.bloom.Transparency = on and math.clamp(e / (fx.dur or 0.45), 0, 1) or 1
	state.light.Brightness = on and math.max(0, (fx.light or 14) * (1 - e / (fx.dur or 0.45))) or 0
	state.sparks.Enabled = on and (e < 0.22)
	state.beamL.Transparency, state.beamR.Transparency = on and 0.15 or 1, on and 0.15 or 1
	if on and target and torso then
		local hitPos = target.Position + (fx.offset and target.CFrame:VectorToWorldSpace(fx.offset) or Vector3.zero)
		state.bloom.CFrame = CFrame.new(hitPos)
		local backDir = -torso.CFrame.LookVector
		state.beamL.CFrame = CFrame.lookAt(torso.Position + torso.CFrame.RightVector * -0.65 + backDir * 1.4, torso.Position + torso.CFrame.RightVector * -0.65 + backDir * 3.2)
		state.beamR.CFrame = CFrame.lookAt(torso.Position + torso.CFrame.RightVector * 0.65 + backDir * 1.4, torso.Position + torso.CFrame.RightVector * 0.65 + backDir * 3.2)
	end
end

-- Shot 185: Thruster clash sparks between fighters grappling
local function buildClashsparks(fx)
	local core = newPart({ Shape = Enum.PartType.Ball, Size = Vector3.one * 0.6, Color = Color3.fromRGB(255, 215, 130), Material = Enum.Material.Neon, Transparency = 1 })
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(255, 190, 80), 14, 0
	light.Parent = core
	local sparks = emitter(core, "smokeSoft", { Size = grow(0.2, 1.4), Lifetime = NumberRange.new(0.2, 0.45),
		Speed = NumberRange.new(12, 26), SpreadAngle = Vector2.new(180, 180),
		Color = ColorSequence.new(Color3.fromRGB(255, 235, 170), Color3.fromRGB(255, 110, 30)), Rate = 110 })
	return { fx = fx, core = core, light = light, sparks = sparks }
end

local function updateClashsparks(state, tau)
	local fx = state.fx
	local im, th = findPart("IronMan.UpperTorso"), findPart("Thanos.UpperTorso")
	local on = im and th and tau >= fx.t and tau < fx.t1
	state.core.Transparency = on and 0.25 or 1
	state.light.Brightness = on and 5 or 0
	state.sparks.Enabled = on
	if on and im and th then
		state.core.CFrame = CFrame.new((im.Position + th.Position) / 2 + Vector3.new(0, 0.4, 0))
	end
end

local FX_KINDS = {
	firelaser = { build = buildFirelaser, update = updateFirelaser },
	sword = { build = buildSword, update = updateSword },
	repulsor = { build = buildRepulsor, update = updateRepulsor },
	nanotech = { build = buildNanotech, update = updateNanotech },
	stoneblast = { build = buildStoneblast, update = updateStoneblast },
	helmet = { build = buildHelmet, update = updateHelmet },
	skid = { build = buildSkid, update = updateSkid },
	shake = { build = buildShake, update = function() end },
	tint = { build = buildTint, update = updateTint },
	beam = { build = buildBeam, update = updateBeam },
	shield = { build = buildShield, update = updateShield },
	fistgun = { build = buildFistgun, update = updateFistgun },
	mark = { build = function(fx)
		-- a flat wet mark (blood) stuck to a body part; offset/size are fractions of the part's size
		return { fx = fx, part = newPart({ Size = Vector3.one * 0.05, Color = rgb(fx.color), Material = Enum.Material.Glass,
			Reflectance = 0.25, Transparency = 1 }) }
	end, update = function(state, tau)
		local fx = state.fx
		local host = findPart(fx.part)
		local g = host and math.clamp((tau - fx.t) / fx.grow, 0, 1) or 0
		state.part.Transparency = g > 0 and 0.05 or 1
		if g > 0 then
			local hs = host.Size
			state.part.Size = Vector3.new(fx.size.X * hs.X, fx.size.Y * hs.Y * (0.3 + 0.7 * g), math.max(fx.size.Z * hs.Z, 0.02))
			state.part.CFrame = host.CFrame * CFrame.new(fx.offset * hs - Vector3.new(0, (1 - g) * 0.35 * fx.size.Y * hs.Y, 0))
		end
	end },
	nanoshot = { build = buildNanoshot, update = updateNanoshot },
	thruster = { build = buildThruster, update = updateThruster },
	kickdisc = { build = buildKickdisc, update = updateKickdisc },
	impact = { build = buildImpact, update = updateImpact },
	anchors = { build = buildAnchors, update = updateAnchors },
	cannons = { build = buildCannons, update = updateCannons },
	pods = { build = buildPods, update = updatePods },
	missiles = { build = buildMissiles, update = updateMissiles },
	blast = { build = buildBlast, update = updateBlast },
	wall = { build = buildWall, update = updateWall },
	smokecloud = { build = buildSmokecloud, update = updateSmokecloud },
	flare = { build = buildFlare, update = updateFlare },
	dust = { build = buildDust, update = updateDust },
	fireball = { build = buildFireball, update = updateFireball },
	launchflash = { build = buildLaunchflash, update = updateLaunchflash },
	backthruster = { build = buildBackthruster, update = updateBackthruster },
	ramimpact = { build = buildRamimpact, update = updateRamimpact },
	clashsparks = { build = buildClashsparks, update = updateClashsparks },
}
local activeFx = {}

local function startFx()
	if fxFolder then
		fxFolder:Destroy()
	end
	fxLayer:ClearAllChildren()
	fxFolder = Instance.new("Folder")
	fxFolder.Name = "SceneFX"
	fxFolder.Parent = workspace
	activeFx = {}
	table.clear(shakes)
	for _, fx in ipairs(Scene.fx or {}) do
		local kind = FX_KINDS[fx.kind]
		if kind then
			table.insert(activeFx, { kind = kind, state = kind.build(fx) })
		end
	end
end

local function stopFx()
	if fxFolder then
		fxFolder:Destroy()
		fxFolder = nil
	end
	fxLayer:ClearAllChildren()
	activeFx = {}
end

-- ------------------------------------------------------------------ helmet HUD
-- Inside-the-mask look for shots with hud = "mask" / "lock": near-black vignette around the
-- face, cyan holographic glow at the edges, glass streaks, small readouts, cool dim grade.
-- "lock" adds the target cluster lower-left that turns from blue to orange as it locks.
-- Everything animates from tau only, so scrubbed frames look exactly like playback.
local NAVY = Color3.fromRGB(1, 4, 10)
local CYAN = Color3.fromRGB(70, 190, 255)
local ICE = Color3.fromRGB(190, 235, 255)
local LOCK = Color3.fromRGB(255, 120, 70)

local hudGui = Instance.new("ScreenGui")
hudGui.Name = "HelmetHUD"
hudGui.IgnoreGuiInset = true
hudGui.ResetOnSpawn = false
hudGui.DisplayOrder = 9                                    -- under the letterbox, overlay and subs
hudGui.Enabled = false
hudGui.Parent = player.PlayerGui

hud = Instance.new("Frame")                                -- sized to the movie frame by layoutFrame
hud.BackgroundTransparency = 1
hud.ClipsDescendants = true
hud.Parent = hudGui

local grade = Instance.new("ColorCorrectionEffect")
grade.Name = "HelmetGrade"
grade.TintColor = Color3.fromRGB(185, 210, 255)
grade.Brightness, grade.Contrast, grade.Saturation = 0.12, 0.0, -0.2   -- helmet look, but the face stays readable (was too dark)
grade.Enabled = false
grade.Parent = game:GetService("Lighting")

local function hudFrame(props)
	local f = Instance.new("Frame")
	f.BorderSizePixel = 0
	for k, v in pairs(props) do
		f[k] = v
	end
	f.Parent = props.Parent or hud
	return f
end

local function fade(f, rotation, keys)                     -- keys: {{at, transparency}, ...}
	local g = Instance.new("UIGradient")
	g.Rotation = rotation
	local seq = {}
	for _, k in ipairs(keys) do
		table.insert(seq, NumberSequenceKeypoint.new(k[1], k[2]))
	end
	g.Transparency = NumberSequence.new(seq)
	g.Parent = f
	return g
end

-- vignette: dark from left/right edges into an oval around the face
local EDGE = { { 0, 0 }, { 0.55, 0.25 }, { 1, 1 } }
fade(hudFrame({ BackgroundColor3 = NAVY, Size = UDim2.fromScale(0.35, 1) }), 0, EDGE)
fade(hudFrame({ BackgroundColor3 = NAVY, Size = UDim2.fromScale(0.35, 1), Position = UDim2.fromScale(0.65, 0) }), 180, EDGE)
fade(hudFrame({ BackgroundColor3 = NAVY, Size = UDim2.fromScale(1, 0.16) }), 90, EDGE)
local DIM = 0.6                                           -- light overall darkening; the face stays readable
local dim = hudFrame({ BackgroundColor3 = NAVY, Size = UDim2.fromScale(1, 1), BackgroundTransparency = DIM })

-- 2D cyan holographic HUD arcs (left and right curved brackets)
local hudArcLeft = hudFrame({ BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.18, 0.5), Size = UDim2.fromScale(0.24, 0.72) })
Instance.new("UICorner", hudArcLeft).CornerRadius = UDim.new(0.5, 0)
local arcLeftStroke = Instance.new("UIStroke")
arcLeftStroke.Color, arcLeftStroke.Thickness, arcLeftStroke.Transparency = CYAN, 1.5, 0.4
arcLeftStroke.Parent = hudArcLeft

local hudArcRight = hudFrame({ BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.82, 0.5), Size = UDim2.fromScale(0.24, 0.72) })
Instance.new("UICorner", hudArcRight).CornerRadius = UDim.new(0.5, 0)
local arcRightStroke = Instance.new("UIStroke")
arcRightStroke.Color, arcRightStroke.Thickness, arcRightStroke.Transparency = CYAN, 1.5, 0.4
arcRightStroke.Parent = hudArcRight

-- glass streaks: long thin diagonal reflections in the lower corners
local streaks = {}
for _, s in ipairs({
	{ x = 0.06, y = 0.7, len = 0.3, rot = 62, a = 0.75 },
	{ x = 0.12, y = 0.78, len = 0.2, rot = 58, a = 0.85 },
	{ x = 0.86, y = 0.7, len = 0.28, rot = -64, a = 0.8 },
	{ x = 0.78, y = 0.82, len = 0.18, rot = -60, a = 0.88 },
}) do
	local f = hudFrame({ BackgroundColor3 = ICE, AnchorPoint = Vector2.new(0.5, 0.5), Rotation = s.rot,
		Position = UDim2.fromScale(s.x, s.y), Size = UDim2.new(s.len, 0, 0, 2) })
	fade(f, 0, { { 0, 1 }, { 0.5, 0 }, { 1, 1 } })
	table.insert(streaks, { frame = f, base = s.a })
end

-- readouts: rows of short bars on the right, a few on the left, like the movie's HUD text
local bars = {}
for i, b in ipairs({
	{ x = 0.84, y = 0.12, n = 3 }, { x = 0.88, y = 0.17, n = 2 }, { x = 0.8, y = 0.3, n = 4 },
	{ x = 0.86, y = 0.52, n = 2 }, { x = 0.06, y = 0.42, n = 2 }, { x = 0.03, y = 0.52, n = 3 },
}) do
	for j = 1, b.n do
		local f = hudFrame({ BackgroundColor3 = (i + j) % 3 == 0 and ICE or CYAN,
			Position = UDim2.new(b.x, (j - 1) * 22, b.y, 0), Size = UDim2.fromOffset(16 + (i * j) % 3 * 6, 3) })
		table.insert(bars, { frame = f, seed = i * 7 + j })
	end
end

-- scan line drifting down the visor
local scan = hudFrame({ BackgroundColor3 = CYAN, Size = UDim2.new(1, 0, 0, 2) })
fade(scan, 0, { { 0, 0.7 }, { 0.25, 0.85 }, { 0.32, 1 }, { 0.68, 1 }, { 0.75, 0.85 }, { 1, 0.7 } })   -- edges only, off the face

-- target lock (hud = "lock"): ring cluster lower-left, a big arc and a dashed line
local lock = hudFrame({ BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.1, 0.72), Size = UDim2.fromScale(0.16, 0.16) })
local ring = hudFrame({ Parent = lock, BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
	Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(1.5, 1.5) })
Instance.new("UICorner", ring).CornerRadius = UDim.new(0.5, 0)
Instance.new("UIAspectRatioConstraint", ring)
local ringStroke = Instance.new("UIStroke")
ringStroke.Thickness = 1.5
ringStroke.Parent = ring
local pips = {}
for i, p in ipairs({ { 0.5, 0.2 }, { 0.78, 0.35 }, { 0.22, 0.45 }, { 0.55, 0.55 }, { 0.3, 0.8 }, { 0.75, 0.85 } }) do
	local f = hudFrame({ Parent = lock, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(p[1], p[2]),
		Size = UDim2.fromScale(0.24, 0.24) })
	Instance.new("UICorner", f).CornerRadius = UDim.new(0.5, 0)
	Instance.new("UIAspectRatioConstraint", f)
	local stroke = Instance.new("UIStroke")
	stroke.Thickness = 2
	stroke.Parent = f
	table.insert(pips, { frame = f, stroke = stroke, delay = (i - 1) * 0.08 })
end
local dashes = {}
for i = 1, 8 do
	table.insert(dashes, hudFrame({ Parent = lock, Position = UDim2.new(-0.3 + i * 0.16, 0, 0.5, 0), Size = UDim2.new(0.08, 0, 0, 2) }))
end

local impactBorder = hudFrame({ BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
local impactStroke = Instance.new("UIStroke")
impactStroke.Thickness = 6
impactStroke.Color = Color3.fromRGB(255, 40, 40)
impactStroke.Transparency = 1
impactStroke.Parent = impactBorder

local function flicker(tau, seed, speed)
	return math.noise(tau * (speed or 4), seed * 1.37, 0.5)  -- -0.5..0.5-ish, deterministic in tau
end

-- the HUD screens light the face from the front: a cool light just in front of the wearer's face
local faceLight = Instance.new("PointLight")
faceLight.Color, faceLight.Range, faceLight.Shadows = ICE, 10, false
faceLight.Enabled = false

local faceLightLeft = Instance.new("PointLight")
faceLightLeft.Color, faceLightLeft.Range, faceLightLeft.Shadows = Color3.fromRGB(0, 215, 255), 14, false
faceLightLeft.Enabled = false

local function lightFace(on, shot, tau)
	local head = findPart("IronMan.Head")
	if on and head then
		if faceLight.Parent ~= head then
			local a = head:FindFirstChild("HUDLight") or Instance.new("Attachment")
			a.Name = "HUDLight"
			a.Position = Vector3.new(0, -0.1, -1.4) * head.Size.Y   -- head-local front is -Z
			a.Parent = head
			faceLight.Parent = a
		end
		if faceLightLeft.Parent ~= head then
			local aL = head:FindFirstChild("HUDLightLeft") or Instance.new("Attachment")
			aL.Name = "HUDLightLeft"
			aL.Position = Vector3.new(-1.2, 0.1, -1.2) * head.Size.Y
			aL.Parent = head
			faceLightLeft.Parent = aL
		end
	end
	faceLight.Enabled = on and head ~= nil
	faceLight.Brightness = 4.0   -- lights Tony's face inside the visor so the eyes and mouth read (movie 060/080/100)
	faceLight.Range = 8

	local is405 = shot and (shot.shot == "405" or (shot.face and shot.face.yaw and shot.face.yaw > 30))
	faceLightLeft.Enabled = on and is405 and head ~= nil
	faceLightLeft.Brightness = is405 and 16 or 0
end

-- inside the mask the camera sits where the helmet is: hide helmet, visor, and clipping parts (this client only)
local helmetHidden = nil
local function hideHelmet(on, shot, tau)
	local ironMan = workspace:FindFirstChild("IronMan")
	if not ironMan then
		return
	end
	if on then
		helmetHidden = true
		for _, mName in ipairs({ "Iron Man Helmet", "Model", "WavyPopularGirlGingerHair" }) do
			local m = ironMan:FindFirstChild(mName)
			if m then
				for _, p in ipairs(m:GetDescendants()) do
					if p:IsA("BasePart") then
						p.LocalTransparencyModifier = 1
					end
				end
			end
		end
		for _, item in ipairs(ironMan:GetDescendants()) do
			if item:GetAttribute("HideInHUD") or item:IsA("Accessory") then
				for _, p in ipairs(item:IsA("BasePart") and { item, unpack(item:GetDescendants()) } or item:GetDescendants()) do
					if p:IsA("BasePart") then
						p.LocalTransparencyModifier = 1
					end
				end
			end
		end
	elseif helmetHidden then
		helmetHidden = false
		for _, mName in ipairs({ "Iron Man Helmet", "Model", "WavyPopularGirlGingerHair" }) do
			local m = ironMan:FindFirstChild(mName)
			if m then
				for _, p in ipairs(m:GetDescendants()) do
					if p:IsA("BasePart") then
						p.LocalTransparencyModifier = 0
					end
				end
			end
		end
		for _, item in ipairs(ironMan:GetDescendants()) do
			if item:GetAttribute("HideInHUD") or item:IsA("Accessory") then
				for _, p in ipairs(item:IsA("BasePart") and { item, unpack(item:GetDescendants()) } or item:GetDescendants()) do
					if p:IsA("BasePart") then
						p.LocalTransparencyModifier = 0
					end
				end
			end
		end
	end

	-- Shot 200: Unmasked Tony Stark (helmet torn off, dark hair exposed, shocked mouth)
	local isShot200 = (not on) and (tau >= 30.496 and tau < 31.05)
	local isShot230 = (not on) and (tau >= 35.250 and tau < 35.876)

	local hair = ironMan:FindFirstChild("WavyPopularGirlGingerHair")
	local hairHandle = hair and hair:FindFirstChild("Handle")
	local ihead = ironMan:FindFirstChild("Head")
	local ilips = ihead and ihead:FindFirstChild("lips")
	local imHelmet = ironMan:FindFirstChild("Iron Man Helmet")
	local mouthPart = imHelmet and imHelmet:FindFirstChild("Mouth")

	if isShot200 then
		for _, mName in ipairs({ "Iron Man Helmet", "Model" }) do
			local m = ironMan:FindFirstChild(mName)
			if m then
				for _, p in ipairs(m:GetDescendants()) do
					if p:IsA("BasePart") then
						p.LocalTransparencyModifier = 1
					end
				end
			end
		end
		for _, item in ipairs(ironMan:GetDescendants()) do
			if item:GetAttribute("HideInHUD") then
				for _, p in ipairs(item:IsA("BasePart") and { item, unpack(item:GetDescendants()) } or item:GetDescendants()) do
					if p:IsA("BasePart") then
						p.LocalTransparencyModifier = 1
					end
				end
			end
		end
		if hairHandle then
			hairHandle.LocalTransparencyModifier = 0
			hairHandle.Color = Color3.fromRGB(35, 30, 28)
			local sm = hairHandle:FindFirstChildOfClass("SpecialMesh")
			if sm then sm.VertexColor = Vector3.new(0.2, 0.17, 0.15) end
		end
		if ilips then
			ilips.Texture = "rbxassetid://4870848084"
		end
	else
		if hairHandle and not on then
			hairHandle.LocalTransparencyModifier = 1
		end
		if ilips and not on then
			ilips.Texture = "rbxassetid://6105612051"
		end
	end

	-- Shot 230: Scuffed battle-damaged faceplate
	if mouthPart then
		if isShot230 then
			mouthPart.Material = Enum.Material.CorrodedMetal
		else
			mouthPart.Material = Enum.Material.Metal
		end
	end

	-- Shot 430: Punch 2 — Shattered Helmet (upper-left half of mask torn away)
	local imModel = ironMan:FindFirstChild("Model")
	local upperMask = imModel and imModel:FindFirstChild("UpperMask")
	if upperMask and not on and not isShot200 then
		if tau >= 59.358 and tau < 60.317 then
			upperMask.LocalTransparencyModifier = 1
		else
			upperMask.LocalTransparencyModifier = 0
		end
	end
end

-- shot.hide = rig name: that rig is cheated out of frame for the shot (this client only)
local hiddenRig = nil
local function cheatOut(name)
	if hiddenRig == name then
		return
	end
	local function set(rigName, value)
		local rig = rigName and workspace:FindFirstChild(rigName)
		for _, p in ipairs(rig and rig:GetDescendants() or {}) do
			if p:IsA("BasePart") then
				p.LocalTransparencyModifier = value
			end
		end
	end
	set(hiddenRig, 0)                                        -- (two calls: a nil in an ipairs list ends it)
	set(name, 1)
	hiddenRig = name
end

local function updateHud(shot, localT, tau)
	cheatOut(shot.hide)
	local on = shot.hud ~= nil
	hudGui.Enabled, grade.Enabled = on, on
	lightFace(on, shot, tau)
	hideHelmet(on, shot, tau)
	if not on then
		return
	end
	local intro = math.clamp(localT / 0.25, 0, 1)            -- visor fades up over the first frames
	arcLeftStroke.Transparency = math.clamp(0.35 + 0.15 * flicker(tau, 1, 2), 0.1, 0.8)
	arcRightStroke.Transparency = math.clamp(0.35 + 0.15 * flicker(tau, 2, 2), 0.1, 0.8)

	-- face: always the default decals (no expression changes)
	local im = workspace:FindFirstChild("IronMan")
	local ihead = im and im:FindFirstChild("Head")
	local ilips, ieyes = ihead and ihead:FindFirstChild("lips"), ihead and ihead:FindFirstChild("eyeballs")
	if ilips then
		ilips.Texture = "rbxassetid://6105612051"
	end
	if ieyes then
		ieyes.Texture = "rbxassetid://5921278628"
	end

	local th = workspace:FindFirstChild("Thanos")
	local thHead = th and th:FindFirstChild("Head")
	local thDecal = thHead and thHead:FindFirstChild("Decal")
	if thDecal then
		thDecal.Texture = "rbxassetid://1512463393"     -- default face, never changed
	end
	for i, s in ipairs(streaks) do
		s.frame.BackgroundTransparency = math.clamp(s.base + 0.2 * flicker(tau, i + 20, 2), 0, 1)
	end
	for _, b in ipairs(bars) do
		b.frame.BackgroundTransparency = flicker(tau, b.seed, 6) > 0.25 and 0.85 or 0.35
	end
	scan.Position = UDim2.fromScale(0, (localT * 0.45) % 1)

	local is415 = shot.shot == "415"
	impactBorder.Visible = is415
	if is415 then
		impactStroke.Transparency = flicker(tau, 99, 12) > 0 and 0.1 or 0.6
		impactStroke.Color = (math.floor(tau * 30) % 2 == 0) and Color3.fromRGB(255, 50, 50) or CYAN
	end

	local locking = shot.hud == "lock"
	lock.Visible = locking
	if locking then
		local u = math.clamp((localT - 0.3) / 1.2, 0, 1)      -- blue search -> orange lock (movie 388 -> 425)
		local color = CYAN:Lerp(LOCK, u)
		for _, p in ipairs(pips) do
			local shown = localT >= 0.3 + p.delay
			p.frame.Visible = shown
			p.frame.BackgroundColor3 = color
			p.frame.BackgroundTransparency = 0.55 + 0.15 * flicker(tau, p.delay * 50, 5)
			p.stroke.Color = color:Lerp(ICE, 0.3)
		end
		ring.Visible = u > 0.5
		ringStroke.Color, ringStroke.Transparency = color, 0.4
		for _, d in ipairs(dashes) do
			d.Visible = u > 0.3
			d.BackgroundColor3 = ICE
			d.BackgroundTransparency = 0.5
		end
		lock.Position = UDim2.fromScale(0.1 + 0.04 * u, 0.74 - 0.04 * u)   -- drifts onto the target
	end
end

-- ------------------------------------------------------------------ fill light
-- A soft warm key from the camera side, like a film set's fill: Titan is backlit, and without it
-- the suits' colours sink into shadow. Off in the HUD shots (they light the face themselves).
-- One key per character, like a bounce board just off camera: placed between the camera and his
-- body, a little above, aimed at his middle, distance and reach scaled to his size so it lights
-- him and barely the ground. Carried by Attachments in Terrain (a part near the camera changes
-- how Roblox renders the haze). Iron Man's is off in the HUD shots (the face light takes over).
local keys = {}
for _, name in ipairs({ "IronMan", "Thanos" }) do
	local at = Instance.new("Attachment")
	at.Name = "Key_" .. name
	local light = Instance.new("SpotLight")
	light.Color, light.Brightness, light.Angle, light.Shadows = Color3.fromRGB(255, 226, 196), 1.5, 45, false   -- a soft fill only: the reference faces sit in shadow
	light.Face = Enum.NormalId.Front
	light.Parent = at
	-- the rim: the reference is backlit by a warm low sun, so each character gets a strong light from behind and
	-- above, opposite the lens, that edges the shoulders and head
	local rimAt = Instance.new("Attachment")
	rimAt.Name = "Rim_" .. name
	local rim = Instance.new("SpotLight")
	rim.Color, rim.Brightness, rim.Angle, rim.Shadows = Color3.fromRGB(255, 186, 120), 16, 50, true   -- shadows on: the body blocks it, only edges catch it
	rim.Face = Enum.NormalId.Front
	rim.Parent = rimAt
	keys[name] = { at = at, light = light, rimAt = rimAt, rim = rim }
end

local function updateFill(shot)
	for name, k in pairs(keys) do
		local chest, ratio = findPart(name .. ".UpperTorso")
		local hips = findPart(name .. ".LowerTorso")
		if k.at.Parent ~= workspace.Terrain then
			k.at.Parent = workspace.Terrain
			k.rimAt.Parent = workspace.Terrain
		end
		k.light.Enabled = chest ~= nil and not (shot.hud and name == "IronMan")
		k.rim.Enabled = k.light.Enabled
		if chest and hips then
			local middle = chest.Position:Lerp(hips.Position, 0.5)
			local size = 5.2 * (workspace[name]:GetAttribute("SizeRatio") or 1) / ((Scene.rigs[name] and Scene.rigs[name].camScale) or 1)
			local toCam = camera.CFrame.Position - middle
			local flat = Vector3.new(toCam.X, 0, toCam.Z)
			flat = flat.Magnitude > 1e-3 and flat.Unit or Vector3.zAxis
			local pos = middle + flat * size * 1.05 + Vector3.new(0, size * 0.3, 0)
			k.at.WorldCFrame = CFrame.lookAt(pos, middle)
			k.light.Range = size * 3
			local rimPos = middle - flat * size * 1.1 + Vector3.new(0, size * 0.75, 0)
			k.rimAt.WorldCFrame = CFrame.lookAt(rimPos, middle + Vector3.new(0, size * 0.15, 0))
			k.rim.Range = size * 3
		end
	end
end

local function keysOff()
	for _, k in pairs(keys) do
		k.light.Enabled = false
		k.rim.Enabled = false
	end
end

-- ------------------------------------------------------------------ playback
local running, connection, parked = nil, nil, nil
local frozenTau = nil                                  -- set while scrubbing

local function park(on)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not root then
		return
	end
	if on then
		parked = { cf = root.CFrame, anchored = root.Anchored, hidden = {} }
		root.Anchored = true
		character:PivotTo(CFrame.new(0, 500, 500))     -- keep the player avatar out of every shot
		for _, d in ipairs(workspace:GetDescendants()) do   -- spawn pads sit on the stage: hide them (this client only)
			if d:IsA("SpawnLocation") then
				for _, v in ipairs({ d, table.unpack(d:GetDescendants()) }) do
					if v:IsA("BasePart") or v:IsA("Decal") then
						table.insert(parked.hidden, { v, v.Transparency })
						v.Transparency = 1
					end
				end
			end
		end
	elseif parked then
		character:PivotTo(parked.cf)
		root.Anchored = parked.anchored
		for _, h in ipairs(parked.hidden) do
			h[1].Transparency = h[2]
		end
		parked = nil
	end
end

local function finish()
	if connection then
		connection:Disconnect()
		connection = nil
	end
	running, frozenTau = nil, nil
	gui.Enabled = false
	hudGui.Enabled, grade.Enabled, faceLight.Enabled = false, false, false
	helmetHidden = nil                                       -- force: the helmet break may have hidden pieces
	hideHelmet(false)
	cheatOut(nil)
	keysOff()
	camera.CameraType = Enum.CameraType.Custom
	camera.FieldOfView = 70
	applyLook(false)
	stopFx()
	park(false)
	local panel = player.PlayerGui:FindFirstChild("ShotButtons")
	if panel then
		panel.Enabled = true
	end
end

sceneStart.OnClientEvent:Connect(function(startAt, scrubTau)
	if not startAt then
		finish()
		return
	end
	if not running then
		park(true)
	end
	running, frozenTau = startAt, scrubTau
	gui.Enabled = true
	local panel = player.PlayerGui:FindFirstChild("ShotButtons")
	if panel then
		panel.Enabled = false
	end
	camera.CameraType = Enum.CameraType.Scriptable
	startFx()
	applyLook(true)
	if connection then
		connection:Disconnect()
	end
	connection = RunService.RenderStepped:Connect(function()
		local tau = frozenTau or math.max(0, workspace:GetServerTimeNow() - running)
		local shot = shotAt(tau)
		local cf, fov = cameraAt(shot, tau - shot.start)
		local stretch = layoutFrame()
		camera.CFrame = cf * shakeAt(tau)
		camera.FieldOfView = math.deg(2 * math.atan(math.tan(math.rad(fov) / 2) * stretch))
		updateFocus(cf, fov, shot.hud)
		updateSun(shot, cf)
		updateAirDust(cf)
		fxLive = frozenTau == nil
		for _, item in ipairs(activeFx) do
			item.kind.update(item.state, tau)
		end
		updateHud(shot, tau - shot.start, tau)
		updateFill(shot)
		subtitle.Visible = showSubs
		subtitle.Text = subtitleAt(tau)
		label.Visible = showLabel
		label.Text = string.format(" FRAME %03d   %5.2fs   SHOT %s%s", math.floor(tau * MOVIE_FPS + 1e-6), tau, shot.shot,
			frozenTau and "   [SCRUB]" or "")
	end)
end)

UserInputService.InputBegan:Connect(function(input, typing)
	if typing then
		return
	end
	if input.KeyCode == Enum.KeyCode.T then
		showLabel = not showLabel
	elseif input.KeyCode == Enum.KeyCode.Y then
		showSubs = not showSubs
	elseif frozenTau and (input.KeyCode == Enum.KeyCode.LeftBracket or input.KeyCode == Enum.KeyCode.RightBracket) then
		local frame = math.floor(frozenTau * MOVIE_FPS + 1e-6) + (input.KeyCode == Enum.KeyCode.RightBracket and 1 or -1)
		shotControl:FireServer("scrub", math.max(0, frame))
	end
end)
