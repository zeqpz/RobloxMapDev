--[[ InstallBlock.lua - assemble a chopped Westgate block after importing its FBX files (Studio command bar or MCP).

Before running:
  1. 3D Importer (Scale Unit Stud, Insert Using Scene Position ON): exports/westgate/<block>/<BLOCK>_Site.fbx,
     _Plaza.fbx, _TopDog.fbx, _ElSol.fbx, _Motel.fbx  -> Workspace, and <BLOCK>_Protos.fbx -> Workspace.
  2. Paste exports/westgate/<block>/<BLOCK>_Placements.lua into a ModuleScript ServerStorage.<BLOCK>_Placements.
What it does:
  * every imported MeshPart named  <BLOCK>_<Building>.<Piece>__<Material>_<HEX>  goes into
    Workspace.Map.Westgate.<BLOCK>.<Building>.<Piece> (one Model per piece) with Material + Color applied
  * prototype MeshParts  P.<proto>__<Material>_<HEX>  become Models in ServerStorage.<BLOCK>_Protos (pivot at origin)
  * each placement clones its prototype into the right piece at CFrame.new(x, y, z) * CFrame.Angles(0, yaw, 0)
  * collision: walls/slabs/stairs collide (walls with openings use PreciseConvexDecomposition so doorways stay open);
    small decor does not collide and casts no shadow; signs/decals never collide
]]
local BLOCK = "WG01"
local BUILDINGS = {"Site", "Plaza", "TopDog", "ElSol", "Motel"}
local SS = game:GetService("ServerStorage")
local CHS = game:GetService("ChangeHistoryService")

local function parse(name)
	-- "<prefix>.<piece>__<Material>_<HEX>"  or  "<prefix>.<piece>.<proto>__..."
	local left, mat = name:match("^(.-)__(.+)$")
	if not left then return nil end
	local kind, hex = mat:match("^(%a+)_(%x%x%x%x%x%x)$")
	return left, mat, kind, hex
end

local PRECISE = {"Front", "Rear", "Side", "Court", "Back", "End", "Shell", "Office", "Stairs", "Walkways"}
local function precise(piece)
	for _, k in ipairs(PRECISE) do
		if piece:find(k) then return true end
	end
	return false
end

local function apply(mp, mat, kind, hex, piece)
	mp.Anchored = true
	if kind and hex then
		local ok, enum = pcall(function() return Enum.Material[kind] end)
		if ok and enum then mp.Material = enum end
		mp.Color = Color3.fromHex(hex)
		if kind == "Glass" then mp.Transparency = 0.25; mp.Reflectance = 0.05 end
		if kind == "Neon" then mp.CastShadow = false end
	else
		-- Sign_/Decal_ planes keep the imported texture
		mp.CanCollide = false
		mp.CanQuery = false
		mp.CastShadow = false
		return
	end
	local s = mp.Size
	local small = math.max(s.X, s.Y, s.Z) < 3
	if small then
		mp.CanCollide = false
		mp.CastShadow = false
		mp.CollisionFidelity = Enum.CollisionFidelity.Box
	elseif precise(piece) then
		mp.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition
	else
		mp.CollisionFidelity = Enum.CollisionFidelity.Default
	end
end

CHS:SetWaypoint("Install " .. BLOCK .. " (before)")
local mapFolder = workspace:FindFirstChild("Map") or workspace
local wg = mapFolder:FindFirstChild("Westgate") or Instance.new("Folder")
wg.Name = "Westgate"
wg.Parent = mapFolder
local blockModel = wg:FindFirstChild(BLOCK) or Instance.new("Model")
blockModel.Name = BLOCK
blockModel.Parent = wg

local counts = {parts = 0, pieces = 0, clones = 0}
-- 1. building shells -> one Model per piece
for _, b in ipairs(BUILDINGS) do
	local imported = workspace:FindFirstChild(BLOCK .. "_" .. b)
	if imported then
		local bm = blockModel:FindFirstChild(b) or Instance.new("Model")
		bm.Name = b
		bm.Parent = blockModel
		for _, mp in ipairs(imported:GetDescendants()) do
			if mp:IsA("MeshPart") then
				local left, mat, kind, hex = parse(mp.Name)
				if left then
					local piece = left:match("^[^%.]+%.(.+)$") or left
					local pm = bm:FindFirstChild(piece)
					if not pm then
						pm = Instance.new("Model")
						pm.Name = piece
						pm.Parent = bm
						counts.pieces += 1
					end
					apply(mp, mat, kind, hex, piece)
					mp.Name = mat
					mp.Parent = pm
					counts.parts += 1
				end
			end
		end
		imported:Destroy()
	else
		warn("not imported yet: " .. BLOCK .. "_" .. b)
	end
end

-- 2. prototypes -> ServerStorage.<BLOCK>_Protos.<proto> (pivot at the world origin = the prototype's local origin)
local protoFolder = SS:FindFirstChild(BLOCK .. "_Protos") or Instance.new("Folder")
protoFolder.Name = BLOCK .. "_Protos"
protoFolder.Parent = SS
local importedP = workspace:FindFirstChild(BLOCK .. "_Protos")
if importedP then
	for _, mp in ipairs(importedP:GetDescendants()) do
		if mp:IsA("MeshPart") then
			local left, mat, kind, hex = parse(mp.Name)
			local proto = left and left:match("^P%.(.+)$")
			if proto then
				local m = protoFolder:FindFirstChild(proto)
				if not m then
					m = Instance.new("Model")
					m.Name = proto
					m.Parent = protoFolder
				end
				apply(mp, mat, kind, hex, "proto")
				-- door leaves / glass in a prototype must not block the opening's collision test; keep frames solid
				mp.Name = mat
				mp.Parent = m
			end
		end
	end
	for _, m in ipairs(protoFolder:GetChildren()) do
		m.WorldPivot = CFrame.new()
	end
	importedP:Destroy()
end

-- 3. placements
local mod = SS:FindFirstChild(BLOCK .. "_Placements")
if mod then
	local list = require(mod)
	for i, p in ipairs(list) do
		local src = protoFolder:FindFirstChild(p.proto)
		if src then
			local bname, piece = p.piece:match("^" .. BLOCK .. "_([^%.]+)%.(.+)$")
			local bm = blockModel:FindFirstChild(bname or "")
			local pm = bm and bm:FindFirstChild(piece or "")
			if bm and not pm then
				pm = Instance.new("Model")
				pm.Name = piece
				pm.Parent = bm
			end
			local c = src:Clone()
			c:PivotTo(CFrame.new(p.x, p.y, p.z) * CFrame.Angles(0, p.yaw, 0))
			c.Parent = pm or blockModel
			counts.clones += 1
		end
		if i % 50 == 0 then task.wait() end
	end
else
	warn("ServerStorage." .. BLOCK .. "_Placements missing - doors/windows not placed")
end
CHS:SetWaypoint("Install " .. BLOCK)
print(string.format("%s installed: %d parts in %d pieces, %d door/window clones", BLOCK, counts.parts, counts.pieces, counts.clones))
