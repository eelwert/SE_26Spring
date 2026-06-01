import bpy

from ..template_engine import apply_scene_template


class CG_OT_Apply_Scene_Template(bpy.types.Operator):
    bl_idname = "cg.apply_scene_template"
    bl_label = "Apply Scene Template"
    bl_description = "Apply a predefined scene template to the active City Generator object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = apply_scene_template(context, context.scene.city_template_id)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if result["warnings"]:
            self.report({"WARNING"}, "; ".join(result["warnings"][:2]))
        else:
            self.report({"INFO"}, f"Applied template: {result['template_name']}")

        return {"FINISHED"}