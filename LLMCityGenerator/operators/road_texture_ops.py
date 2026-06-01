import bpy

from ..road_texture_engine import apply_pavement_texture, apply_road_texture


class CG_OT_Apply_Road_Texture(bpy.types.Operator):
    bl_idname = "cg.apply_road_texture"
    bl_label = "Apply Road Texture"
    bl_description = "Apply selected road texture material to the active City Generator object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = apply_road_texture(context, context.scene.road_texture_id)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if result["warnings"]:
            self.report({"WARNING"}, "; ".join(result["warnings"][:2]))
        else:
            self.report({"INFO"}, f"Applied road texture: {result['texture_name']}")

        return {"FINISHED"}


class CG_OT_Apply_Pavement_Texture(bpy.types.Operator):
    bl_idname = "cg.apply_pavement_texture"
    bl_label = "Apply Pavement Texture"
    bl_description = "Apply selected pavement texture material to the active City Generator object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = apply_pavement_texture(context, context.scene.pavement_texture_id)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if result["warnings"]:
            self.report({"WARNING"}, "; ".join(result["warnings"][:2]))
        else:
            self.report({"INFO"}, f"Applied pavement texture: {result['texture_name']}")

        return {"FINISHED"}
