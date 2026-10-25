-- ShotPlayer (synced by Rojo into ServerScriptService)
-- 1. Sets up the cast from SceneData: rigs named Thanos / IronMan (renames Dummies if needed),
--    scales them and puts them on their marks.
-- 2. Plays single shots from the panel on the right rig (name contains "thanos"/"ironman").
-- 3. Plays the whole scene on the movie timeline; every client's Director runs the camera in sync.
-- Studio play-test only: RegisterKeyframeSequence ids work in Studio, not in a published game.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")

pcall(function()
	local VoiceChatService = game:GetService("VoiceChatService")
	VoiceChatService.EnableDefaultVoice = false
end)

local Scene = require(ReplicatedStorage:WaitForChild("SceneData"))
local Costumes = require(ServerStorage:WaitForChild("Costumes"))

local shotControl = Instance.new("RemoteEvent")
shotControl.Name = "ShotControl"
shotControl.Parent = ReplicatedStorage

local sceneStart = Instance.new("RemoteEvent")   -- server -> clients: (startServerTime) or (nil) to end
sceneStart.Name = "SceneStart"
sceneStart.Parent = ReplicatedStorage

local shotList = Instance.new("Folder")
shotList.Name = "ShotList"
shotList.Parent = ReplicatedStorage

-- ------------------------------------------------------------------ cast
local function isRig(m)
	return m:IsA("Model") and m:FindFirstChildOfClass("Humanoid") and m:FindFirstChild("HumanoidRootPart")
end

local function lowestPoint(rig)
	local low = math.huge
	for _, p in ipairs(rig:GetDescendants()) do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and p.Transparency < 1 and not p:FindFirstAncestorOfClass("Accessory") then
			local half = p.Size / 2
			for _, c in ipairs({ Vector3.new(1, 1, 1), Vector3.new(1, 1, -1), Vector3.new(1, -1, 1), Vector3.new(1, -1, -1),
				Vector3.new(-1, 1, 1), Vector3.new(-1, 1, -1), Vector3.new(-1, -1, 1), Vector3.new(-1, -1, -1) }) do
				low = math.min(low, (p.CFrame * (half * c)).Y)
			end
		end
	end
	return low
end

local function heightOf(rig)                          -- body height: parts only, no accessories or root
	local low, high = math.huge, -math.huge
	for _, p in ipairs(rig:GetDescendants()) do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" and not p:FindFirstAncestorOfClass("Accessory") and p.Transparency < 1 then
			local half = p.Size / 2
			for _, c in ipairs({ Vector3.new(1, 1, 1), Vector3.new(-1, -1, -1), Vector3.new(1, -1, 1), Vector3.new(-1, 1, -1) }) do
				local y = (p.CFrame * (half * c)).Y
				low, high = math.min(low, y), math.max(high, y)
			end
		end
	end
	return high - low
end

-- Iron Man's red plates are Metal (some with negative reflectance). Roblox metal shows almost only
-- reflections, and on Titan the surroundings are dark rock, so the red went near-black in every
-- shot. For the shoot they get a glossy paint finish instead (runtime only; the saved model is
-- untouched). Gold and trim stay Metal: they read well.
local function filmPaint(rig)
	for _, p in ipairs(rig:GetDescendants()) do
		if p:IsA("BasePart") and p.Material == Enum.Material.Metal then
			local c = p.Color
			if c.R > 0.15 and c.R > c.G * 2.5 then
				p.Material, p.Reflectance = Enum.Material.SmoothPlastic, 0.12
			end
		end
	end
end

