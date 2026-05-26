import bpy


class CG_Building_Panel(bpy.types.Panel):
    bl_label = "Building Settings"
    bl_idname = "CG_Building_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Setting_panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Access the active object
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Create a new box for better visual grouping
                box = layout.box()  # Start a new visual box
                box.prop(mod, '["Socket_112"]', text="Building Height Min")
                box.prop(mod, '["Socket_113"]', text="Building Height Max")
                box.prop(mod, '["Socket_114"]', text="Seed")

                box.prop(mod, '["Socket_120"]', text="Switch Asset Type")

                # Add Asset Seed after the box
                box.prop(mod, '["Socket_115"]', text="Asset Seed")


class CG_Building_Advanced_Panel(bpy.types.Panel):
    bl_label = "Advanced Settings"
    bl_idname = "CG_Building_Advanced_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Building_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Access the active object
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Initialize a box layout for visual grouping
                box = layout.box()  # You must define this before using it

                # Add Custom Height Value to the same box
                row = box.row(align=True)  # Add a row within the box
                row.scale_y = 1.5
                row.label(icon='FACESEL')  # Add the face icon
                row.prop(scene, "height_value", text="Custom Height Value")

                # Add Custom Facade Asset Index
                row = box.row(align=True)  # Add a row within the box
                row.scale_y = 1.5
                row.label(icon='FACESEL')  # Add the face icon
                row.prop(scene, "custom_facade_asset_index", text="Custom Facade Asset")

                # Add Custom Ground Floor Asset Index
                row = box.row(align=True)  # Add a row within the box
                row.scale_y = 1.5
                row.label(icon='FACESEL')  # Add the face icon
                row.prop(scene, "custom_ground_asset", text="Custom Ground Floor Asset")

                # Add operators for modern building assignment
                row = box.row()
                row.scale_y = 1.5
                row.operator("mesh.set_modern_building_attribute", text="Assign Modern Building", icon='FACESEL').value = 1
                row.operator("mesh.set_modern_building_attribute", text="Remove Modern Building", icon='FACESEL').value = 0

                # Add operators for building deletion
                row = box.row()
                row.scale_y = 1.5
                row.operator("mesh.delete_building_attribute", text="Delete Building", icon='FACESEL').value = 1
                row.operator("mesh.delete_building_attribute", text="Add Building", icon='FACESEL').value = 0

                # Add Custom Ground Floor Asset Index
                row = box.row(align=True)  # Add a row within the box
                row.scale_y = 1.5
                row.label(icon='FACESEL')  # Add the face icon
                row.prop(scene, "zshape", text="ZShape Amount")

                # Add Custom Ground Floor Asset Index
                row = box.row(align=True)  # Add a row within the box
                row.scale_y = 1.5
                row.label(icon='FACESEL')  # Add the face icon
                row.prop(scene, "zshape_height", text="ZShape Height")

                # Add Custom Ground Floor Asset Index
                row = box.row(align=True)  # Add a row within the box
                row.scale_y = 1.5
                row.label(icon='FACESEL')  # Add the face icon
                row.prop(scene, "zshape_insert", text="ZShape Insert")


class CG_Building_Asset_distribution_Panel(bpy.types.Panel):
    bl_label = "Asset Distribution Settings"
    bl_idname = "CG_Building_Asset_Distribution_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Building_Advanced_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Create a new box for better grouping
                box = layout.box()
                box.prop(mod, '["Socket_116"]', text="Asset Layer Seed")
                box.prop(mod, '["Socket_117"]', text="Horizontal | Vertical Order")
                box.prop(mod, '["Socket_118"]', text="Seed")
                box.prop(mod, '["Socket_119"]', text="Mask Top Bottom Floors")


class CG_Building_Floor_Plan_Shape_Panel(bpy.types.Panel):
    bl_label = "Floor Plan Shape Settings"
    bl_idname = "CG_Building_Floor_Plan_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Building_Advanced_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Create a new box for better grouping
                box = layout.box()
                box.prop(mod, '["Socket_122"]', text="Randomise Shape")
                box.prop(mod, '["Socket_123"]', text="Probability")
                box.prop(mod, '["Socket_124"]', text="Seed")
                box.prop(mod, '["Socket_125"]', text="SubDiv Level")
                box.prop(mod, '["Socket_126"]', text="Offset Scale")


class CG_Building_Additional_Assets_Panel(bpy.types.Panel):
    bl_label = "Additional Assets"
    bl_idname = "CG_Building_Additional_Assets_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Building_Advanced_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Create a new box for better grouping
                box = layout.box()
                # Colection Panel
                row = box.row()
                row.prop_search(mod, '["Socket_128"]', bpy.data, "collections", text="Fire Escapes Assets", icon='OUTLINER_COLLECTION')
                row = box.row()
                box.prop(mod, '["Socket_129"]', text="Probability")
                box.prop(mod, '["Socket_130"]', text="Seed")
                # Colection Panel
                row = box.row()
                row.prop_search(mod, '["Socket_131"]', bpy.data, "collections", text="Flag Signs", icon='OUTLINER_COLLECTION')
                row = box.row()
                box.prop(mod, '["Socket_132"]', text="Probability")
                box.prop(mod, '["Socket_133"]', text="Seed")
                box.prop(mod, '["Socket_134"]', text="Floor Max")
                box.prop(mod, '["Socket_135"]', text="Seed")
                box.prop(mod, '["Socket_136"]', text="Scale Seed")
                box.prop(mod, '["Socket_137"]', text="Position Seed")
                row = box.row()
                row.prop_search(mod, '["Socket_138"]', bpy.data, "collections", text="Scaffolding Assets", icon='OUTLINER_COLLECTION')
                row = box.row()
                box.prop(mod, '["Socket_139"]', text="Select Edges")
                box.prop(mod, '["Socket_140"]', text="Seed")


class CG_Building_Roof_Panel(bpy.types.Panel):
    bl_label = "Roof Settings"
    bl_idname = "CG_Building_Roof_Assets_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Building_Advanced_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")

            if mod:
                # Create a new box for better grouping
                box = layout.box()
                row = box.row()
                row.label(text="Roof Material: ", icon='MATERIAL')
                row.prop_search(mod, '["Socket_147"]', bpy.data, "materials", text="")
                row = box.row()
                row.label(text="Roof Material: ", icon='MATERIAL')
                row.prop_search(mod, '["Socket_148"]', bpy.data, "materials", text="")
                row = box.row()
                row.label(text="Roof Material: ", icon='MATERIAL')
                row.prop_search(mod, '["Socket_149"]', bpy.data, "materials", text="")
                row = box.row()
                box.prop(mod, '["Socket_164"]', text="Seed")
                box.prop(mod, '["Socket_174"]', text="Distance Min")
                box.prop(mod, '["Socket_175"]', text="Density Factor")
                box.prop(mod, '["Socket_176"]', text="Distance From Edge")
                box.prop(mod, '["Socket_177"]', text="Scale Min")
                box.prop(mod, '["Socket_178"]', text="Scale Max")
                box.prop(mod, '["Socket_179"]', text="Seed")
                row = box.row()
                row.prop_search(mod, '["Socket_180"]', bpy.data, "collections", text="Asset Type 1", icon='OUTLINER_COLLECTION')
                row = box.row()
                row.prop_search(mod, '["Socket_181"]', bpy.data, "collections", text="Asset Type 2", icon='OUTLINER_COLLECTION')
