"""RobloxMapDev Blender kit — model in studs, check against an R6 player, export for Roblox Studio.

Convention: while modeling, 1 Blender unit = 1 Roblox stud (Z up, ground at Z=0, +Y = building front).
Standard sizes come from standards/sizes.json (the single source of truth shared with Studio tools).

Run inside Blender (Text Editor ▸ Run Script, or through the MCP execute tool):
    import sys; sys.path.append(r"<repo>/blender"); import rmd_kit as k
    k.setup_scene(); k.make_r6_proxy(); k.make_door(location=(6, 0, 0))
    k.export_fbx(r"<repo>/exports/house_a.fbx", ["HouseA"])
"""
import json
import math
import os

import bpy
import bmesh

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES_PATH = os.path.join(REPO, "standards", "sizes.json")


def sizes():
    """Load standards/sizes.json (studs)."""
    with open(SIZES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ scene
def setup_scene(grid=1.0):
    """Studs-as-units scene (Roblox docs): Unit System None so 1 Blender unit = 1 stud, 1-stud grid."""
    sc = bpy.context.scene
    us = sc.unit_settings
    us.system = sizes()["export"].get("blender_unit_system", "NONE")
    us.scale_length = 1.0
    for area in bpy.context.screen.areas if bpy.context.screen else []:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.overlay.grid_scale = grid
                    sp.clip_end = 20000
    ts = sc.tool_settings
    ts.use_snap = False                     # toggle with Shift+Tab; increment snap = grid
    try:
        ts.snap_elements = {"INCREMENT"}
    except TypeError:
        pass
    coll = bpy.data.collections.get("RMD_Reference") or bpy.data.collections.new("RMD_Reference")
    if coll.name not in sc.collection.children:
        sc.collection.children.link(coll)
    return coll


def _ref_collection():
    return bpy.data.collections.get("RMD_Reference") or setup_scene()


def _box(name, size, center, coll, mat=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    coll.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


def _mat(name, rgba):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = rgba
    m.diffuse_color = rgba
    return m


# ------------------------------------------------------------------ reference objects
def make_r6_proxy(location=(0.0, 0.0, 0.0), name="R6_Proxy"):
    """Blocky R6 character at true stud size: legs 1x1x2, torso 2x1x2, arms 1x1x2, head ~1.25 cube.
    Feet at Z=0, faces -Y (towards a camera looking along +Y). Non-renderable reference, never export."""
    coll = _ref_collection()
    skin, shirt, pants = _mat("RMD_R6_Skin", (0.96, 0.80, 0.41, 1)), _mat("RMD_R6_Shirt", (0.05, 0.41, 0.67, 1)), \
        _mat("RMD_R6_Pants", (0.15, 0.35, 0.10, 1))
    x, y, z = location
    parts = [
        ("LeftLeg", (1, 1, 2), (x - 0.5, y, z + 1.0), pants),
        ("RightLeg", (1, 1, 2), (x + 0.5, y, z + 1.0), pants),
        ("Torso", (2, 1, 2), (x, y, z + 3.0), shirt),
        ("LeftArm", (1, 1, 2), (x - 1.5, y, z + 3.0), skin),
        ("RightArm", (1, 1, 2), (x + 1.5, y, z + 3.0), skin),
        ("Head", (1.25, 1.25, 1.25), (x, y, z + 4.625), skin),   # R6 head mesh ≈1.25 studs; top of head ≈5.25
    ]
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"; root.location = location
    coll.objects.link(root)
    bpy.context.view_layer.update()               # matrix_world is stale until a depsgraph update
    for pn, s, c, m in parts:
        ob = _box(f"{name}_{pn}", s, c, coll, m)
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()
        ob.hide_render = True
        ob["rmd_reference"] = True
    root["rmd_reference"] = True
    return root


def make_door(location=(0.0, 0.0, 0.0), name="Door_Std", with_frame=True):
    """Standard door slab (sizes.json door) standing on Z=0, hinge side at -X, facing ±Y, plus an optional
    frame. Returns (slab, frame)."""
    d = sizes()["openings"]["door"]
    w, h, t = d["width"], d["height"], d["thickness"]
    x, y, z = location
    coll = bpy.context.scene.collection
    slab = _box(name, (w, t, h), (x, y, z + h / 2), coll, _mat("RMD_Door", (0.45, 0.30, 0.18, 1)))
    frame = None
    if with_frame:
        fw = d.get("frame_width", 0.3)
        fm = _mat("RMD_DoorFrame", (0.85, 0.82, 0.75, 1))
        bits = [_box(f"{name}_FrameL", (fw, t + 0.2, h + fw), (x - w / 2 - fw / 2, y, z + (h + fw) / 2), coll, fm),
                _box(f"{name}_FrameR", (fw, t + 0.2, h + fw), (x + w / 2 + fw / 2, y, z + (h + fw) / 2), coll, fm),
                _box(f"{name}_FrameTop", (w, t + 0.2, fw), (x, y, z + h + fw / 2), coll, fm)]
        frame = bits
    return slab, frame


def door_cutter(location=(0.0, 0.0, 0.0), wall_thickness=None, name="Cut_Door"):
    """Box sized to the rough opening (door + frame clearance) for a Boolean DIFFERENCE on a wall."""
    s = sizes()
    d = s["openings"]["door"]
    t = (wall_thickness or s["walls"]["exterior_thickness"]) + 0.2
    ow, oh = d["rough_opening_width"], d["rough_opening_height"]
    x, y, z = location
    ob = _box(name, (ow, t, oh), (x, y, z + oh / 2), bpy.context.scene.collection)
    ob.display_type = "WIRE"; ob.hide_render = True
    return ob


def check_fit(obj_names=None):
    """Print bounding sizes (studs) of the given objects (or selection) next to the standards."""
    bpy.context.view_layer.update()
    obs = [bpy.data.objects[n] for n in obj_names] if obj_names else list(bpy.context.selected_objects)
    out = []
    for ob in obs:
        if ob.type != "MESH":
            continue
        xs, ys, zs = zip(*[(ob.matrix_world @ v.co)[:] for v in ob.data.vertices])
        out.append(f"{ob.name}: W {max(xs) - min(xs):.2f}  D {max(ys) - min(ys):.2f}  H {max(zs) - min(zs):.2f} "
                   f" base Z {min(zs):.2f}  tris {sum(len(p.vertices) - 2 for p in ob.data.polygons)}")
    print("\n".join(out))
    return out


# ------------------------------------------------------------------ export
def export_fbx(path, object_names, apply_modifiers=True):
    """Export the named objects (and their children) as FBX for the Roblox 3D Importer.
    Scale/axes come from sizes.json["export"] so every building is exported the same way.
    Reference objects (R6 proxy, cutters) are never exported."""
    ex = sizes()["export"]
    bpy.ops.object.select_all(action="DESELECT")
    keep = []
    for n in object_names:
        ob = bpy.data.objects[n]
        for o in [ob] + list(ob.children_recursive):
            if o.get("rmd_reference") or o.name.startswith(("R6_Proxy", "Cut_")):
                continue
            o.select_set(True); keep.append(o.name)
    if not keep:
        raise ValueError("nothing to export")
    bpy.context.view_layer.objects.active = bpy.data.objects[keep[0]]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH", "EMPTY"},
        global_scale=ex["fbx_global_scale"], apply_unit_scale=ex["fbx_apply_unit_scale"],
        apply_scale_options=ex["fbx_apply_scale_options"],
        axis_forward=ex["axis_forward"], axis_up=ex["axis_up"],
        use_mesh_modifiers=apply_modifiers, mesh_smooth_type=ex["mesh_smooth_type"],
        use_triangles=ex["triangulate"], add_leaf_bones=False, bake_anim=False, path_mode="COPY",
        embed_textures=False)
    print(f"exported {len(keep)} objects -> {path}")
    return keep
