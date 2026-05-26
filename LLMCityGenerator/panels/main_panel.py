import bpy


class CG_PT_Main_Panel(bpy.types.Panel):
    bl_label = "Import City Generator"
    bl_idname = "CG_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        row = box.row()
        row.scale_y = 2.0
        row.operator("cg.import_node_group", text="Import City Generator", icon='IMPORT')

        row = box.row()
        row.scale_y = 2.0
        row.operator("cg.apply_node_group", text="Apply Node Group", icon='NODETREE')


class CG_Setting_Panel(bpy.types.Panel):
    bl_label = "City Generator Settings"
    bl_idname = "CG_Setting_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
