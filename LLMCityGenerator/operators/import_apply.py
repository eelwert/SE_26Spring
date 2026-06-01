import bpy
from ..utils import append_data, find_layer_collection


class CG_OT_Import_Node_Group(bpy.types.Operator):
    bl_idname = 'cg.import_node_group'
    bl_label = 'Import Node Group'
    bl_description = "Import City Generator Node Group"
    bl_options = {'PRESET', 'UNDO'}

    def execute(self, context):
        node_group_name = 'City_Generator_2.0'
        city_object_name = 'City_Generator_2.0_Object'
        assets_collection_name = 'City_Gen_2.0_Assets'

        # Import the City object
        if city_object_name not in bpy.data.objects:
            append_data("Object", city_object_name)
            self.report({'INFO'}, f"'{city_object_name}' object imported successfully.")
        else:
            self.report({'INFO'}, f"'{city_object_name}' object already exists.")

        # Import node group
        if node_group_name not in bpy.data.node_groups:
            append_data("NodeTree", node_group_name)
            self.report({'INFO'}, f"'{node_group_name}' node group imported successfully.")
        else:
            self.report({'INFO'}, f"'{node_group_name}' node group already exists.")

        # Import and link the assets collection
        if assets_collection_name not in bpy.data.collections:
            append_data("Collection", assets_collection_name)
        coll = bpy.data.collections.get(assets_collection_name)
        if coll and coll.name not in context.scene.collection.children:
            context.scene.collection.children.link(coll)

        # Hide the assets collection from the viewport
        layer_collection = find_layer_collection(context.view_layer.layer_collection, assets_collection_name)

        if layer_collection:
            layer_collection.exclude = True  # Exclude from the viewport
            context.view_layer.update()  # Refresh the view layer to apply changes
        else:
            self.report({'WARNING'}, f"Layer collection '{assets_collection_name}' not found.")

        return {'FINISHED'}


class CG_OT_Apply_Node_Group(bpy.types.Operator):
    bl_idname = 'cg.apply_node_group'
    bl_label = 'Apply Node Group'
    bl_description = "Apply City Generator Node Group to Active Object"
    bl_options = {'PRESET', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        node_group_name = 'City_Generator_2.0'
        assets_collection_name = 'City_Gen_2.0_Assets'
        obj = context.active_object

        # Import node group if missing
        if node_group_name not in bpy.data.node_groups:
            append_data("NodeTree", node_group_name)

        # Import and link the assets collection if needed
        if assets_collection_name not in bpy.data.collections:
            append_data("Collection", assets_collection_name)
        coll = bpy.data.collections.get(assets_collection_name)
        if coll and coll.name not in context.scene.collection.children:
            context.scene.collection.children.link(coll)

        # Apply node group as a modifier
        if node_group_name not in obj.modifiers:
            mod = obj.modifiers.new(type='NODES', name=node_group_name)
            mod.node_group = bpy.data.node_groups.get(node_group_name)
        else:
            self.report({'WARNING'}, f"'{node_group_name}' modifier already exists on the active object!")

        # Manage the collection visibility
        layer_collection = find_layer_collection(context.view_layer.layer_collection, assets_collection_name)

        if layer_collection:
            layer_collection.exclude = True  # Exclude from the viewport
            context.view_layer.update()  # Refresh the view layer to apply changes
            self.report({'INFO'}, f"Collection '{assets_collection_name}' visibility updated.")
        else:
            self.report({'WARNING'}, f"Layer collection '{assets_collection_name}' not found.")

        return {'FINISHED'}


class CG_OT_Duplicate_Object(bpy.types.Operator):
    bl_idname = "cg.duplicate_object"
    bl_label = "Duplicate Object with Modifier"
    bl_description = "Duplicate the object with the same Geometry Nodes modifier and rename it to 'CityGen Buildings'"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object

        # Check if the object and its modifiers exist
        if obj and obj.modifiers:
            geo_mod = obj.modifiers.get("City_Generator_2.0")
            if geo_mod:
                obj.modifiers["City_Generator_2.0"]["Socket_163"] = True

                # Duplicate the object
                bpy.ops.object.duplicate()

                # Get the duplicated object
                duplicate = context.object
                duplicate.name = "CityGen Buildings"  # Rename the duplicate

                # Apply the modifier
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.modifier_apply(modifier=geo_mod.name)

                # Add the modifier back to the duplicate
                new_mod = duplicate.modifiers.new(name="City_Generator_2.0", type="NODES")
                new_mod.node_group = geo_mod.node_group  # Copy the node group

                # Copy all other settings from the original modifier
                for prop in geo_mod.keys():
                    if prop not in {"rna_type", "name", "type", "node_group"}:  # Skip default keys
                        new_mod[prop] = geo_mod[prop]

                geo_mod["Socket_163"] = False  # Original object
                geo_mod["Socket_142"] = False  # Original object

                new_mod["Socket_163"] = False  # Duplicate object
                new_mod["Socket_145"] = True  # Set the new socket for the duplicate

                # Programmatically disable and re-enable the modifier for the duplicate object
                geo_mod.show_viewport = False
                bpy.context.view_layer.update()
                geo_mod.show_viewport = True
                bpy.context.view_layer.update()

                self.report({'INFO'}, "Object duplicated and modifier re-added successfully!")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "The object does not have a 'City_Generator_2.0' modifier.")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "No active object or modifiers found.")
            return {'CANCELLED'}
