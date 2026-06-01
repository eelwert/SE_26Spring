import bpy

from ..layout_template_engine import apply_layout_template


class CG_OT_Apply_Layout_Template(bpy.types.Operator):
    bl_idname = "cg.apply_layout_template"
    bl_label = "Apply Layout Template"
    bl_description = "Create an experimental City Generator source layout with the selected grid size"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        try:
            result = apply_layout_template(
                context,
                layout_id=scene.layout_template_id,
                rows=scene.layout_template_rows,
                columns=scene.layout_template_columns,
                clear_previous=scene.layout_template_clear_previous,
            )
            self.report({"INFO"}, f"Applied layout: {result['layout_name']} ({result['rows']} x {result['columns']})")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
