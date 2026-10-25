-- Costumes (synced by Rojo into ServerStorage) — dresses the R15 rigs as Thanos and Iron Man.
-- Style: the user's reference images — blocky Roblox characters, but detailed (Mark 50 suit with
-- champagne-gold panels and the triangular reactor; purple Thanos, navy suit, grey-gold collar,
-- grey armoured legs, a big glowing block gauntlet).
-- Called by ShotPlayer before a rig is scaled, so ScaleTo scales the costume with the body.
-- Body parts are recoloured; armour pieces are welded on top, so every animation carries them.
-- Pieces tagged HideInHUD are hidden by the Director in the inside-the-helmet shots.

local Costumes = {}

local function piece(rig, body, name, props, offset, size)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, false, true
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	for k, v in pairs(props) do
		p[k] = v
	end
	if size then
		p.Size = size
	end
	p.CFrame = body.CFrame * (offset or CFrame.new())
	local weld = Instance.new("WeldConstraint")
	weld.Part0, weld.Part1 = body, p
	weld.Parent = p
	p.Parent = rig.Costume
	return p
end

local function paint(part, color, material, reflectance)
	if part then
		part.Color = color
		part.Material = material or Enum.Material.SmoothPlastic
		part.Reflectance = reflectance or 0
		if part:IsA("MeshPart") then
			part.TextureID = ""                                    -- drop the dummy's texture
		end
	end
end

local function tag(inst)
	inst:SetAttribute("HideInHUD", true)
	return inst
end

local function surface(color, material, reflectance, extra)
	local t = { Color = color, Material = material or Enum.Material.SmoothPlastic, Reflectance = reflectance or 0 }
	for k, v in pairs(extra or {}) do
		t[k] = v
	end
	return t
end

local rot = CFrame.Angles

-- ------------------------------------------------------------------ Thanos
local SKIN = Color3.fromRGB(122, 86, 138)
local SKIN_LINE = Color3.fromRGB(84, 56, 98)
local SUIT = Color3.fromRGB(32, 38, 72)
local TRIM = Color3.fromRGB(168, 160, 150)                         -- the grey-silver collar trim
local GOLD = Color3.fromRGB(210, 168, 82)
local GOLD_DARK = Color3.fromRGB(128, 98, 48)
local LEG = Color3.fromRGB(86, 86, 96)
local LEG_DARK = Color3.fromRGB(58, 58, 66)
local STONES = { Color3.fromRGB(70, 130, 255), Color3.fromRGB(235, 45, 45), Color3.fromRGB(160, 70, 240),
	Color3.fromRGB(255, 145, 30), Color3.fromRGB(45, 210, 90), Color3.fromRGB(255, 225, 45) }

