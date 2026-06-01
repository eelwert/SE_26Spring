# dA_5_add
import bpy

from ..furniture_asset_engine import apply_added_3d_asset, reapply_selected_added_3d_group


# dA_5_add
class CG_OT_Apply_Added_3D_Asset(bpy.types.Operator):
    bl_idname = "cg.apply_added_3d_asset"
    bl_label = "Apply Added 3D Asset"
    bl_description = "Load the selected added 3D asset and place instances around the active City Generator object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        try:
            result = apply_added_3d_asset(
                context,
                scene.added_3d_asset_id,
                min_count=scene.added_3d_asset_min_count,
                max_count=scene.added_3d_asset_max_count,
                spacing=scene.added_3d_asset_spacing,
                scale=scene.added_3d_asset_scale,
                placement_offset=scene.added_3d_asset_placement_offset,
                randomize=scene.added_3d_asset_randomize,
                clear_previous=scene.added_3d_asset_clear_previous,
            )
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Placed {result['count']} instances of {result['asset_name']}",
        )
        return {"FINISHED"}


# dA_5_add
class CG_OT_Apply_Selected_3D_Asset_Group(bpy.types.Operator):
    bl_idname = "cg.apply_selected_3d_asset_group"
    bl_label = "Apply Selected 3D Asset Group"
    bl_description = "Rebuild only the selected generated 3D asset group with edited parameters"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        try:
            result = reapply_selected_added_3d_group(
                context,
                min_count=scene.added_3d_group_edit_min_count,
                max_count=scene.added_3d_group_edit_max_count,
                spacing=scene.added_3d_group_edit_spacing,
                scale=scene.added_3d_group_edit_scale,
                placement_offset=scene.added_3d_group_edit_placement_offset,
            )
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Updated selected group: {result['count']} instances",
        )
        return {"FINISHED"}
