--[[ PrepTerrain_WG01.lua - flatten the terrain under block WG01 before installing it (Studio command bar / MCP).
Block WG01 = Roblox X 1052..1368, Z -824..-452 (inside the sidewalks). The lot surface sits at Y 2.8, terrain must
end at Y 2 (FillBlock to Y 0 -> surface at 2, see roblox-terrain-voxel-gotchas). The drained pool basin needs a hole
down to Y -3.2 at X 1172..1214, Z -598..-562. One undo waypoint.
]]
local CHS = game:GetService("ChangeHistoryService")
local T = workspace.Terrain
CHS:SetWaypoint("WG01 terrain (before)")
local x0, x1, z0, z1 = 1052, 1368, -824, -452
-- clear everything above the lot grade, then refill a flat ground slab
T:FillBlock(CFrame.new((x0 + x1) / 2, 60, (z0 + z1) / 2), Vector3.new(x1 - x0, 116, z1 - z0), Enum.Material.Air)
task.wait()
T:FillBlock(CFrame.new((x0 + x1) / 2, -8, (z0 + z1) / 2), Vector3.new(x1 - x0, 16, z1 - z0), Enum.Material.Ground)
task.wait()
-- pool hole
T:FillBlock(CFrame.new(1193, -1.5, -580), Vector3.new(42, 7, 36), Enum.Material.Air)
CHS:SetWaypoint("WG01 terrain")
print("WG01 terrain flattened to Y 2, pool carved")
