import bpy


class CG_Traffic_Sim_Panel(bpy.types.Panel):
    bl_label = "Traffic Simulation"
    bl_idname = "CG_Traffic_Sim_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Setting_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # Access the active object
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Create a new box for better visual grouping
                box = layout.box()
        box.operator("object.simulation_nodes_cache_calculate_to_frame", text="Calculate to Frame").selected = True
        box.operator("object.simulation_nodes_cache_bake", text="Bake Simulation").selected = True
        box.operator("object.simulation_nodes_cache_delete", text="Delete Bake")
        box.label(text="Traffic Paths")
        box.prop(mod, '["Socket_89"]', text="Show Paths")
        box.prop(mod, '["Socket_90"]', text="Path Amount")
        box.prop(mod, '["Socket_91"]', text="Seed")
        box.label(text="Car distribution")
        box.prop(mod, '["Socket_94"]', text="Car Distance Min")
        box.prop(mod, '["Socket_95"]', text="Intersection Distance")
        box.prop(mod, '["Socket_96"]', text="Delete Cars Probability")
        box.label(text="Simulation Settings")
        box.prop(mod, '["Socket_98"]', text="Min Speed")
        box.prop(mod, '["Socket_99"]', text="Max Speed")
        box.prop(mod, '["Socket_100"]', text="Seed")
        box.prop(mod, '["Socket_101"]', text="car headlights")

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_102"]', bpy.data, "collections", text="Car Model", icon='OUTLINER_COLLECTION')

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_103"]', bpy.data, "collections", text="Front Wheels", icon='OUTLINER_COLLECTION')

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_104"]', bpy.data, "collections", text="Back Wheels", icon='OUTLINER_COLLECTION')

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_105"]', bpy.data, "collections", text="Car Lights", icon='OUTLINER_COLLECTION')

        box.prop(mod, '["Socket_106"]', text="Instance Seed")
        box.prop(mod, '["Socket_107"]', text="Min Scale")
        box.prop(mod, '["Socket_108"]', text="Max Scale")
        box.prop(mod, '["Socket_109"]', text="Scale Seed")

        # Access the material named "CityGen car material"
        material = bpy.data.materials.get("CityGen car material")
        if material is None:
            layout.label(text="Material 'CityGen car material' not found.", icon='ERROR')
            return

        if not material.use_nodes:
            layout.label(text="Material 'CityGen car material' does not use nodes.", icon='ERROR')
            return

        # Look for a ColorRamp node in the material's node tree
        color_ramp_node = None
        for node in material.node_tree.nodes:
            if node.type == 'VALTORGB':  # Node type for ColorRamp
                color_ramp_node = node
                break

        if color_ramp_node is None:
            layout.label(text="No 'Color Ramp' node found in material 'CityGen car material'.", icon='ERROR')
            return

        # Create a box for the street light color UI
        box = layout.box()
        box.label(text="Car Colors:")
        box.template_color_ramp(color_ramp_node, "color_ramp", expand=True)
