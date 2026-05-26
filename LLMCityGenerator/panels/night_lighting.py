import bpy


class CG_Night_Lighting_Panel(bpy.types.Panel):
    bl_label = "Night_Lighting Settings"
    bl_idname = "CG_Night_Lighting_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Setting_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Access the node group for street light color (not related to the materials, but a separate group)
        node_group = bpy.data.node_groups.get("street light color")
        if node_group is None:
            layout.label(text="Node group 'street light color' not found.", icon='ERROR')
            return

        # Look for a ColorRamp node in the node group
        color_ramp_node = None
        for node in node_group.nodes:
            if node.type == 'VALTORGB':  # Node type for ColorRamp
                color_ramp_node = node
                break

        if color_ramp_node is None:
            layout.label(text="No 'Color Ramp' node found in 'street light color'.", icon='ERROR')
            return

        # Create a box for street light color
        box = layout.box()
        box.label(text="Street Light Color:")
        box.template_color_ramp(color_ramp_node, "color_ramp", expand=True)

        # Get object modifiers (make sure object is selected)
        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")  # Adjust the modifier name if needed
            if mod:
                box.prop(mod, '["Socket_64"]', text="Street Lights")
                box.prop(mod, '["Socket_65"]', text="Street Lights Cycles Optimisation")
                box.prop(mod, '["Socket_63"]', text="Spot Light")
                box.prop(mod, '["Socket_101"]', text="Car Headlights")
                row = box.row()
                box.prop(context.scene, "global_emission_strength", text="Emission Materials Strength")


class InteriorPanel(bpy.types.Panel):
    bl_label = "Interior Settings"
    bl_idname = "SCENE_PT_parallax_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Night_Lighting_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # Add sliders for each property
        layout.prop(context.scene, "emission_strength", text="Emission Strength")
        layout.prop(context.scene, "light_probability", text="Light Probability")
        layout.prop(context.scene, "seed", text="Seed")
        layout.prop(context.scene, "randomise_hue", text="Randomise Hue")
        layout.prop(context.scene, "change_hue", text="Change Hue")
        layout.prop(context.scene, "room_seed", text="Room Seed")
        layout.prop(context.scene, "close_roller_shutter", text="Close Roller Shutter")
        layout.prop(context.scene, "close_curtains", text="Close Curtains")
        layout.prop(context.scene, "curtain_shutter_seed", text="Curtain | Shutter Seed")
