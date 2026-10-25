-- titan_set.lua — builds the Titan battlefield in the open place (run in EDIT mode, e.g. via the
-- Studio MCP execute_luau or the command bar). Not synced by Rojo: it writes Terrain, Lighting and
-- Workspace.TitanSet, which are saved with the place. Re-running rebuilds everything the same way
-- (fixed seeds). The original Lighting is kept in Workspace.TitanSet.OriginalLighting.
--
-- Stage (see scene.py): Thanos on the origin facing -Z, Iron Man's mark 40 studs away at z = -40.
-- The fight runs along that line, so a corridor around it stays flat (feet land on y = 0) and
-- clear of anything taller than pebbles; rocks, wreckage and haze fill everything around it.

local Lighting = game:GetService("Lighting")
local terrain = workspace.Terrain

local GROUND = 0                                   -- top of the terrain fill
local SURFACE = 1.95                               -- where that surface actually renders (voxel smoothing);
                                                   -- = STAGE_Y in scene.py, the rigs stand on it
local CORRIDOR = { x = 16, z0 = -62, z1 = 22 }    -- kept flat and clear
local RADIUS = 300                                  -- half size of the built area

local function inCorridor(x, z, margin)
	margin = margin or 0
	return math.abs(x) < CORRIDOR.x + margin and z > CORRIDOR.z0 - margin and z < CORRIDOR.z1 + margin
end

-- ------------------------------------------------------------------ reset
local old = workspace:FindFirstChild("TitanSet")
local originalLighting = old and old:FindFirstChild("OriginalLighting") and old.OriginalLighting.Value
if old then
	old:Destroy()
end
terrain:Clear()

local set = Instance.new("Folder")
set.Name = "TitanSet"

-- remember the place's own lighting once, so the set can be removed cleanly later
local saved = Instance.new("StringValue")
saved.Name = "OriginalLighting"
saved.Value = originalLighting or game:GetService("HttpService"):JSONEncode({
	ClockTime = Lighting.ClockTime, Brightness = Lighting.Brightness,
	Ambient = { Lighting.Ambient.R, Lighting.Ambient.G, Lighting.Ambient.B },
	OutdoorAmbient = { Lighting.OutdoorAmbient.R, Lighting.OutdoorAmbient.G, Lighting.OutdoorAmbient.B },
})
saved.Parent = set

local baseplate = workspace:FindFirstChild("Baseplate")
if baseplate then
	baseplate.Transparency = 1                      -- still collides; the terrain is what you see
	for _, t in ipairs(baseplate:GetChildren()) do
		if t:IsA("Texture") or t:IsA("Decal") then
			t.Transparency = 1
		end
	end
end

-- ------------------------------------------------------------------ terrain
for material, color in pairs({
	[Enum.Material.Rock] = Color3.fromRGB(80, 65, 53), [Enum.Material.Basalt] = Color3.fromRGB(66, 55, 46),
	[Enum.Material.Ground] = Color3.fromRGB(96, 77, 60), [Enum.Material.Slate] = Color3.fromRGB(82, 69, 58),
	[Enum.Material.Sand] = Color3.fromRGB(110, 90, 70), [Enum.Material.Mud] = Color3.fromRGB(74, 59, 48),
	[Enum.Material.Cobblestone] = Color3.fromRGB(76, 64, 54),
}) do
	terrain:SetMaterialColor(material, color)
end

-- flat cracked bedrock everywhere, top exactly at GROUND
terrain:FillBlock(CFrame.new(0, GROUND - 8, 0), Vector3.new(RADIUS * 2, 16, RADIUS * 2), Enum.Material.Basalt)
task.wait()

local rng = Random.new(1972)
local groundMats = { Enum.Material.Rock, Enum.Material.Ground, Enum.Material.Slate, Enum.Material.Mud, Enum.Material.Cobblestone }

