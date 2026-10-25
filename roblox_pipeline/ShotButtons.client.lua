-- ShotButtons (synced by Rojo into StarterPlayer > StarterPlayerScripts)
-- Control panel for reviewing shots.
--   Click a shot  -> play it          F -> replay selected shot
--   Q / E         -> previous / next shot (and play it)
--   Space         -> pause / resume       Left / Right (or numpad 4 / 6) -> back / forward 1 second
--   Speed button  -> 1x / 0.5x / 0.25x (slow-mo to check details)
--   Loop button   -> loop on/off       Stop -> stop

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local KEY_REPLAY, KEY_PREV, KEY_NEXT = Enum.KeyCode.F, Enum.KeyCode.Q, Enum.KeyCode.E
local SPEEDS = { 1, 0.5, 0.25 }
local IDLE, ACTIVE, ON = Color3.fromRGB(50, 50, 60), Color3.fromRGB(200, 60, 60), Color3.fromRGB(60, 140, 80)

local shotControl = ReplicatedStorage:WaitForChild("ShotControl")
local shotList = ReplicatedStorage:WaitForChild("ShotList")

-- ------------------------------------------------------------------ helpers
local function corner(parent, r)
	Instance.new("UICorner", parent).CornerRadius = UDim.new(0, r)
end

local function makeButton(parent, text, width)
	local b = Instance.new("TextButton")
	b.Size = UDim2.new(width, -4, 0, 30)
	b.BackgroundColor3 = IDLE
	b.TextColor3 = Color3.new(1, 1, 1)
	b.Font = Enum.Font.GothamBold
	b.TextSize = 14
	b.Text = text
	b.Parent = parent
	corner(b, 6)
	return b
end

-- ------------------------------------------------------------------ layout
local gui = Instance.new("ScreenGui")
gui.Name = "ShotButtons"
gui.ResetOnSpawn = false
gui.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.Position = UDim2.fromOffset(16, 16)
panel.Size = UDim2.fromOffset(260, 420)
panel.BackgroundColor3 = Color3.fromRGB(20, 20, 24)
panel.BackgroundTransparency = 0.15
panel.Parent = gui
corner(panel, 8)

local title = Instance.new("TextLabel")
title.Position = UDim2.fromOffset(10, 8)
title.Size = UDim2.new(1, -20, 0, 36)
title.BackgroundTransparency = 1
title.TextColor3 = Color3.fromRGB(210, 210, 220)
title.Font = Enum.Font.Gotham
title.TextSize = 13
title.TextWrapped = true
title.TextXAlignment = Enum.TextXAlignment.Left
title.Text = "Click a shot · F replay · Q/E prev/next"
title.Parent = panel

local sceneButton = Instance.new("TextButton")
sceneButton.Position = UDim2.fromOffset(10, 46)
sceneButton.Size = UDim2.new(1, -20, 0, 34)
sceneButton.BackgroundColor3 = Color3.fromRGB(200, 140, 30)
sceneButton.TextColor3 = Color3.new(1, 1, 1)
sceneButton.Font = Enum.Font.GothamBold
sceneButton.TextSize = 16
sceneButton.Text = "🎬  Play scene  (P)"
sceneButton.Parent = panel
corner(sceneButton, 6)

local controls = Instance.new("Frame")
controls.Position = UDim2.fromOffset(10, 86)
controls.Size = UDim2.new(1, -20, 0, 30)
controls.BackgroundTransparency = 1
controls.Parent = panel
local controlsLayout = Instance.new("UIListLayout", controls)
controlsLayout.FillDirection = Enum.FillDirection.Horizontal
controlsLayout.Padding = UDim.new(0, 4)

local speedButton = makeButton(controls, "Speed 1x", 0.36)
local loopButton = makeButton(controls, "Loop off", 0.34)
local stopButton = makeButton(controls, "Stop", 0.30)

local list = Instance.new("ScrollingFrame")
list.Position = UDim2.fromOffset(10, 124)
list.Size = UDim2.new(1, -20, 1, -134)
list.BackgroundTransparency = 1
list.BorderSizePixel = 0
list.ScrollBarThickness = 6
list.AutomaticCanvasSize = Enum.AutomaticSize.Y
list.CanvasSize = UDim2.new()
list.Parent = panel
local listLayout = Instance.new("UIListLayout", list)
listLayout.Padding = UDim.new(0, 4)
listLayout.SortOrder = Enum.SortOrder.Name   -- buttons are named after shots -> alphabetical

-- ------------------------------------------------------------------ state
local buttons, selected = {}, nil
local speedIndex, looped = 1, false

local function sortedNames()
	local names = {}
	for name in pairs(buttons) do
		table.insert(names, name)
	end
	table.sort(names)
	return names
end

local function play(shotName)
	if not shotName then
		return
	end
	selected = shotName
	for name, button in pairs(buttons) do
		button.BackgroundColor3 = (name == shotName) and ACTIVE or IDLE
	end
	shotControl:FireServer("play", shotName, SPEEDS[speedIndex], looped)
end

local function step(direction)
	local names = sortedNames()
	if #names == 0 then
		return
	end
	local index = table.find(names, selected) or 0
	play(names[(index - 1 + direction) % #names + 1])
end

local function addButton(entry)
	if buttons[entry.Name] then
		return
	end
	local length = entry:GetAttribute("Length") or 0
	local button = makeButton(list, string.format("▶  %s   (%.1fs)", entry.Name, length), 1)
	button.Name = entry.Name
	button.TextXAlignment = Enum.TextXAlignment.Left
	button.TextTruncate = Enum.TextTruncate.AtEnd
	button.Activated:Connect(function()
		play(entry.Name)
	end)
	buttons[entry.Name] = button
end

-- ------------------------------------------------------------------ wiring
speedButton.Activated:Connect(function()
	speedIndex = speedIndex % #SPEEDS + 1
	speedButton.Text = "Speed " .. SPEEDS[speedIndex] .. "x"
	speedButton.BackgroundColor3 = (speedIndex == 1) and IDLE or ON
	play(selected)
end)

loopButton.Activated:Connect(function()
	looped = not looped
	loopButton.Text = looped and "Loop on" or "Loop off"
	loopButton.BackgroundColor3 = looped and ON or IDLE
	play(selected)
end)

stopButton.Activated:Connect(function()
	shotControl:FireServer("stop")
end)

sceneButton.Activated:Connect(function()
	shotControl:FireServer("scene")
end)

shotList.ChildAdded:Connect(addButton)
for _, entry in ipairs(shotList:GetChildren()) do
	addButton(entry)
end

UserInputService.InputBegan:Connect(function(input, typing)
	if typing then
		return
	end
	if input.KeyCode == Enum.KeyCode.P then
		shotControl:FireServer("scene")
	elseif input.KeyCode == KEY_REPLAY then
		play(selected or sortedNames()[1])
	elseif input.KeyCode == KEY_PREV then
		step(-1)
	elseif input.KeyCode == KEY_NEXT then
		step(1)
	elseif input.KeyCode == Enum.KeyCode.Space then
		shotControl:FireServer("transport", "toggle")
	elseif input.KeyCode == Enum.KeyCode.Left or input.KeyCode == Enum.KeyCode.KeypadFour then
		shotControl:FireServer("transport", "back")
	elseif input.KeyCode == Enum.KeyCode.Right or input.KeyCode == Enum.KeyCode.KeypadSix then
		shotControl:FireServer("transport", "fwd")
	end
end)
