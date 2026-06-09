"""Blender Operators for controlled building placement / movement / deletion.

All operators use cg.* bl_idname prefix and CG_OT_ class prefix following the
project convention. Each operator reads its inputs from dedicated operator
properties (self.*) so they can be called programmatically via bpy.ops.cg.*().

Placement creates a single-face mesh with City_Generator_2.0 modifier, so each
controlled building appears as a miniature CG city block visually consistent
with the rest of the scene.
"""

import bpy
from bpy.props import StringProperty, FloatProperty


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COLLECTION_NAME = "CG_Controlled_Buildings"
NODE_GROUP_NAME = "City_Generator_2.0"
ASSETS_COLLECTION_NAME = "City_Gen_2.0_Assets"


def _get_or_create_collection():
    """Return the CG_Controlled_Buildings collection, creating it if needed."""
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
        bpy.context.scene.collection.children.link(coll)
    return coll


def _write_props(obj, building_id, width, depth, height, color):
    """Write all cg.* custom properties onto a building object."""
    obj["cg.is_controlled_building"] = True
    obj["cg.building_id"] = str(building_id)
    obj["cg.building_width"] = float(width)
    obj["cg.building_depth"] = float(depth)
    obj["cg.building_height"] = float(height)
    obj["cg.building_color"] = str(color) if color else ""