-- material patches at the same height: the ground reads as broken slabs and dust, not one colour
for i = 1, 260 do
	local x, z = rng:NextNumber(-RADIUS, RADIUS), rng:NextNumber(-RADIUS, RADIUS)
	local size = Vector3.new(rng:NextNumber(6, 30), 4, rng:NextNumber(6, 30))
	terrain:FillBlock(CFrame.new(x, GROUND - 2, z) * CFrame.Angles(0, rng:NextNumber(0, math.pi), 0), size,
		groundMats[rng:NextInteger(1, #groundMats)])
	if i % 40 == 0 then
		task.wait()
	end
end

-- slab ledges: thin raised plates of rock, low near the corridor, the cracked-ground layers of the movie
for i = 1, 140 do
	local x, z = rng:NextNumber(-RADIUS, RADIUS), rng:NextNumber(-RADIUS, RADIUS)
	if not inCorridor(x, z, 2) then
		local h = math.min(rng:NextNumber(0.8, 3), 0.5 + (Vector3.new(x, 0, z).Magnitude / 40))
		terrain:FillBlock(CFrame.new(x, GROUND + h / 2 - 1, z) * CFrame.Angles(rng:NextNumber(-0.08, 0.08), rng:NextNumber(0, math.pi), rng:NextNumber(-0.08, 0.08)),
			Vector3.new(rng:NextNumber(8, 26), h + 2, rng:NextNumber(6, 18)), rng:NextNumber() < 0.5 and Enum.Material.Slate or Enum.Material.Rock)
	end
	if i % 35 == 0 then
		task.wait()
	end
end

-- rubble mounds (movie 185: Thanos driven back up a rubble slope behind his mark)
local function mound(x, z, r, height, material)
	terrain:FillBall(Vector3.new(x, GROUND + height - r, z), r, material)
end
mound(4, 34, 14, 4.5, Enum.Material.Rock)
mound(-14, 40, 12, 5, Enum.Material.Ground)
mound(18, 46, 16, 6, Enum.Material.Rock)
for i = 1, 70 do
	local a, d = rng:NextNumber(0, math.pi * 2), rng:NextNumber(45, RADIUS - 20)
	local x, z = math.cos(a) * d, math.sin(a) * d - 20
	if not inCorridor(x, z, 10) then
		local r = rng:NextNumber(8, 22) * (0.6 + d / RADIUS)
		mound(x, z, r, r * rng:NextNumber(0.25, 0.55), rng:NextNumber() < 0.6 and Enum.Material.Rock or Enum.Material.Ground)
	end
	if i % 20 == 0 then
		task.wait()
	end
end

-- boulders: half-sunk rocks, small ones close to the corridor, big ones further out
for i = 1, 420 do
	local x, z = rng:NextNumber(-RADIUS * 0.8, RADIUS * 0.8), rng:NextNumber(-RADIUS * 0.8, RADIUS * 0.8)
	if not inCorridor(x, z, 1) then
		local d = math.max(math.abs(x) - CORRIDOR.x, 0) + math.max(CORRIDOR.z0 - z, z - CORRIDOR.z1, 0)
		local r = rng:NextNumber(0.8, 1.6) + math.min(d / 25, 4) * rng:NextNumber()
		terrain:FillBall(Vector3.new(x, GROUND + r * rng:NextNumber(-0.2, 0.4), z), r,
			rng:NextNumber() < 0.7 and Enum.Material.Rock or Enum.Material.Slate)
	end
	if i % 60 == 0 then
		task.wait()
	end
end

-- far cliffs and spires: the horizon of broken rock the haze fades into
for i = 1, 26 do
	local a = (i / 26) * math.pi * 2 + rng:NextNumber(-0.1, 0.1)
	local d = rng:NextNumber(200, 270)
	local h = rng:NextNumber(25, 70)
	terrain:FillBlock(CFrame.new(math.cos(a) * d, GROUND + h / 2 - 4, math.sin(a) * d) * CFrame.Angles(rng:NextNumber(-0.25, 0.25), a, rng:NextNumber(-0.3, 0.3)),
		Vector3.new(rng:NextNumber(30, 70), h, rng:NextNumber(14, 30)), Enum.Material.Slate)
	if i % 8 == 0 then
		task.wait()
	end
end

-- Terrain renders its surface ~2 studs above a fill's top, unevenly where fills overlap. The stage
-- is rewritten voxel by voxel (full below GROUND, empty above, materials kept) so the surface along
-- the fight line is a steady SURFACE (measured 1.93-2.0 at x = 0), which is where the rigs stand.
do
	local region = Region3.new(Vector3.new(-CORRIDOR.x - 8, GROUND - 8, CORRIDOR.z0 - 4),
		Vector3.new(CORRIDOR.x + 8, GROUND + 8, CORRIDOR.z1)):ExpandToGrid(4)
	local mats, occ = terrain:ReadVoxels(region, 4)
	local size = mats.Size
	for x = 1, size.X do
		for z = 1, size.Z do
			local floor = Enum.Material.Basalt
			for y = 1, size.Y do
				local center = region.CFrame.Position.Y - region.Size.Y / 2 + (y - 0.5) * 4
				if center < GROUND then
					if mats[x][y][z] ~= Enum.Material.Air then
						floor = mats[x][y][z]
					end
					mats[x][y][z], occ[x][y][z] = floor, 1
				else
					mats[x][y][z], occ[x][y][z] = Enum.Material.Air, 0
				end
			end
		end
	end
	terrain:WriteVoxels(region, 4, mats, occ)
	task.wait()
end

-- ------------------------------------------------------------------ parts
local RUST = { Color3.fromRGB(50, 39, 33), Color3.fromRGB(42, 36, 32), Color3.fromRGB(60, 45, 35), Color3.fromRGB(33, 30, 29) }

local function part(parent, props)
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CastShadow, p.TopSurface, p.BottomSurface = true, false, true, Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	p.Material = rng:NextNumber() < 0.5 and Enum.Material.CorrodedMetal or Enum.Material.Metal   -- plain metal tones down the orange rust texture
	p.Color = RUST[rng:NextInteger(1, #RUST)]
	for k, v in pairs(props) do
		p[k] = v
	end
	p.Parent = parent
	return p
end

local function tilt(maxRad)
	return CFrame.Angles(rng:NextNumber(-maxRad, maxRad), rng:NextNumber(0, math.pi * 2), rng:NextNumber(-maxRad, maxRad))
end

-- a heap of wreckage: bent girders, torn plates, a ladder truss and pipes, half buried
local function wreck(parent, x, z, scale)
	local m = Instance.new("Model")
	m.Name = "Wreck"
	local base = CFrame.new(x, SURFACE - 0.3, z)
	for _ = 1, rng:NextInteger(3, 6) do                             -- girders
		local len = rng:NextNumber(6, 16) * scale
		part(m, { Size = Vector3.new(0.6, 0.6, len) * math.sqrt(scale), CFrame = base * CFrame.new(rng:NextNumber(-4, 4) * scale, len * 0.15, rng:NextNumber(-4, 4) * scale) * tilt(0.9) })
	end
	for _ = 1, rng:NextInteger(1, 3) do                             -- plates
		part(m, { Size = Vector3.new(rng:NextNumber(4, 9), 0.35, rng:NextNumber(3, 7)) * scale,
			CFrame = base * CFrame.new(rng:NextNumber(-3, 3) * scale, 1.2 * scale, rng:NextNumber(-3, 3) * scale) * tilt(1.1), Material = Enum.Material.DiamondPlate })
	end
	if rng:NextNumber() < 0.6 then                                  -- ladder truss
		local len, cf = rng:NextNumber(8, 14) * scale, base * CFrame.new(rng:NextNumber(-3, 3) * scale, 2 * scale, 0) * tilt(0.7)
		for _, side in ipairs({ -0.9, 0.9 }) do
			part(m, { Size = Vector3.new(0.3, 0.3, len), CFrame = cf * CFrame.new(side * scale, 0, 0) })
		end
		for k = 0, math.floor(len / 1.6) do
			part(m, { Size = Vector3.new(1.8 * scale, 0.2, 0.2), CFrame = cf * CFrame.new(0, 0, -len / 2 + k * 1.6) })
		end
	end
	for _ = 1, rng:NextInteger(0, 3) do                             -- pipes
		local len = rng:NextNumber(4, 10) * scale
		part(m, { Shape = Enum.PartType.Cylinder, Size = Vector3.new(len, 0.7 * scale, 0.7 * scale),
			CFrame = base * CFrame.new(rng:NextNumber(-4, 4) * scale, 0.4 * scale, rng:NextNumber(-4, 4) * scale) * tilt(0.4) })
	end
	m.Parent = parent
end

local wreckage = Instance.new("Folder")
wreckage.Name = "Wreckage"
wreckage.Parent = set
for i = 1, 70 do
	local x, z
	repeat
		x, z = rng:NextNumber(-170, 170), rng:NextNumber(-190, 150)
	until not inCorridor(x, z, 4)
	wreck(wreckage, x, z, rng:NextNumber(0.7, 1.5) * (1 + Vector3.new(x, 0, z).Magnitude / 160))
	if i % 10 == 0 then
		task.wait()
	end
end

-- towers: tall blocky ruins with pipes (movie 185 has one behind Thanos' rubble slope)
local towers = Instance.new("Folder")
towers.Name = "Towers"
towers.Parent = set
local function tower(x, z, h)
	local m = Instance.new("Model")
	m.Name = "Tower"
	local y = SURFACE - 1
	local w = rng:NextNumber(7, 11)
	while y < h do
		local bh = rng:NextNumber(3, 7)
		part(m, { Size = Vector3.new(w, bh, w * rng:NextNumber(0.7, 1.1)), CFrame = CFrame.new(x + rng:NextNumber(-0.8, 0.8), y + bh / 2, z) * CFrame.Angles(0, rng:NextNumber(-0.15, 0.15), rng:NextNumber(-0.04, 0.04)),
			Material = Enum.Material.Slate, Color = Color3.fromRGB(70, 60, 52) })
		y += bh
		w *= rng:NextNumber(0.8, 0.97)
	end
	for _ = 1, 4 do
		local len = rng:NextNumber(6, 14)
		part(m, { Shape = Enum.PartType.Cylinder, Size = Vector3.new(len, 0.8, 0.8),
			CFrame = CFrame.new(x + rng:NextNumber(-5, 5), rng:NextNumber(h * 0.4, h), z + rng:NextNumber(-5, 5)) * tilt(0.8) })
	end
	m.Parent = towers
end
tower(-6, 78, 26)
tower(30, 96, 20)
tower(-38, -96, 22)
tower(42, -120, 30)
tower(-70, 40, 18)

-- giant wreck plates in the haze: the huge dark tilted shapes on the horizon
local giants = Instance.new("Folder")
giants.Name = "GiantWreck"
giants.Parent = set
for _, g in ipairs({
	{ 120, 150, 0.5, 140, 18, 50, 0.6 }, { -150, 120, -0.6, 160, 22, 44, -0.5 }, { 60, -230, 0.2, 180, 16, 60, 0.4 },
	{ -190, -150, 0.7, 120, 20, 40, -0.7 }, { 210, -40, -0.3, 150, 18, 46, 0.5 }, { -60, 240, 0.1, 200, 24, 50, 0.3 },
}) do
	part(giants, { Size = Vector3.new(g[4], g[5], g[6]), CFrame = CFrame.new(g[1], GROUND + g[4] * 0.25, g[2]) * CFrame.Angles(0, g[3], g[7]),
		Material = Enum.Material.Slate, Color = Color3.fromRGB(48, 40, 36), CastShadow = false })
end

-- floating debris: rocks hanging in the sky (Titan's gravity is broken after the moon falls)
local debris = Instance.new("Folder")
debris.Name = "FloatingDebris"
debris.Parent = set
for i = 1, 140 do
	local a, d = rng:NextNumber(0, math.pi * 2), rng:NextNumber(30, 240)
	local s = rng:NextNumber(0.25, 1.1) * (1 + d / 150)
	part(debris, { Size = Vector3.new(s, s * rng:NextNumber(0.3, 0.7), s * rng:NextNumber(0.5, 1.4)),
		CFrame = CFrame.new(math.cos(a) * d, rng:NextNumber(18, 30) + d * rng:NextNumber(0.1, 0.45), math.sin(a) * d - 20) * tilt(math.pi),
		Material = Enum.Material.Slate, Color = Color3.fromRGB(44, 38, 34), CastShadow = false })
	if i % 80 == 0 then
		task.wait()
	end
end

-- small rubble inside the corridor: pebbles only, so feet and cameras stay clear
local rubble = Instance.new("Folder")
rubble.Name = "Rubble"
rubble.Parent = set
for _ = 1, 120 do
	local x, z = rng:NextNumber(-CORRIDOR.x, CORRIDOR.x), rng:NextNumber(CORRIDOR.z0, CORRIDOR.z1)
	if math.abs(x) > 3 then                                         -- keep the fight line itself clean
		local s = rng:NextNumber(0.25, 0.8)
		part(rubble, { Size = Vector3.new(s, s * 0.6, s * rng:NextNumber(0.8, 1.4)), CFrame = CFrame.new(x, SURFACE + s * 0.15, z) * tilt(0.6),
			Material = Enum.Material.Slate, Color = Color3.fromRGB(58, 49, 42) })
	end
end

set.Parent = workspace

-- ------------------------------------------------------------------ sky and light
-- low warm sun behind dust: dark ground, bright hazy sky, everything desaturated
Lighting.ClockTime = 17.3
Lighting.GeographicLatitude = 20
Lighting.Brightness = 2.4
Lighting.Ambient = Color3.fromRGB(42, 33, 27)
Lighting.OutdoorAmbient = Color3.fromRGB(140, 116, 92)   -- sky fill: what lifts the characters' shadowed fronts
Lighting.ColorShift_Top = Color3.fromRGB(255, 205, 150)
Lighting.ColorShift_Bottom = Color3.fromRGB(60, 45, 35)
Lighting.EnvironmentDiffuseScale = 0.8      -- metals (gold, trim) need the sky's reflection to read
Lighting.EnvironmentSpecularScale = 1
Lighting.ExposureCompensation = -0.35

local function effect(class, name)
	local e = Lighting:FindFirstChild(name) or Instance.new(class)
	e.Name = name
	e.Parent = Lighting
	return e
end

local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere") or effect("Atmosphere", "Atmosphere")
atmosphere.Density, atmosphere.Offset, atmosphere.Haze, atmosphere.Glare = 0.47, 0.12, 2.8, 0.45
atmosphere.Color, atmosphere.Decay = Color3.fromRGB(196, 156, 110), Color3.fromRGB(96, 72, 48)

local sky = Lighting:FindFirstChildOfClass("Sky")
if sky then
	sky.SunAngularSize, sky.MoonAngularSize, sky.StarCount = 16, 0, 0
end

local rays = Lighting:FindFirstChildOfClass("SunRaysEffect")
if rays then
	rays.Intensity, rays.Spread = 0.08, 0.6
end

local grade = effect("ColorCorrectionEffect", "TitanGrade")
grade.TintColor, grade.Saturation, grade.Contrast, grade.Brightness = Color3.fromRGB(255, 234, 208), -0.28, 0.12, -0.02

return ("TitanSet built: %d parts, %d terrain cells"):format(#set:GetDescendants(), terrain:CountCells())
