"""LLM natural language control panel for the City Generator sidebar."""

import bpy


class CG_UL_LLMResultList(bpy.types.UIList):
    bl_idname = "CG_UL_llm_result_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.text)


# --- Main LLM Panel ---

class CG_PT_LLM_Panel(bpy.types.Panel):
    bl_label = "LLM Natural Language Control"
    bl_idname = "CG_PT_llm_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # API Key input
        box = layout.box()
        box.label(text="API Configuration")
        row = box.row()
        row.prop(scene, "llm_api_key", text="API Key")

        layout.separator()

        # Instruction input
        box = layout.box()
        box.label(text="Natural Language Instruction")
        box.prop(scene, "llm_text_input", text="")

        # Quick examples (collapsed by default to save space)
        box = layout.box()
        row = box.row()
        row.prop(scene, "llm_show_examples", text="", icon='TRIA_DOWN' if scene.llm_show_examples else 'TRIA_RIGHT', emboss=False)
        row.label(text="Quick Examples")
        if scene.llm_show_examples:
            examples = [
                "把道路宽度调到12米，增加车道到6条",
                "切换成滨水商业街区，树木多一些，傍晚小雨天气",
                "设置天气为晴天，时间中午12点，树木密度0.8",
                "应用校园模板，道路宽6米，树密度70%",
            ]
            for ex in examples:
                op = box.operator("cg.fill_llm_example", text=ex[:60] + ("…" if len(ex) > 60 else ""))
                op.example_text = ex

        layout.separator()

        # Execute button
        row = layout.row()
        row.scale_y = 1.8
        status = scene.llm_status
        if status == "calling":
            row.operator("cg.execute_llm_command", text="Calling LLM...")
        elif status == "executing":
            row.operator("cg.execute_llm_command", text="Executing...")
        else:
            row.operator("cg.execute_llm_command", text="Send to LLM")

        # Clear button
        row = layout.row()
        row.operator("cg.clear_llm_result", text="Clear")

        # Result display — scrollable list
        if len(scene.llm_result_lines) > 0:
            layout.separator()
            box = layout.box()
            box.label(text="Result")
            row = box.row()
            row.template_list(
                "CG_UL_llm_result_list", "",
                scene, "llm_result_lines",
                scene, "llm_result_index",
                rows=8,
            )


class CG_OT_FillLLMExample(bpy.types.Operator):
    bl_idname = "cg.fill_llm_example"
    bl_label = "Fill Example"
    bl_description = "Fill the input with this example"
    bl_options = {'REGISTER', 'UNDO'}

    example_text: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.llm_text_input = self.example_text
        return {'FINISHED'}
