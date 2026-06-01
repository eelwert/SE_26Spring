import bpy
from .properties import update_parallax_settings


_syncing_added_3d_group_selection = False


def frame_change_handler(scene):
    update_parallax_settings(scene)



def boat_animation_handler(scene):
    """Animate boats along Follow Path constraints — runs after frame change."""
    for obj in bpy.data.objects:
        if obj.get("_boat_use_driver"):
            continue
        if "_boat_start" not in obj.keys():
            continue
        con = None
        for c in obj.constraints:
            if c.type == 'FOLLOW_PATH':
                con = c
                break
        if con is None:
            continue
        start = obj["_boat_start"]
        speed = obj.get("_boat_speed", 250.0)
        if speed <= 0:
            continue
        if con.target and con.target.type == 'CURVE':
            con.target.data.use_path = True
        con.use_fixed_location = True
        con.offset_factor = (start + scene.frame_current / speed) % 1.0


def register_handlers():
    bpy.app.handlers.frame_change_pre.append(frame_change_handler)
    bpy.app.handlers.frame_change_post.append(boat_animation_handler)

def _generated_group_instances(group_id):
    return [
        obj
        for obj in bpy.data.objects
        if obj.get("cg_added_3d_asset_instance") and obj.get("cg_added_3d_group_id") == group_id
    ]


def added_3d_group_selection_handler(scene, depsgraph):
    global _syncing_added_3d_group_selection
    if _syncing_added_3d_group_selection:
        return

    context = bpy.context
    active = context.object
    if active is None or not active.get("cg_added_3d_asset_instance"):
        if getattr(scene, "added_3d_active_group_id", ""):
            scene.added_3d_active_group_id = ""
        return

    group_id = active.get("cg_added_3d_group_id", "")
    if not group_id:
        return

    group_instances = _generated_group_instances(group_id)
    if not group_instances:
        return

    _syncing_added_3d_group_selection = True
    try:
        for obj in bpy.data.objects:
            if obj.get("cg_added_3d_asset_instance"):
                obj.select_set(obj.get("cg_added_3d_group_id") == group_id)
        context.view_layer.objects.active = active

        if scene.added_3d_active_group_id != group_id:
            scene.added_3d_active_group_id = group_id
            scene.added_3d_group_edit_min_count = int(active.get("cg_added_3d_group_min_count", len(group_instances)))
            scene.added_3d_group_edit_max_count = int(active.get("cg_added_3d_group_max_count", len(group_instances)))
            scene.added_3d_group_edit_spacing = float(active.get("cg_added_3d_group_spacing", 5.0))
            scene.added_3d_group_edit_scale = float(active.get("cg_added_3d_group_ui_scale", 1.0))
            scene.added_3d_group_edit_placement_offset = float(active.get("cg_added_3d_group_placement_offset", 0.0))
    finally:
        _syncing_added_3d_group_selection = False


def register_handlers():
    if frame_change_handler not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(frame_change_handler)
    if added_3d_group_selection_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(added_3d_group_selection_handler)


def unregister_handlers():
    if frame_change_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(frame_change_handler)
    if boat_animation_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(boat_animation_handler)
    if added_3d_group_selection_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(added_3d_group_selection_handler)
