"""UI panel for road layout control."""

import bpy


class CG_PT_Layout_Panel(bpy.types.Panel):
    bl_label = "Road Layout Control"
    bl_idname = "CG_PT_Layout_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Setting_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ---- Manual coordinate input ----
        box = layout.box()
        box.label(text="Point Coordinates", icon="OUTLINER_OB_MESH")
        box.prop(scene, "cg_layout_points_text", text="")
        row = box.row(align=True)
        row.scale_y = 1.3
        row.operator("cg.preview_point_layout", text="Preview", icon="HIDE_OFF")
        row.operator("cg.apply_point_layout", text="Apply", icon="CHECKMARK")

        # ---- Sketch input ----
        box = layout.box()
        box.label(text="Sketch Image", icon="IMAGE_DATA")
        box.prop(scene, "cg_sketch_image_path", text="")
        row = box.row(align=True)
        row.prop(scene, "cg_sketch_threshold", text="Threshold")
        row.prop(scene, "cg_sketch_min_line_length", text="Min Length")
        row = box.row()
        row.scale_y = 1.3
        row.operator("cg.apply_sketch_layout", text="Generate from Sketch", icon="FILE_IMAGE")
