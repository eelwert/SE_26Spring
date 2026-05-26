import bpy


class CG_Street_Setting_Panel(bpy.types.Panel):
    bl_label = "Street Settings"
    bl_idname = "CG_Street_Setting_Panel"
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
                box.prop(mod, '["Socket_9"]', text="Street Width")
                box.prop(mod, '["Socket_12"]', text="Lane Amount")
                box.prop(mod, '["Socket_16"]', text="Side Walk Scale")
                box.prop(mod, '["Socket_20"]', text="Parking Lanes Probability")
                box.prop(mod, '["Socket_21"]', text="Seed")
        else:
            layout.label(text="No active object selected.", icon='ERROR')


class CG_Park_Setting_Panel(bpy.types.Panel):
    bl_label = "Park Settings"
    bl_idname = "CG_Park_Setting_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Street_Setting_Panel'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        if obj and obj.modifiers:
            mod = obj.modifiers.get("City_Generator_2.0")
            if mod:
                box = layout.box()
                box.scale_y = 1.5
                row = box.row()  # Properly define the row
                row.operator("mesh.add_park_attribute", text="Add Park", icon='FACESEL').value = 1
                row.operator("mesh.add_park_attribute", text="Remove Park", icon='FACESEL').value = 0
                box = layout.box()
                box.prop(mod, '["Socket_154"]', text="Path Subdivision")
                box.prop(mod, '["Socket_155"]', text="Path Seed")
                box.prop(mod, '["Socket_156"]', text="Path Iterations")
                box.prop(mod, '["Socket_157"]', text="Path Radius")
                box.prop(mod, '["Socket_158"]', text="Tree Distance Min")
                box.prop(mod, '["Socket_159"]', text="Tree Density Factor")
                box.prop(mod, '["Socket_160"]', text="Tree Seed")
                box.prop(mod, '["Socket_161"]', text="Min Scale")
                box.prop(mod, '["Socket_162"]', text="Max Scale")
        else:
            layout.label(text="No active object selected.", icon='ERROR')


