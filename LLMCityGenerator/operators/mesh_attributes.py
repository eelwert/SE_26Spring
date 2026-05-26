import bpy


class MESH_OT_SetLowPolyAttribute(bpy.types.Operator):
    bl_idname = "mesh.set_low_poly_attribute"
    bl_label = "Set Low Poly"
    value: bpy.props.IntProperty()

    def execute(self, context):
        if context.object.mode == 'EDIT' and context.object.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh = context.object.data
            for poly in mesh.polygons:
                if poly.select:
                    if "low poly" not in mesh.attributes:
                        mesh.attributes.new(name="low poly", type='INT', domain='FACE')
                    mesh.attributes["low poly"].data[poly.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class MESH_OT_AddParkAttribute(bpy.types.Operator):
    bl_idname = "mesh.add_park_attribute"
    bl_label = "Add Park"
    value: bpy.props.IntProperty()

    def execute(self, context):
        if context.object.mode == 'EDIT' and context.object.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh = context.object.data
            for poly in mesh.polygons:
                if poly.select:
                    if "assign Park" not in mesh.attributes:
                        mesh.attributes.new(name="assign Park", type='INT', domain='FACE')
                    mesh.attributes["assign Park"].data[poly.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class MESH_OT_Add_Intersection_Grid(bpy.types.Operator):
    bl_idname = "mesh.set_intersection_grid"
    bl_label = "Set Intersection Grid"
    value: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        if obj.mode == 'EDIT' and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')  # Switch to Object mode
            mesh = obj.data
            for vert in mesh.vertices:  # Iterate over vertices
                if vert.select:  # Check if the vertex is selected
                    if "add intersection grid" not in mesh.attributes:
                        mesh.attributes.new(name="add intersection grid", type='INT', domain='POINT')
                    mesh.attributes["add intersection grid"].data[vert.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')  # Return to Edit mode
        return {'FINISHED'}


class MESH_OT_Delete_CrossWalk(bpy.types.Operator):
    bl_idname = "mesh.delete_crosswalk"
    bl_label = "delete crosswalk"
    value: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        if obj.mode == 'EDIT' and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')  # Switch to Object mode
            mesh = obj.data
            for vert in mesh.vertices:  # Iterate over vertices
                if vert.select:  # Check if the vertex is selected
                    if "delete cross walk" not in mesh.attributes:
                        mesh.attributes.new(name="delete cross walk", type='INT', domain='POINT')
                    mesh.attributes["delete cross walk"].data[vert.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')  # Return to Edit mode
        return {'FINISHED'}


class MESH_OT_Add_Bus_Lane(bpy.types.Operator):
    bl_idname = "mesh.add_bus_lane"
    bl_label = "Add Bus Lane"
    value: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        if obj.mode == 'EDIT' and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')  # Switch to Object mode
            mesh = obj.data
            for edge in mesh.edges:  # Iterate through edges instead of polygons
                if edge.select:  # Check if the edge is selected
                    if "add bus lane" not in mesh.attributes:
                        mesh.attributes.new(name="add bus lane", type='INT', domain='EDGE')
                    mesh.attributes["add bus lane"].data[edge.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')  # Return to Edit mode
        return {'FINISHED'}


class MESH_OT_delete_Trees_Edge(bpy.types.Operator):
    bl_idname = "mesh.delete_trees_from_edge"
    bl_label = "Delete Trees from Edge"
    value: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        if obj.mode == 'EDIT' and obj.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')  # Switch to Object mode
            mesh = obj.data
            for edge in mesh.edges:  # Iterate through edges instead of polygons
                if edge.select:  # Check if the edge is selected
                    if "delete Trees from Edge" not in mesh.attributes:
                        mesh.attributes.new(name="delete Trees from Edge", type='INT', domain='EDGE')
                    mesh.attributes["delete Trees from Edge"].data[edge.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')  # Return to Edit mode
        return {'FINISHED'}


class MESH_OT_SetmodernBuildingAttribute(bpy.types.Operator):
    bl_idname = "mesh.set_modern_building_attribute"
    bl_label = "Set Modern Building"
    value: bpy.props.IntProperty()

    def execute(self, context):
        if context.object.mode == 'EDIT' and context.object.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh = context.object.data
            for poly in mesh.polygons:
                if poly.select:
                    if "modern building" not in mesh.attributes:
                        mesh.attributes.new(name="modern building", type='INT', domain='FACE')
                    mesh.attributes["modern building"].data[poly.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class MESH_OT_DeleteBuildingAttribute(bpy.types.Operator):
    bl_idname = "mesh.delete_building_attribute"
    bl_label = "Delete Building"
    value: bpy.props.IntProperty()

    def execute(self, context):
        if context.object.mode == 'EDIT' and context.object.type == 'MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh = context.object.data
            for poly in mesh.polygons:
                if poly.select:
                    if "Delete Building" not in mesh.attributes:
                        mesh.attributes.new(name="Delete Building", type='INT', domain='FACE')
                    mesh.attributes["Delete Building"].data[poly.index].value = self.value
            bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
