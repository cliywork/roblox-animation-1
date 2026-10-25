
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local Scene = require(ReplicatedStorage:WaitForChild("SceneData"))

local function findPart(target)
    local rigName, partName = target:match("^([^%.]+)%.([^%.]+)$")
    local rig = workspace:FindFirstChild(rigName)
    return rig and rig:FindFirstChild(partName)
end

local function resolve(target)
    local rigName, partName = target[1]:match("^([^%.]+)%.([^%.]+)$")
    local off = target[2]
    local rig = workspace:FindFirstChild(rigName)
    local part = rig and rig:FindFirstChild(partName)
    local center = part and part.Position or Vector3.zero
    return center + off
end

local function ease(t)
    t = math.clamp(t, 0, 1)
    return t * t * (3 - 2 * t)
end

local function cameraAt(shot, localT)
    local fc = shot.face
    local head = fc and findPart("IronMan.Head")
    if head then
        local cf = head.CFrame * CFrame.Angles(0, math.rad(fc.yaw or 0), 0) * CFrame.Angles(math.rad(fc.pitch or 0), 0, 0)
        local pos = head.Position + cf.LookVector * (fc.dist or 2.8)
        local view = CFrame.lookAt(pos, head.Position - head.CFrame.UpVector * 0.18, cf.UpVector) * CFrame.Angles(0, 0, math.rad(fc.roll or 0))
        return view, shot.cam[1].fov, "FaceCam"
    end
    local keys = shot.cam
    local k0, k1 = keys[1], keys[1]
    for i, k in ipairs(keys) do
        if k.t <= localT then
            k0, k1 = k, keys[i + 1] or k
        end
    end
    local u = (k1 == k0) and 0 or ease((localT - k0.t) / (k1.t - k0.t))
    local p0, p1 = resolve(k0.pos), resolve(k1.pos)
    local l0, l1 = resolve(k0.look), resolve(k1.look)
    local pos = p0:Lerp(p1, u)
    local look = l0:Lerp(l1, u)
    pos = look + (pos - look) * (Scene.pullback or 1)
    local roll = (k0.roll or 0) + ((k1.roll or 0) - (k0.roll or 0)) * u
    local view = CFrame.lookAt(pos, look)
    if roll ~= 0 then
        view = view * CFrame.Angles(0, 0, math.rad(roll))
    end
    return view, k0.fov + (k1.fov - k0.fov) * u, "Standard"
end

local function getActiveFX(t0, t1)
    local active = {}
    for _, fx in ipairs(Scene.fx) do
        local fx_t = fx.t or fx.t0 or 0
        local fx_t1 = fx.t1 or (fx.t and fx.dur and (fx.t + fx.dur)) or fx_t + 0.5
        if not (fx_t1 < t0 or fx_t > t1) then
            table.insert(active, fx.kind or "effect")
        end
    end
    return active
end

local dump = {}
for i, s in ipairs(Scene.shots) do
    local cf0, fov0, mode0 = cameraAt(s, 0.0)
    local cf1, fov1, mode1 = cameraAt(s, s.dur)
    
    local playList = {}
    for rig, anim in pairs(s.play) do
        table.insert(playList, rig .. " -> " .. anim)
    end
    
    local activeFX = getActiveFX(s.start, s.start + s.dur)
    
    table.insert(dump, {
        cut = i,
        shot = s.shot,
        start = s.start,
        dur = s.dur,
        ["end"] = s.start + s.dur,
        note = s.note,
        hud = s.hud or "none",
        hide = s.hide or "none",
        camMode = mode0,
        play = playList,
        activeFX = activeFX,
        cam_start = {
            pos = { cf0.Position.X, cf0.Position.Y, cf0.Position.Z },
            look = { cf0.LookVector.X, cf0.LookVector.Y, cf0.LookVector.Z },
            fov = fov0,
            target_part = s.cam[1].pos[1],
            target_offset = { s.cam[1].pos[2].X, s.cam[1].pos[2].Y, s.cam[1].pos[2].Z },
            look_part = s.cam[1].look[1],
            look_offset = { s.cam[1].look[2].X, s.cam[1].look[2].Y, s.cam[1].look[2].Z }
        },
        cam_end = {
            pos = { cf1.Position.X, cf1.Position.Y, cf1.Position.Z },
            look = { cf1.LookVector.X, cf1.LookVector.Y, cf1.LookVector.Z },
            fov = fov1,
            target_part = s.cam[#s.cam].pos[1],
            target_offset = { s.cam[#s.cam].pos[2].X, s.cam[#s.cam].pos[2].Y, s.cam[#s.cam].pos[2].Z },
            look_part = s.cam[#s.cam].look[1],
            look_offset = { s.cam[#s.cam].look[2].X, s.cam[#s.cam].look[2].Y, s.cam[#s.cam].look[2].Z }
        }
    })
end

return HttpService:JSONEncode(dump)