class CG_Street_Adv_Setting_Panel(bpy.types.Panel):
    bl_label = "Advanced Settings"
    bl_idname = "CG_Street_Adv_Setting_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM City Generator'
    bl_parent_id = 'CG_Street_Setting_Panel'
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

        # Standard properties (Sockets 22-25)
        box.prop(mod, '["Socket_22"]', text="Corner Radius")
        box.prop(mod, '["Socket_23"]', text="Sidewalk Height")
        box.prop(mod, '["Socket_24"]', text="Curb Width")
        box.prop(mod, '["Socket_25"]', text="Curb Height")

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_26"]', bpy.data, "collections", text="Decal Collection", icon='OUTLINER_COLLECTION')
        box.prop(mod, '["Socket_27"]', text="Decal Distance Min")

        box.label(text="Tree Settings")
        row = box.row()
        row.prop_search(mod, '["Socket_166"]', bpy.data, "collections", text="Tree Collection", icon='OUTLINER_COLLECTION')
        box.prop(mod, '["Socket_169"]', text="Tree Corner Distance")
        box.prop(mod, '["Socket_170"]', text="Tree Position")
        box.prop(mod, '["Socket_185"]', text="Tree Random Face Probability")
        box.prop(mod, '["Socket_186"]', text="Seed")
        box.prop(mod, '["Socket_167"]', text="Tree Random Edge Probability")
        box.prop(mod, '["Socket_168"]', text="Seed")
        row = box.row()
        row.scale_y = 1.5
        row.operator("mesh.delete_trees_from_edge", text="Delete Trees from Edge", icon='EDGESEL').value = 1
        row.operator("mesh.delete_trees_from_edge", text="Add Trees to Edge", icon='EDGESEL').value = 0
        box.prop(mod, '["Socket_171"]', text="Tree Distance")
        box.prop(mod, '["Socket_172"]', text="Delete Tree Probability")
        box.prop(mod, '["Socket_173"]', text="Seed")
        box.prop(mod, '["Socket_182"]', text="Tree Min Scale")
        box.prop(mod, '["Socket_183"]', text="Tree Max Scale")
        box.prop(mod, '["Socket_184"]', text="Seed")

        box.label(text="Crosswalk Settings")
        row = box.row()
        row.scale_y = 1.5
        row.operator("mesh.delete_crosswalk", text="Remove Crosswalk", icon='VERTEXSEL').value = 1
        row.operator("mesh.delete_crosswalk", text="Add Crosswalk", icon='VERTEXSEL').value = 0

        # Material Panel
        row = box.row()
        row.label(text="Crosswalk Material: ", icon='MATERIAL')
        row.prop_search(mod, '["Socket_29"]', bpy.data, "materials", text="")

        box.prop(mod, '["Socket_30"]', text="Crosswalk Length")
        box.prop(mod, '["Socket_31"]', text="Crosswalk Width")
        box.prop(mod, '["Socket_32"]', text="Crosswalk Width Scale")

        box.label(text="Lane Settings")
        row = box.row()
        row.scale_y = 1.5
        row.operator("mesh.add_bus_lane", text="Add Bus Lane", icon='EDGESEL').value = 1
        row.operator("mesh.add_bus_lane", text="Remove Bus Lane", icon='EDGESEL').value = 0
        box.prop(mod, '["Socket_35"]', text="Lane Distance")
        box.prop(mod, '["Socket_36"]', text="Marking Radius")
        box.prop(mod, '["Socket_37"]', text="Dashed Lines Probability")
        box.prop(mod, '["Socket_38"]', text="Dashed Lines Seed")
        box.prop(mod, '["Socket_39"]', text="Dashed Lines Length")
        box.prop(mod, '["Socket_40"]', text="Stop Line Width")

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_41"]', bpy.data, "collections", text="", icon='OUTLINER_COLLECTION')
        row = box.row()

        # Material Panel
        row.label(text="Select Material: ", icon='MATERIAL')
        row.prop_search(mod, '["Socket_42"]', bpy.data, "materials", text="")
        row = box.row()

        box.label(text="Side Lanes")
        box.prop(mod, '["Socket_44"]', text="Side Lanes Min")
        box.prop(mod, '["Socket_45"]', text="Side Lanes Max")
        box.prop(mod, '["Socket_46"]', text="Seed")
        box.prop(mod, '["Socket_47"]', text="Diagonal Lines Distance")
        box.label(text="Bike Lanes")
        box.prop(mod, '["Socket_48"]', text="Bike Lane Probability")
        box.prop(mod, '["Socket_49"]', text="Bike Lane Seed")

        # Material Panel
        row = box.row()
        row.label(text="Bike Lane Material:", icon='MATERIAL')
        row.prop_search(mod, '["Socket_50"]', bpy.data, "materials", text="")

        box.prop(mod, '["Socket_49"]', text="Bike Lane Seed")
        # Simple Label
        box.label(text="Parking Cars Settings")
        box.prop(mod, '["Socket_51"]', text="Parking Cars Distance")
        box.prop(mod, '["Socket_52"]', text="Delete Cars Probability")
        box.prop(mod, '["Socket_53"]', text="Delete Cars Seed")

        # Simple Label
        box.label(text="Intersection Grid Settings")
        row = box.row()
        row.scale_y = 1.5
        row.operator("mesh.set_intersection_grid", text="Add Intersection Grid", icon='VERTEXSEL').value = 1
        row.operator("mesh.set_intersection_grid", text="Remove Intersection Grid", icon='VERTEXSEL').value = 0

        # Material Panel
        row = box.row()
        row.label(text="Intersection Grid Material:", icon='MATERIAL')
        row.prop_search(mod, '["Socket_54"]', bpy.data, "materials", text="")

        box.prop(mod, '["Socket_55"]', text="Intersection Grid Additional Radius")
        box.prop(mod, '["Socket_56"]', text="Intersection Grid SubDiv Level")

        # Simple Label
        box.label(text="Side Walk Settings")
        # Material Panel
        row = box.row()
        row.label(text="Side Walk Material:", icon='MATERIAL')
        row.prop_search(mod, '["Socket_59"]', bpy.data, "materials", text="")
        box.prop(mod, '["Socket_60"]', text="UV Scalel")

        row = box.row()
        row = box.row()
        box.label(text="Street Light Settings")
        row = box.row()
        row = box.row()
        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_62"]', bpy.data, "collections", text="Street Light Collection", icon='OUTLINER_COLLECTION')

        box.prop(mod, '["Socket_63"]', text="Spot Light")
        box.prop(mod, '["Socket_64"]', text="Street Lights")
        box.prop(mod, '["Socket_65"]', text="Cycles Optimised Street Lighting")
        box.prop(mod, '["Socket_66"]', text="Street Lights Corner Distance")
        box.prop(mod, '["Socket_67"]', text="Street Lights Distance")
        box.prop(mod, '["Socket_68"]', text="Street Lights Placement")

        row = box.row()
        row = box.row()
        box.label(text="Sidewalk Assets")
        row = box.row()

        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_69"]', bpy.data, "collections", text="Side Walk Assets", icon='OUTLINER_COLLECTION')
        row = box.row()
        row.prop_search(mod, '["Socket_70"]', bpy.data, "collections", text="Secondary Side Walk Assets", icon='OUTLINER_COLLECTION')
        box.prop(mod, '["Socket_71"]', text="Use Secondary Assets")
        box.prop(mod, '["Socket_72"]', text="Probability")
        box.prop(mod, '["Socket_73"]', text="Asset Distance")
        box.prop(mod, '["Socket_74"]', text="Edge Selection")

        box.label(text="Railings")
        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_75"]', bpy.data, "collections", text="", icon='OUTLINER_COLLECTION')
        row = box.row()
        box.prop(mod, '["Socket_76"]', text="Corner Distance")
        box.prop(mod, '["Socket_77"]', text="Length")
        box.prop(mod, '["Socket_78"]', text="Edge Selection")
        box.prop(mod, '["Socket_79"]', text="Seed")
        box.prop(mod, '["Socket_80"]', text="Delete Elements")
        box.prop(mod, '["Socket_81"]', text="Seed")

        box.label(text="Traffic Light Settings")
        # Colection Panel
        row = box.row()
        row.prop_search(mod, '["Socket_82"]', bpy.data, "collections", text="Traffic Light Collection", icon='OUTLINER_COLLECTION')
        row = box.row()
        box.prop(mod, '["Socket_83"]', text="Instance Probability")
        box.prop(mod, '["Socket_84"]', text="Seed")
        box.prop(mod, '["Socket_85"]', text="Corner Placement")
