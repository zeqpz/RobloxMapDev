--[[
	ScaleAudit — paste into Studio's command bar (or run through the Studio MCP execute tool) with a building
	Model selected. Reports every part whose name says what it is (Door*, Window*, Stair*, Rail*, Counter*,
	Wall*) and flags sizes that miss standards/sizes.json, plus mesh triangle-heavy parts and collision on decor.

	Naming convention it relies on (also used by the Blender kit):
	  Door_*  Window_*  Stair_*  Rail_*  Counter_*  WallExt_*  WallInt_*  Decor_* (no collision expected)
]]
local Selection = game:GetService("Selection")
local TOL = 0.15 -- studs

local S = {
	door = { w = 4.6, h = 7.4, t = 0.5 },
	windowSill = 3.0, windowHead = 7.4,
	stairRise = 0.65, stairRun = 1.1,
	rail = 3.3, counter = 3.0,
	wallExt = 1.0, wallInt = 0.5,
}

local function near(a, b) return math.abs(a - b) <= TOL end
local lines, bad = {}, 0
local function report(ok, msg)
	if not ok then bad += 1 end
	table.insert(lines, (ok and "  ok   " or "  FIX  ") .. msg)
end

local model = Selection:Get()[1]
assert(model, "select a building Model first")
local cf, size = model:GetBoundingBox()
local groundY = cf.Position.Y - size.Y / 2
table.insert(lines, ("ScaleAudit %s  bbox %.1f x %.1f x %.1f studs"):format(model:GetFullName(), size.X, size.Y, size.Z))

for _, p in model:GetDescendants() do
	if not p:IsA("BasePart") then continue end
	local n, s = p.Name:lower(), p.Size
	local thin, a, b = math.min(s.X, s.Z), math.max(s.X, s.Z), s.Y
	local bottom = p.Position.Y - s.Y / 2 - groundY
	if n:match("^door") and not n:match("frame") then
		report(near(a, S.door.w) and near(b, S.door.h) and near(thin, S.door.t),
			("%s %.2f x %.2f x %.2f (want 4.6 x 7.4 x 0.5)"):format(p.Name, a, b, thin))
	elseif n:match("^window") and not n:match("frame") then
		local top = bottom + s.Y
		report(near(top % 11, S.windowHead) or near(top, S.windowHead),
			("%s head %.2f above floor (want %.1f), sill %.2f"):format(p.Name, top, S.windowHead, bottom))
	elseif n:match("^stair") then
		report(near(s.Y, S.stairRise) or s.Y <= S.stairRise + TOL, ("%s rise %.2f (max %.2f)"):format(p.Name, s.Y, S.stairRise))
	elseif n:match("^rail") then
		report(near(bottom + s.Y, S.rail), ("%s top %.2f (want %.1f)"):format(p.Name, bottom + s.Y, S.rail))
	elseif n:match("^counter") then
		report(near(bottom + s.Y, S.counter), ("%s top %.2f (want %.1f)"):format(p.Name, bottom + s.Y, S.counter))
	elseif n:match("^wallext") then
		report(near(thin, S.wallExt), ("%s thickness %.2f (want %.1f)"):format(p.Name, thin, S.wallExt))
	elseif n:match("^wallint") then
		report(near(thin, S.wallInt), ("%s thickness %.2f (want %.1f)"):format(p.Name, thin, S.wallInt))
	end
	if n:match("^decor") and (p.CanCollide or p.CanTouch or p.CanQuery) then
		report(false, p.Name .. " is decor but still CanCollide/CanTouch/CanQuery")
	end
	if p:IsA("MeshPart") and p.CollisionFidelity == Enum.CollisionFidelity.PreciseConvexDecomposition and s.Magnitude < 20 then
		report(false, p.Name .. " small mesh using PreciseConvexDecomposition (use Box/Hull)")
	end
end
table.insert(lines, bad == 0 and "PASS" or ("%d issue(s)"):format(bad))
print(table.concat(lines, "\n"))
