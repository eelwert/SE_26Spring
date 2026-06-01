# dA_5_add
import bpy

from ..constants import CITY_3D_ASSETS
from ..furniture_asset_engine import selected_added_3d_group


# dA_5_add
class CG_Added_3D_Assets_Panel(bpy.types.Panel):
    bl_label = "Added 3D Assets"
    bl_idname = "CG_Added_3D_Assets_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Setting_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        selected_group = selected_added_3d_group(context)
        if selected_group:
            box.label(text="Adjust Selected Asset Group", icon="GROUP")
            box.label(text=selected_group["asset_name"])
            row = box.row(align=True)
            row.prop(scene, "added_3d_group_edit_min_count", text="Min Count")
            row.prop(scene, "added_3d_group_edit_max_count", text="Max Count")
            box.prop(scene, "added_3d_group_edit_spacing", text="Spacing")
            box.prop(scene, "added_3d_group_edit_scale", text="Scale")
            box.prop(scene, "added_3d_group_edit_placement_offset", text="Placement Offset")

            row = box.row()
            row.scale_y = 1.5
            row.operator("cg.apply_selected_3d_asset_group", text="Apply This Group", icon="CHECKMARK")
            return

        box.prop(scene, "added_3d_asset_id", text="Asset")

        asset = CITY_3D_ASSETS.get(scene.added_3d_asset_id)
        if asset:
            box.label(text=asset["label"])

        row = box.row(align=True)
        row.prop(scene, "added_3d_asset_min_count", text="Min Count")
        row.prop(scene, "added_3d_asset_max_count", text="Max Count")
        box.prop(scene, "added_3d_asset_spacing", text="Spacing")
        box.prop(scene, "added_3d_asset_randomize", text="Random Layout")
        box.prop(scene, "added_3d_asset_scale", text="Scale")
        box.prop(scene, "added_3d_asset_placement_offset", text="Placement Offset")
        box.prop(scene, "added_3d_asset_clear_previous", text="Replace Same Asset")

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.apply_added_3d_asset", text="Apply 3D Asset", icon="OUTLINER_OB_GROUP_INSTANCE")

        obj = context.object
        if not obj or not obj.modifiers.get("City_Generator_2.0"):
            box.label(text="Apply City Generator to an active mesh first.", icon="ERROR")
