import bpy


class CG_General_Setting_Panel(bpy.types.Panel):
    bl_label = "General Settings"
    bl_idname = "CG_General_Setting_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Setting_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")
            if mod:
                box = layout.box()
                box.prop(mod, '["Socket_8"]', text="Layout Edit Mode")
                box.label(text="Activated Elements")
                box.prop(mod, '["Socket_142"]', text="Buildings")
                box.prop(mod, '["Socket_143"]', text="Streets")
                box.prop(mod, '["Socket_144"]', text="Traffic")
                row = box.row()
                row.scale_y = 2.0
                row.operator("cg.duplicate_object", text="Seperate Buildings for more controll", icon='DUPLICATE')
                row = box.row()
                row.scale_y = 1.5
                row.operator("mesh.set_low_poly_attribute", text="Assign Low Poly", icon='FACESEL').value = 1
                row.operator("mesh.set_low_poly_attribute", text="Remove Low Poly", icon='FACESEL').value = 0
                row = box.row()
                box.prop(mod, '["Socket_165"]', text="Realize Instances")
                box.prop(mod, '["Socket_187"]', text="Real Mesh")
                box.prop(mod, '["Socket_188"]', text="Instances")
        else:
            layout.label(text="No active object selected.", icon='ERROR')