local function setupCast()
	local spare = {}
	for _, m in ipairs(workspace:GetChildren()) do
		if isRig(m) and m.Name == "Dummy" then
			table.insert(spare, m)
		end
	end
	local rigs = {}
	for name, spec in pairs(Scene.rigs) do
		local rig = workspace:FindFirstChild(name)
		if not (rig and isRig(rig)) then
			rig = table.remove(spare, 1)
			if not rig then
				warn(("ShotPlayer: no rig for %s — add an R15 rig named %s (Avatar > Rig Builder)"):format(name, name))
				continue
			end
			print(("ShotPlayer: renamed a Dummy to %s"):format(name))
			rig.Name = name
			Costumes.dress(rig, name)                   -- plain dummies get the built costume; user models keep their own look
		end
		local root = rig.HumanoidRootPart
		root.Anchored = true
		if name == "IronMan" then
			filmPaint(rig)
			-- the faceplate (UpperMask / LowerMask / Eyes) lives outside the helmet model: tag it as
			-- helmet too, so the HUD shots and the helmet break hide the whole mask
			for _, d in ipairs(rig:GetDescendants()) do
				if d:IsA("BasePart") and (d.Name == "UpperMask" or d.Name == "LowerMask") then
					local holder = d.Parent:IsA("Model") and d.Parent ~= rig and d.Parent or d
					holder:SetAttribute("HideInHUD", true)
				end
			end
		end
		-- cameras were planned on the plain dummy (Scene.refHeight tall, times the rig's scale) and
		-- tuned with a per-rig factor (camScale); the Director multiplies camera offsets by
		-- SizeRatio, so framing holds for any avatar or custom model
		local height = heightOf(rig)
		if math.abs(rig:GetScale() - spec.scale) > 1e-3 then
			rig:ScaleTo(spec.scale)
		end
		rig:SetAttribute("SizeRatio", height / Scene.refHeight * (spec.camScale or 1))
		print(("ShotPlayer: %s is %.2f studs tall unscaled (camera size ratio %.2f)"):format(name, height, rig:GetAttribute("SizeRatio")))
		-- place by the root part (a model's pivot can point anywhere), then drop the lowest body
		-- point exactly onto the mark
		local want = CFrame.new(spec.pos) * CFrame.Angles(0, math.rad(spec.yaw), 0)
		rig:PivotTo(want * root.CFrame:ToObjectSpace(rig:GetPivot()))
		rig:PivotTo(rig:GetPivot() + Vector3.new(0, spec.pos.Y - lowestPoint(rig), 0))
		local humanoid = rig:FindFirstChildOfClass("Humanoid")
		local animator = humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", humanoid)
		rigs[name] = { model = rig, animator = animator, tracks = {}, current = nil }
	end
	return rigs
end

local rigs = setupCast()

-- ------------------------------------------------------------------ shots
local animations = {}

local function lengthOf(ks)
	local last = 0
	for _, keyframe in ipairs(ks:GetKeyframes()) do
		last = math.max(last, keyframe.Time)
	end
	return last
end

local shotsFolder = ServerStorage:FindFirstChild("Shots")
if shotsFolder then
	for _, ks in ipairs(shotsFolder:GetDescendants()) do
		if ks:IsA("KeyframeSequence") and not animations[ks.Name] then
			local anim = Instance.new("Animation")
			anim.AnimationId = KeyframeSequenceProvider:RegisterKeyframeSequence(ks)
			animations[ks.Name] = anim
			local entry = Instance.new("StringValue")
			entry.Name = ks.Name
			entry:SetAttribute("Length", Scene.lengths[ks.Name] or lengthOf(ks))
			entry.Parent = shotList
		end
	end
end

-- A scaled rig stands lower once an animation drives it than in its rest pose, so settle each rig
-- on its mark while it holds a standing pose (Scene.stand), measured, then let go.
local function settleOnMarks()
	for name, rig in pairs(rigs) do
		local anim = Scene.stand and animations[Scene.stand[name]]
		if anim then
			local track = rig.animator:LoadAnimation(anim)
			track:Play(0, 1, 0)
			task.wait(0.25)
			local model = rig.model
			model:PivotTo(model:GetPivot() + Vector3.new(0, Scene.rigs[name].pos.Y - lowestPoint(model), 0))
			track:Stop(0)
		end
	end
end
task.spawn(settleOnMarks)

local function rigsFor(shotName)
	local lower = shotName:lower()
	for name, rig in pairs(rigs) do
		if lower:find(name:lower(), 1, true) then
			return { rig }
		end
	end
	local all = {}
	for _, rig in pairs(rigs) do
		table.insert(all, rig)
	end
	return all
end

local function trackFor(rig, animName)
	local track = rig.tracks[animName]
	if not track and animations[animName] then
		track = rig.animator:LoadAnimation(animations[animName])
		track.Looped = false
		rig.tracks[animName] = track
	end
	return track
end

local function playOn(rig, animName, speed)
	local track = trackFor(rig, animName)
	if not track then
		warn("ShotPlayer: missing animation", animName)
		return
	end
	if rig.current and rig.current ~= track then
		rig.current:Stop(0)
	end
	rig.current = track
	track:Play(0, 1, speed or 1)          -- no fade: cuts are hard cuts
	return track
end

local function freeze(track, at)
	if track and track.IsPlaying then
		track:AdjustSpeed(0)
		track.TimePosition = at
	end
end

local function stopAll()
	for _, rig in pairs(rigs) do
		for _, track in pairs(rig.tracks) do
			track:Stop(0)
		end
		rig.current = nil
	end
end

-- ------------------------------------------------------------------ scene playback
local sceneId = 0
-- movie clock for the transport (Space pause, Left/Right 1 s): start = server time of movie 0,
-- paused = movie seconds while held, finish = end of the scene's last shot
local clock = { start = nil, paused = nil, finish = 0 }

local function at(serverTime, fn)
	local id = sceneId
	task.delay(math.max(0, serverTime - workspace:GetServerTimeNow()), function()
		if id == sceneId then
			fn()
		end
	end)
end

local function playScene(from)                         -- from: movie time to start at (default 0)
	from = from or 0
	sceneId += 1
	stopAll()
	for rigName, animName in pairs(Scene.preroll) do      -- everyone on their opening pose
		local rig = rigs[rigName]
		if rig then
			freeze(playOn(rig, animName), 0)
		end
	end
	local start = workspace:GetServerTimeNow() + 0.75 - from   -- lead-in so clients are ready
	clock.start, clock.paused = start, nil
	sceneStart:FireAllClients(start)
	local finish = 0
	for _, shot in ipairs(Scene.shots) do
		for rigName, animName in pairs(shot.play) do
			local rig = rigs[rigName]
			if rig and shot.start + shot.dur > from then
				at(start + shot.start, function()
					local track = playOn(rig, animName)
					local late = workspace:GetServerTimeNow() - (start + shot.start)
					if track and late > 0.02 then                -- started mid-shot (PlayFrom)
						track.TimePosition = late
					end
					at(start + shot.start + shot.dur, function()
						if rig.current == track then
							freeze(track, shot.dur)        -- hold the last pose until this rig's next shot
						end
					end)
				end)
			end
		end
		finish = math.max(finish, shot.start + shot.dur)
	end
	clock.finish = finish
	at(start + finish + 1.0, function()
		sceneStart:FireAllClients(nil)
	end)
end

-- Scrub: freeze every rig on one exact movie frame; clients hold the camera there too.
-- Driven by the panel ([ / ] step a frame) or by ReplicatedStorage's "ScrubFrame" attribute
-- (set it from the command bar / MCP; clear it to leave scrub).
local MOVIE_FPS = 23.976
local scrubbing = false

local function leaveScrub()                              -- before any other playback takes over
	scrubbing = false
	ReplicatedStorage:SetAttribute("ScrubFrame", nil)
end

local function poseAt(rigName, tau)
	local animName, localT = Scene.preroll[rigName], 0
	for _, shot in ipairs(Scene.shots) do
		if shot.play[rigName] and shot.start <= tau then
			animName, localT = shot.play[rigName], math.min(tau - shot.start, shot.dur)
		end
	end
	return animName, localT
end

local function scrub(frame)
	sceneId += 1
	scrubbing = true
	local tau = frame / MOVIE_FPS
	for rigName, rig in pairs(rigs) do
		local animName, localT = poseAt(rigName, tau)
		local track = playOn(rig, animName)
		if track then
			track.Looped = false
			freeze(track, localT)
		end
	end
	sceneStart:FireAllClients(workspace:GetServerTimeNow(), tau)
end

ReplicatedStorage:GetAttributeChangedSignal("ScrubFrame"):Connect(function()
	local frame = ReplicatedStorage:GetAttribute("ScrubFrame")
	if typeof(frame) == "number" then
		scrub(math.max(0, math.floor(frame)))
	elseif scrubbing then
		scrubbing = false
		sceneId += 1
		stopAll()
		sceneStart:FireAllClients(nil)
	end
end)

-- "PlayFrom" attribute (movie seconds): play the scene live starting there. Set it from the
-- command bar / MCP (server side, so nothing on the client touches the camera); it clears itself.
ReplicatedStorage:GetAttributeChangedSignal("PlayFrom"):Connect(function()
	local from = ReplicatedStorage:GetAttribute("PlayFrom")
	if typeof(from) == "number" then
		leaveScrub()
		playScene(math.max(0, from))
		ReplicatedStorage:SetAttribute("PlayFrom", nil)
	end
end)

-- Transport. Space ('toggle') pauses: a paused scene is a frozen scrub frame, so the camera and the
-- rigs hold. Left/Right ('back'/'fwd') move 1 movie second and keep the play or pause state.
local function movieNow()
	if clock.paused then
		return clock.paused
	end
	if not clock.start then
		return 0
	end
	return math.clamp(workspace:GetServerTimeNow() - clock.start, 0, clock.finish)
end

local function holdAt(tau)
	clock.paused = math.max(0, tau)
	sceneId += 1
	scrubbing = true
	ReplicatedStorage:SetAttribute("ScrubFrame", math.floor(clock.paused * MOVIE_FPS))
end

local function transport(cmd)
	if cmd == "toggle" then
		if clock.paused then
			local tau = clock.paused
			leaveScrub()
			playScene(tau)
		else
			holdAt(movieNow())
		end
		return
	end
	local delta = (cmd == "back" and -1) or (cmd == "fwd" and 1) or 0
	if delta == 0 then
		return
	end
	local tau = math.max(0, movieNow() + delta)
	if clock.paused then
		holdAt(tau)
	else
		leaveScrub()
		playScene(tau)
	end
end

shotControl.OnServerEvent:Connect(function(_, action, shotName, speed, looped)
	if action == "transport" then
		transport(shotName)
		return
	end
	if action == "scene" then
		leaveScrub()
		playScene()
		return
	end
	if action == "scrub" then
		ReplicatedStorage:SetAttribute("ScrubFrame", math.max(0, math.floor(tonumber(shotName) or 0)))
		return
	end
	sceneId += 1                                         -- any manual action cancels the scene
	leaveScrub()
	if action == "stop" then
		stopAll()
		sceneStart:FireAllClients(nil)
		return
	end
	if action ~= "play" or not animations[shotName] then
		return
	end
	speed = math.clamp(tonumber(speed) or 1, 0.05, 4)
	for _, rig in ipairs(rigsFor(shotName)) do
		local track = playOn(rig, shotName, speed)
		if track then
			track.Looped = looped == true
		end
	end
end)

-- Preload every shot's track on its rig. A track loads the first time it is used, and that can
-- take long enough that a short shot misses its cut entirely in live playback (scrubbing hid it,
-- since a scrub waits). Length is 0 until a track has loaded.
local preloaded, pending = 0, {}
for _, shot in ipairs(Scene.shots) do
	for rigName, animName in pairs(shot.play) do
		local rig = rigs[rigName]
		local track = rig and trackFor(rig, animName)
		if track then
			table.insert(pending, track)
		end
	end
end
local deadline = os.clock() + 15
for _, track in ipairs(pending) do
	while track.Length == 0 and os.clock() < deadline do
		task.wait()
	end
	preloaded += track.Length > 0 and 1 or 0
end

local names = {}
for name in pairs(rigs) do
	table.insert(names, name)
end
print(("ShotPlayer ready: %d shot(s), %d/%d tracks preloaded, cast: %s"):format(#shotList:GetChildren(), preloaded, #pending, table.concat(names, ", ")))
