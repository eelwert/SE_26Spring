import bpy
from .properties import update_parallax_settings


def frame_change_handler(scene):
    update_parallax_settings(scene)


def register_handlers():
    bpy.app.handlers.frame_change_pre.append(frame_change_handler)


def unregister_handlers():
    if frame_change_handler in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(frame_change_handler)