def _ensure_editmode_off():
    """Switch to OBJECT mode if currently in EDIT mode."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def _next_id():
    """Generate the next building ID and increment the persistent counter."""
    scene = bpy.context.scene
    try:
        counter = scene.cg_building_counter
    except (AttributeError, TypeError):
        counter = 0
    counter += 1
    scene.cg_building_counter = counter
    return f"B_{counter:04d}"


# ---------------------------------------------------------------------------
# CG resource helpers
# ---------------------------------------------------------------------------

def _ensure_cg_resources():
    """Ensure City_Generator_2.0 NodeTree and assets Collection are imported.

    Follows the same import pattern as CG_OT_Apply_Node_Group in
    operators/import_apply.py.  Idempotent — safe to call repeatedly.
    """
    from ..utils import append_data, find_layer_collection

    # NodeTree
    if NODE_GROUP_NAME not in bpy.data.node_groups:
        append_data("NodeTree", NODE_GROUP_NAME)

    # Assets collection
    if ASSETS_COLLECTION_NAME not in bpy.data.collections:
        append_data("Collection", ASSETS_COLLECTION_NAME)
    coll = bpy.data.collections.get(ASSETS_COLLECTION_NAME)
    if coll and coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)

    # Hide assets from viewport
    lc = find_layer_collection(
        bpy.context.view_layer.layer_collection, ASSETS_COLLECTION_NAME,
    )
    if lc:
        lc.exclude = True


def _create_single_face_mesh(mesh_name, width, depth, height):
    """Create a single-quad-face mesh data-block.

    The face is a width×depth rectangle centred at origin, on the Z=0 plane.
    Face attributes are initialised so the CG modifier produces one building.

    Returns the new Mesh datablock.
    """
    hw = width * 0.5
    hd = depth * 0.5

    vertices = (
        (-hw, -hd, 0.0),
        ( hw, -hd, 0.0),
        (-hw,  hd, 0.0),
        ( hw,  hd, 0.0),
    )
    faces = ((0, 1, 3, 2),)

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # --- Face attributes (same set as _ensure_default_face_attributes) ---
    defaults_int = {
        "assign Park": 0,
        "Delete Building": 0,
        "modern building": 0,
        "low poly": 0,
    }
    for attr_name, default_val in defaults_int.items():
        if attr_name not in mesh.attributes:
            mesh.attributes.new(name=attr_name, type="INT", domain="FACE")
        for item in mesh.attributes[attr_name].data:
            item.value = default_val

    # Custom_Height — the key attribute for building height
    if "Custom_Height" not in mesh.attributes:
        mesh.attributes.new(name="Custom_Height", type="INT", domain="FACE")
    for item in mesh.attributes["Custom_Height"].data:
        item.value = int(height)

    return mesh


def _add_cg_modifier(obj):
    """Attach the City_Generator_2.0 Geometry Nodes modifier to *obj*."""
    mod = obj.modifiers.new(type='NODES', name=NODE_GROUP_NAME)
    mod.node_group = bpy.data.node_groups.get(NODE_GROUP_NAME)
    return mod


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class CG_OT_PlaceBuilding(bpy.types.Operator):
    """Place a new controlled CG block at the specified XY position.

    Creates a single-face mesh with City_Generator_2.0 modifier, so the
    building blends seamlessly with the rest of the city scene.
    """
    bl_idname = "cg.place_building"
    bl_label = "Place Controlled Block"
    bl_description = "Create a controlled CG city block at the given coordinates"
    bl_options = {"REGISTER", "UNDO"}

    x: FloatProperty(
        name="X", description="Center X coordinate",
        default=0.0, subtype='DISTANCE',
    )
    y: FloatProperty(
        name="Y", description="Center Y coordinate",
        default=0.0, subtype='DISTANCE',
    )
    width: FloatProperty(
        name="Width", description="Block width along X (m)",
        default=10.0, min=1.0, max=500.0, subtype='DISTANCE',
    )
    depth: FloatProperty(
        name="Depth", description="Block depth along Y (m)",
        default=10.0, min=1.0, max=500.0, subtype='DISTANCE',
    )
    height: FloatProperty(
        name="Height", description="Building height (sets Custom_Height face attribute)",
        default=20.0, min=1.0, max=1000.0, subtype='DISTANCE',
    )
    color: StringProperty(
        name="Color", description="Reserved for future use (CG controls appearance via modifier)",
        default="",
    )

    def execute(self, context):
        from .building_registry import BuildingRegistry

        _ensure_editmode_off()

        # 1. Overlap check
        registry = BuildingRegistry.instance()
        conflict = registry.check_overlap(self.x, self.y, self.width, self.depth)
        if conflict is not None:
            self.report(
                {'WARNING'},
                f"位置 ({self.x:.1f}, {self.y:.1f}) 与区块 {conflict} 重叠，放置已取消",
            )
            return {'CANCELLED'}

        # 2. Ensure CG resources (NodeTree + Assets) are available
        building_id = _next_id()
        try:
            _ensure_cg_resources()
        except Exception as exc:
            self.report({'ERROR'}, f"无法导入 City Generator 资源: {exc}")
            return {'CANCELLED'}

        # 3. Create single-face mesh data-block
        mesh_name = f"CG_Block_{building_id}_Mesh"
        mesh = _create_single_face_mesh(mesh_name, self.width, self.depth, self.height)

        # 4. Create object, set location, link to scene
        obj = bpy.data.objects.new(f"CG_Block_{building_id}", mesh)
        obj.location = (self.x, self.y, 0.0)
        context.scene.collection.objects.link(obj)

        # 5. Attach CG modifier
        try:
            _add_cg_modifier(obj)
        except Exception as exc:
            # Clean up on failure
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
            self.report({'ERROR'}, f"无法挂载 City Generator 修改器: {exc}")
            return {'CANCELLED'}

        # 6. Write custom properties
        _write_props(obj, building_id, self.width, self.depth, self.height, self.color)

        # 7. Move to controlled-buildings collection
        coll = _get_or_create_collection()
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        coll.objects.link(obj)

        # 8. Register in spatial index
        registry.register(
            building_id, obj.name,
            self.x, self.y, self.width, self.depth, self.height,
            self.color,
        )

        # 9. Ensure it's the active object (CG modifier depends on this)
        context.view_layer.objects.active = obj

        self.report(
            {'INFO'},
            f"CG 区块 {building_id} 已放置在 ({self.x:.1f}, {self.y:.1f})，"
            f"尺寸 {self.width:.1f}x{self.depth:.1f}m，高度 {self.height:.0f}m",
        )
        return {'FINISHED'}


class CG_OT_MoveBuilding(bpy.types.Operator):
    """Move an existing controlled building to new XY coordinates."""
    bl_idname = "cg.move_building"
    bl_label = "Move Controlled Building"
    bl_description = "Move a controlled building to new coordinates"
    bl_options = {"REGISTER", "UNDO"}

    building_id: StringProperty(
        name="Building ID", description="ID of the building to move (e.g. B_0001)",
        default="",
    )
    x: FloatProperty(
        name="X", description="New center X coordinate",
        default=0.0, subtype='DISTANCE',
    )
    y: FloatProperty(
        name="Y", description="New center Y coordinate",
        default=0.0, subtype='DISTANCE',
    )

    def execute(self, context):
        from .building_registry import BuildingRegistry

        if not self.building_id:
            self.report({'ERROR'}, "building_id 不能为空")
            return {'CANCELLED'}

        registry = BuildingRegistry.instance()

        # 1. Look up record
        record = registry.get(self.building_id)
        if record is None:
            self.report({'ERROR'}, f"未找到建筑 {self.building_id}")
            return {'CANCELLED'}

        # 2. Check overlap at new position (exclude self)
        conflict = registry.check_overlap(
            self.x, self.y, record.width, record.depth, exclude_id=self.building_id,
        )
        if conflict is not None:
            self.report(
                {'WARNING'},
                f"目标位置 ({self.x:.1f}, {self.y:.1f}) 与区块 {conflict} 重叠，移动已取消",
            )
            return {'CANCELLED'}

        # 3. Find Blender object and move it
        obj = bpy.data.objects.get(record.obj_name)
        if obj is None:
            self.report({'ERROR'}, f"Blender 对象 {record.obj_name} 不存在")
            return {'CANCELLED'}

        obj.location.x = self.x
        obj.location.y = self.y

        # 4. Update registry
        registry.move(self.building_id, self.x, self.y)

        self.report(
            {'INFO'},
            f"区块 {self.building_id} 已移动到 ({self.x:.1f}, {self.y:.1f})",
        )
        return {'FINISHED'}


class CG_OT_DeleteBuilding(bpy.types.Operator):
    """Delete a controlled building and free its occupied space."""
    bl_idname = "cg.delete_building"
    bl_label = "Delete Controlled Building"
    bl_description = "Delete a controlled building by its ID"
    bl_options = {"REGISTER", "UNDO"}

    building_id: StringProperty(
        name="Building ID", description="ID of the building to delete (e.g. B_0001)",
        default="",
    )

    def execute(self, context):
        from .building_registry import BuildingRegistry

        if not self.building_id:
            self.report({'ERROR'}, "building_id 不能为空")
            return {'CANCELLED'}

        registry = BuildingRegistry.instance()

        # 1. Look up record
        record = registry.get(self.building_id)
        if record is None:
            self.report({'ERROR'}, f"未找到建筑 {self.building_id}")
            return {'CANCELLED'}

        # 2. Remove Blender object + mesh data
        obj = bpy.data.objects.get(record.obj_name)
        if obj is not None:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh and mesh.users == 0 and not mesh.use_fake_user:
                bpy.data.meshes.remove(mesh)

        # 3. Unregister
        registry.unregister(self.building_id)

        self.report({'INFO'}, f"CG 区块 {self.building_id} 已删除")
        return {'FINISHED'}