function Costumes.Thanos(rig)
	for _, n in ipairs({ "Head", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm", "RightHand" }) do
		paint(rig[n], SKIN)
	end
	paint(rig.UpperTorso, SUIT, Enum.Material.Fabric)
	paint(rig.LowerTorso, SUIT, Enum.Material.Fabric)
	for _, n in ipairs({ "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg" }) do
		paint(rig[n], LEG, Enum.Material.Metal, 0.05)
	end
	paint(rig.LeftFoot, LEG_DARK, Enum.Material.Metal)
	paint(rig.RightFoot, LEG_DARK, Enum.Material.Metal)

	local ut, lt = rig.UpperTorso, rig.LowerTorso
	local gold, trim = surface(GOLD, Enum.Material.Metal, 0.12), surface(TRIM, Enum.Material.Metal, 0.08)
	-- collar: a wide V of silver trim edged in gold from the shoulders to the sternum, a neck band
	for _, side in ipairs({ -1, 1 }) do
		piece(rig, ut, "CollarTrim", trim, CFrame.new(side * 0.42, 0.32, -0.52) * rot(0, 0, -side * math.rad(32)), Vector3.new(0.34, 1.1, 0.05))
		piece(rig, ut, "CollarGold", gold, CFrame.new(side * 0.6, 0.3, -0.535) * rot(0, 0, -side * math.rad(32)), Vector3.new(0.07, 1.05, 0.04))
		piece(rig, ut, "ShoulderTrim", trim, CFrame.new(side * 0.72, 0.76, 0), Vector3.new(0.5, 0.1, 1.04))   -- over the shoulders
	end
	piece(rig, ut, "NeckBand", gold, CFrame.new(0, 0.74, 0), Vector3.new(0.9, 0.14, 1.06))
	-- belt: dark gold band with a buckle plate
	piece(rig, lt, "Belt", surface(GOLD_DARK, Enum.Material.Metal, 0.1), CFrame.new(0, 0.05, 0), Vector3.new(2.06, 0.22, 1.06))
	piece(rig, lt, "Buckle", gold, CFrame.new(0, 0.05, -0.54), Vector3.new(0.5, 0.26, 0.05))
	-- armoured legs: darker knee and shin plates
	for _, n in ipairs({ "LeftLowerLeg", "RightLowerLeg" }) do
		piece(rig, rig[n], "KneePlate", surface(LEG_DARK, Enum.Material.Metal, 0.08), CFrame.new(0, 0.38, -0.52), Vector3.new(0.7, 0.4, 0.06))
		piece(rig, rig[n], "ShinLine", surface(GOLD_DARK, Enum.Material.Metal), CFrame.new(0, -0.15, -0.52), Vector3.new(0.08, 0.6, 0.05))
	end
	-- his ridged chin
	for i = -1, 1 do
		piece(rig, rig.Head, "ChinLine", surface(SKIN_LINE), CFrame.new(i * 0.13, -0.38, -0.605), Vector3.new(0.04, 0.32, 0.03))
	end

	-- the gauntlet: a big gold block glove (as in the reference) with the six stones on the back of
	-- the hand and knuckles, a cuff up the wrist, and their glow lighting the hand
	paint(rig.LeftHand, GOLD, Enum.Material.Metal, 0.15)
	local glove = piece(rig, rig.LeftHand, "Glove", gold, CFrame.new(0, -0.05, 0), Vector3.new(1.22, 0.62, 1.22))
	piece(rig, rig.LeftHand, "Knuckles", surface(GOLD_DARK, Enum.Material.Metal, 0.1), CFrame.new(0, -0.38, 0), Vector3.new(1.12, 0.14, 1.12))
	piece(rig, rig.LeftLowerArm, "Cuff", gold, CFrame.new(0, -0.3, 0), Vector3.new(1.12, 0.5, 1.12))
	piece(rig, rig.LeftLowerArm, "CuffRim", surface(GOLD_DARK, Enum.Material.Metal), CFrame.new(0, -0.04, 0), Vector3.new(1.16, 0.08, 1.16))
	for i, color in ipairs(STONES) do
		-- five across the back of the hand (its -X face), the sixth on the back of the wrist
		local offset = i <= 5 and CFrame.new(-0.62, -0.18, -0.4 + (i - 1) * 0.2) or CFrame.new(-0.57, -0.3, 0)
		local stone = piece(rig, i <= 5 and rig.LeftHand or rig.LeftLowerArm, "Stone",
			surface(color, Enum.Material.Neon, 0, { Shape = Enum.PartType.Ball }), offset, Vector3.one * 0.16)
		if i == 6 then
			stone.Size = Vector3.one * 0.2
		end
	end
	for i, color in ipairs(STONES) do                               -- and a row across the knuckles (front)
		piece(rig, rig.LeftHand, "KnuckleStone", surface(color, Enum.Material.Neon, 0, { Shape = Enum.PartType.Ball }),
			CFrame.new(-0.45 + (i - 1) * 0.18, -0.15, -0.62), Vector3.one * 0.15)
	end
	local glow = Instance.new("PointLight")
	glow.Color, glow.Range, glow.Brightness = Color3.fromRGB(255, 210, 200), 6, 1.6
	glow.Parent = glove
end

-- ------------------------------------------------------------------ Iron Man (Mark 50)
local RED = Color3.fromRGB(150, 18, 26)
local RED_DEEP = Color3.fromRGB(104, 12, 20)
local RED_BRIGHT = Color3.fromRGB(196, 36, 40)
local CHAMPAGNE = Color3.fromRGB(200, 184, 154)                    -- the Mark 50's gold-silver panels
local GUNMETAL = Color3.fromRGB(96, 92, 88)
local GLOW = Color3.fromRGB(190, 230, 255)
local FACE = Color3.fromRGB(205, 160, 128)

function Costumes.IronMan(rig)
	-- smooth paint, not Metal: Metal mirrors the dark Titan surroundings and turns the suit muddy
	local red = surface(RED, Enum.Material.SmoothPlastic, 0.2)
	local deep = surface(RED_DEEP, Enum.Material.SmoothPlastic, 0.15)
	local champ = surface(CHAMPAGNE, Enum.Material.SmoothPlastic, 0.3)
	local gun = surface(GUNMETAL, Enum.Material.SmoothPlastic, 0.15)
	local glow = surface(GLOW, Enum.Material.Neon)

	for _, n in ipairs({ "UpperTorso", "LowerTorso", "LeftLowerArm", "RightLowerArm", "LeftLowerLeg", "RightLowerLeg" }) do
		paint(rig[n], RED, Enum.Material.SmoothPlastic, 0.2)
	end
	for _, n in ipairs({ "LeftUpperArm", "RightUpperArm", "LeftUpperLeg", "RightUpperLeg" }) do
		paint(rig[n], CHAMPAGNE, Enum.Material.SmoothPlastic, 0.3)
	end
	for _, n in ipairs({ "LeftHand", "RightHand", "LeftFoot", "RightFoot" }) do
		paint(rig[n], RED_DEEP, Enum.Material.SmoothPlastic, 0.15)
	end
	paint(rig.Head, FACE)                                          -- Tony's face, seen in the HUD shots

	local ut, lt = rig.UpperTorso, rig.LowerTorso
	-- arc reactor: the Mark 50's inverted triangle, a glowing outline around a bright core
	piece(rig, ut, "ReactorBase", gun, CFrame.new(0, 0.3, -0.515), Vector3.new(0.6, 0.5, 0.04))
	piece(rig, ut, "ReactorTop", glow, CFrame.new(0, 0.48, -0.54), Vector3.new(0.5, 0.07, 0.03))
	for _, side in ipairs({ -1, 1 }) do
		piece(rig, ut, "ReactorSide", glow, CFrame.new(side * 0.13, 0.3, -0.54) * rot(0, 0, side * math.rad(-30)), Vector3.new(0.07, 0.42, 0.03))
	end
	local core = piece(rig, ut, "ReactorCore", glow, CFrame.new(0, 0.36, -0.545), Vector3.new(0.16, 0.14, 0.03))
	local light = Instance.new("PointLight")
	light.Color, light.Range, light.Brightness = Color3.fromRGB(170, 220, 255), 6, 1.6
	light.Parent = core
	-- gunmetal seams sweeping from the chest down to the sides, segmented red abs, blue side lights
	for _, side in ipairs({ -1, 1 }) do
		piece(rig, ut, "Seam", gun, CFrame.new(side * 0.55, -0.1, -0.515) * rot(0, 0, side * math.rad(28)), Vector3.new(0.09, 1.0, 0.04))
		piece(rig, ut, "SideLight", glow, CFrame.new(side * 0.62, -0.5, -0.53), Vector3.new(0.09, 0.09, 0.03))
		piece(rig, ut, "ChestEdge", champ, CFrame.new(side * 1.01, 0.1, 0), Vector3.new(0.05, 0.9, 0.8))
	end
	for k = 0, 3 do
		piece(rig, ut, "Abs", deep, CFrame.new(0, -0.2 - k * 0.15, -0.512), Vector3.new(0.75, 0.035, 0.03))
	end
	piece(rig, ut, "Collar", gun, CFrame.new(0, 0.76, 0), Vector3.new(0.8, 0.1, 0.9))
	piece(rig, lt, "Belt", deep, CFrame.new(0, 0.05, 0), Vector3.new(2.04, 0.2, 1.04))
	-- shoulders / upper arms: champagne with a red band and seam above the elbow
	for _, n in ipairs({ "LeftUpperArm", "RightUpperArm" }) do
		piece(rig, rig[n], "ArmBand", red, CFrame.new(0, -0.32, 0), Vector3.new(1.04, 0.42, 1.04))
		piece(rig, rig[n], "ArmSeam", gun, CFrame.new(0, -0.08, 0), Vector3.new(1.05, 0.05, 1.05))
		piece(rig, rig[n], "ShoulderCap", champ, CFrame.new(0, 0.5, 0), Vector3.new(1.08, 0.2, 1.08))
	end
	-- forearms: champagne inner plates; thighs: panel lines; shins: bright red boot bands
	for _, side in ipairs({ { "LeftLowerArm", 1 }, { "RightLowerArm", -1 } }) do
		piece(rig, rig[side[1]], "ForearmPlate", champ, CFrame.new(side[2] * 0.51, 0.05, 0), Vector3.new(0.05, 0.6, 0.6))
		piece(rig, rig[side[1]], "Cuff", deep, CFrame.new(0, -0.45, 0), Vector3.new(1.04, 0.12, 1.04))
	end
	for _, n in ipairs({ "LeftUpperLeg", "RightUpperLeg" }) do
		for _, side in ipairs({ -1, 1 }) do
			piece(rig, rig[n], "ThighLine", gun, CFrame.new(side * 0.18, 0.05, -0.51) * rot(0, 0, side * math.rad(12)), Vector3.new(0.05, 0.9, 0.03))
		end
		piece(rig, rig[n], "Knee", red, CFrame.new(0, -0.5, 0), Vector3.new(1.04, 0.22, 1.04))
	end
	for _, n in ipairs({ "LeftLowerLeg", "RightLowerLeg" }) do
		piece(rig, rig[n], "BootBand", surface(RED_BRIGHT, Enum.Material.SmoothPlastic, 0.25), CFrame.new(0, -0.45, 0), Vector3.new(1.05, 0.16, 1.05))
		piece(rig, rig[n], "ShinLine", gun, CFrame.new(0, 0.1, -0.51), Vector3.new(0.06, 0.5, 0.03))
	end

	-- helmet: red shell, champagne faceplate with the red widow's peak, angled glowing eyes, jaw
	local head = rig.Head
	tag(piece(rig, head, "HelmetShell", red, CFrame.new(0, 0.03, 0.02), Vector3.new(1.3, 1.32, 1.28)))
	tag(piece(rig, head, "Faceplate", champ, CFrame.new(0, -0.08, -0.65), Vector3.new(0.98, 0.98, 0.05)))
	tag(piece(rig, head, "WidowsPeak", red, CFrame.new(0, 0.42, -0.675) * rot(0, 0, math.rad(45)), Vector3.new(0.42, 0.42, 0.04)))
	tag(piece(rig, head, "Jaw", champ, CFrame.new(0, -0.5, -0.6), Vector3.new(0.7, 0.2, 0.14)))
	tag(piece(rig, head, "Mouth", gun, CFrame.new(0, -0.35, -0.68), Vector3.new(0.34, 0.03, 0.02)))
	for _, side in ipairs({ -1, 1 }) do
		tag(piece(rig, head, "Eye", surface(Color3.fromRGB(240, 248, 255), Enum.Material.Neon),
			CFrame.new(side * 0.22, 0.08, -0.69) * rot(0, 0, side * math.rad(-10)), Vector3.new(0.3, 0.08, 0.02)))
		tag(piece(rig, head, "Cheek", gun, CFrame.new(side * 0.42, -0.2, -0.675) * rot(0, 0, side * math.rad(20)), Vector3.new(0.04, 0.4, 0.02)))
	end
end

function Costumes.dress(rig, name)
	if rig:FindFirstChild("Costume") or not Costumes[name] then
		return
	end
	local folder = Instance.new("Folder")
	folder.Name = "Costume"
	folder.Parent = rig
	Costumes[name](rig)
end

return Costumes
