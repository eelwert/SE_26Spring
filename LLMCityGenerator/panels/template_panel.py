import bpy

from ..constants import SCENE_TEMPLATES


class CG_Template_Panel(bpy.types.Panel):
    bl_label = "Scene Template"
    bl_idname = "CG_Template_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Setting_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.prop(scene, "city_template_id", text="Template")

        template = SCENE_TEMPLATES.get(scene.city_template_id)
        if template:
            box.label(text=template["label"])
            box.label(text=template["description"])

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.apply_scene_template", text="Apply Template", icon="PRESET")

        obj = context.object
        if not obj or not obj.modifiers.get("City_Generator_2.0"):
            box.label(text="Apply City Generator to an active mesh first.", icon="ERROR")