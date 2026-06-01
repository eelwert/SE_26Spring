import bpy
from .properties import update_parallax_settings


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


def unregister_handlers():
    if frame_change_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(frame_change_handler)
    if boat_animation_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(boat_animation_handler)
