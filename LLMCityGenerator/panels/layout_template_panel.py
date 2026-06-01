import bpy

from ..layout_template_constants import LAYOUT_TEMPLATE_ASSETS


class CG_Layout_Template_Panel(bpy.types.Panel):
    bl_label = "Layout Template"
    bl_idname = "CG_Layout_Template_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Setting_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.prop(scene, "layout_template_id", text="Layout")

        selected = LAYOUT_TEMPLATE_ASSETS.get(scene.layout_template_id)
        if selected:
            box.label(text=selected["label"])
            box.label(text=selected["description"])

        row = box.row(align=True)
        row.prop(scene, "layout_template_rows", text="Rows")
        row.prop(scene, "layout_template_columns", text="Columns")
        box.prop(scene, "layout_template_clear_previous", text="Replace Previous Layout")

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.apply_layout_template", text="Apply Layout Template", icon="MESH_GRID")
