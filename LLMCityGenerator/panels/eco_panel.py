import bpy


class CG_Eco_Scene_Panel(bpy.types.Panel):
    bl_label = "Eco Scene Elements"
    bl_idname = "CG_Eco_Scene_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Setting_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Procedural terrain, water, and boat generation.")


class CG_Eco_Terrain_Panel(bpy.types.Panel):
    bl_label = "Terrain"
    bl_idname = "CG_Eco_Terrain_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Eco_Scene_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="Terrain Generation")
        box.prop(scene, "cg_terrain_grid_size")
        box.prop(scene, "cg_terrain_subdivisions")

        box.separator()
        box.label(text="Main Noise Layer")
        box.prop(scene, "cg_terrain_hill_height")
        box.prop(scene, "cg_terrain_noise_scale")
        box.prop(scene, "cg_terrain_noise_detail")

        box.separator()
        box.prop(scene, "cg_terrain_detail_enabled")
        if scene.cg_terrain_detail_enabled:
            box.prop(scene, "cg_terrain_detail_height")

        row = box.row()
        row.scale_y = 2.0
        row.operator("cg.eco_generate_terrain", text="Generate Terrain", icon='SMOOTHCURVE')


class CG_Eco_Lake_Panel(bpy.types.Panel):
    bl_label = "Lake"
    bl_idname = "CG_Eco_Lake_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Eco_Scene_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="Lake Generation")
        box.prop(scene, "cg_lake_block_size")
        box.prop(scene, "cg_lake_size")
        box.prop(scene, "cg_lake_edge_irregularity")
        box.prop(scene, "cg_lake_seed")
        box.prop(scene, "cg_lake_vertices")

        box.separator()
        box.label(text="Water Material")
        box.prop(scene, "cg_lake_water_color")
        box.prop(scene, "cg_lake_ripple_strength")
        box.prop(scene, "cg_lake_ripple_scale")

        row = box.row()
        row.scale_y = 2.0
        row.operator("cg.eco_generate_lake", text="Generate Lake", icon='MESH_CIRCLE')


class CG_Eco_River_Panel(bpy.types.Panel):
    bl_label = "River & Boats"
    bl_idname = "CG_Eco_River_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Eco_Scene_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text="River Generation")
        box.prop(scene, "cg_river_width")
        box.prop(scene, "cg_river_seed")

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.eco_generate_river", text="Generate River", icon='CURVE_BEZCURVE')

        box.separator()
        box.label(text="Boat Settings")
        box.prop(scene, "cg_boat_scale")
        box.prop(scene, "cg_river_flow_speed")

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.eco_add_boat", text="Add Boat", icon='OBJECT_DATA')
