import bpy


class CG_OT_Eco_Generate_Terrain(bpy.types.Operator):
    bl_idname = "cg.eco_generate_terrain"
    bl_label = "Generate Terrain"
    bl_description = "Generate procedural terrain with hills using noise displacement"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        grid_size = scene.cg_terrain_grid_size
        subdivisions = scene.cg_terrain_subdivisions
        hill_height = scene.cg_terrain_hill_height
        noise_scale = scene.cg_terrain_noise_scale
        noise_detail = scene.cg_terrain_noise_detail
        detail_enabled = scene.cg_terrain_detail_enabled
        detail_height = scene.cg_terrain_detail_height

        # Create base grid
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=subdivisions,
            y_subdivisions=subdivisions,
            size=grid_size,
            location=(0, 0, 0)
        )
        terrain_obj = context.object
        terrain_obj.name = "CG_Terrain"

        # Add Subdivision Surface modifier for vertex density
        subsurf = terrain_obj.modifiers.new(name="Subsurf_Terrain", type='SUBSURF')
        subsurf.levels = 2
        subsurf.render_levels = 2
        subsurf.subdivision_type = 'SIMPLE'

        # Create main noise texture
        tex_main = bpy.data.textures.new("CG_Terrain_Noise_Main", 'CLOUDS')
        tex_main.noise_scale = noise_scale
        tex_main.noise_depth = noise_detail

        # Add main Displace modifier
        disp_main = terrain_obj.modifiers.new(name="Displace_Main", type='DISPLACE')
        disp_main.texture = tex_main
        disp_main.strength = hill_height
        disp_main.mid_level = 0.5
        disp_main.texture_coords = 'LOCAL'

        # Add detail noise layer if enabled
        if detail_enabled:
            tex_detail = bpy.data.textures.new("CG_Terrain_Noise_Detail", 'CLOUDS')
            tex_detail.noise_scale = noise_scale * 0.3
            tex_detail.noise_depth = 2

            disp_detail = terrain_obj.modifiers.new(name="Displace_Detail", type='DISPLACE')
            disp_detail.texture = tex_detail
            disp_detail.strength = detail_height
            disp_detail.mid_level = 0.5
            disp_detail.texture_coords = 'LOCAL'

        # --- Create height-based terrain material ---
        terrain_mat = bpy.data.materials.get("CG_Terrain_Material")
        if terrain_mat is None:
            terrain_mat = bpy.data.materials.new("CG_Terrain_Material")
        terrain_mat.use_nodes = True
        nodes = terrain_mat.node_tree.nodes
        links = terrain_mat.node_tree.links
        nodes.clear()

        # Principled BSDF
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (200, 0)
        bsdf.inputs['Roughness'].default_value = 0.8

        # ColorRamp to blend low/high colors based on height
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.location = (0, 0)
        color_ramp.color_ramp.elements[0].color = scene.cg_terrain_low_color
        color_ramp.color_ramp.elements[1].color = scene.cg_terrain_high_color
        # Shift the blend point for more green at the bottom
        color_ramp.color_ramp.elements[1].position = 0.6

        # Geometry node → Position → Separate XYZ → extract Z for height
        geometry = nodes.new(type='ShaderNodeNewGeometry')
        geometry.location = (-600, 0)
        separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
        separate_xyz.location = (-400, 0)

        # Map Range: remap Z from [-strength/2, +strength/2] to [0, 1]
        map_range = nodes.new(type='ShaderNodeMapRange')
        map_range.location = (-200, 0)
        map_range.inputs['From Min'].default_value = -hill_height * 0.5
        map_range.inputs['From Max'].default_value = hill_height * 0.5
        map_range.inputs['To Min'].default_value = 0.0
        map_range.inputs['To Max'].default_value = 1.0

        # Output
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)

        # Links
        links.new(geometry.outputs['Position'], separate_xyz.inputs['Vector'])
        links.new(separate_xyz.outputs['Z'], map_range.inputs['Value'])
        links.new(map_range.outputs['Result'], color_ramp.inputs['Fac'])
        links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        # Assign material
        if terrain_obj.data.materials:
            terrain_obj.data.materials[0] = terrain_mat
        else:
            terrain_obj.data.materials.append(terrain_mat)

        # --- Optionally apply terrain displacement to city grid ---
        if scene.cg_terrain_apply_to_city:
            city_obj = None
            for obj in bpy.data.objects:
                if obj.type == 'MESH':
                    mod = obj.modifiers.get("City_Generator_2.0")
                    if mod:
                        city_obj = obj
                        break

            if city_obj is None:
                self.report({'WARNING'}, "No city grid found. Apply City Generator first.")
            else:
                bpy.context.view_layer.objects.active = city_obj

                # Add Subdivision Surface (before CG modifier, for smooth displacement)
                subsurf_name = "Subsurf_City"
                if subsurf_name not in city_obj.modifiers:
                    subsurf = city_obj.modifiers.new(name=subsurf_name, type='SUBSURF')
                    # Move Subsurf to before City_Generator_2.0
                    cg_idx = city_obj.modifiers.find("City_Generator_2.0")
                    sub_idx = city_obj.modifiers.find(subsurf_name)
                    city_obj.modifiers.move(sub_idx, cg_idx)
                    subsurf.levels = 2
                    subsurf.render_levels = 2
                    subsurf.subdivision_type = 'SIMPLE'

                # Remove previous terrain displace modifiers
                for old_mod_name in ("Displace_Terrain_Main", "Displace_Terrain_Detail"):
                    old_mod = city_obj.modifiers.get(old_mod_name)
                    if old_mod:
                        city_obj.modifiers.remove(old_mod)

                # Add displace modifiers (placed after CG modifier)
                disp_city = city_obj.modifiers.new(name="Displace_Terrain_Main", type='DISPLACE')
                disp_city.texture = tex_main
                disp_city.strength = hill_height
                disp_city.mid_level = 0.5
                disp_city.texture_coords = 'LOCAL'

                if detail_enabled:
                    disp_city_detail = city_obj.modifiers.new(
                        name="Displace_Terrain_Detail", type='DISPLACE')
                    disp_city_detail.texture = tex_detail
                    disp_city_detail.strength = detail_height
                    disp_city_detail.mid_level = 0.5
                    disp_city_detail.texture_coords = 'LOCAL'

                self.report({'INFO'}, "Terrain displacement applied to city grid.")

        # Switch to Object mode and select the terrain
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        terrain_obj.select_set(True)
        context.view_layer.objects.active = terrain_obj

        self.report({'INFO'}, "Terrain generated successfully.")
        return {'FINISHED'}


class CG_OT_Eco_Generate_Lake(bpy.types.Operator):
    bl_idname = "cg.eco_generate_lake"
    bl_label = "Generate Lake"
    bl_description = "Generate a circular lake with water material and ripple effects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        lake_size = scene.cg_lake_size
        block_size = scene.cg_lake_block_size
        edge_irregular = scene.cg_lake_edge_irregularity
        lake_seed = scene.cg_lake_seed
        lake_vertices = scene.cg_lake_vertices
        ripple_strength = scene.cg_lake_ripple_strength
        ripple_scale = scene.cg_lake_ripple_scale
        water_color = scene.cg_lake_water_color

        import random
        import math
        random.seed(lake_seed)

        # --- Step 1: Create single park block (1x1, uniform park ground) ---
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=1, y_subdivisions=1,
            size=block_size, location=(0, 0, 0))
        block_obj = context.object
        block_obj.name = "CG_Lake_Block"

        # Ensure City_Generator_2.0 node group exists
        node_group_name = 'City_Generator_2.0'
        if node_group_name not in bpy.data.node_groups:
            from ..utils import append_data
            append_data("NodeTree", node_group_name)

        # Apply CG modifier
        mod = block_obj.modifiers.new(name=node_group_name, type='NODES')
        mod.node_group = bpy.data.node_groups.get(node_group_name)

        # Configure: Buildings OFF, Streets ON (needed for park ground)
        mod["Socket_142"] = False  # Buildings off
        mod["Socket_143"] = True   # Streets on
        mod["Socket_144"] = False  # Traffic off

        # Minimize street footprint, keep only park ground
        mod["Socket_9"] = 0.01
        mod["Socket_16"] = 0.0
        mod["Socket_20"] = 0.0
        mod["Socket_12"] = 1

        # Disable street tree systems
        mod["Socket_167"] = 0.0
        mod["Socket_185"] = 0.0
        mod["Socket_172"] = 0.0

        # Park paths off (avoid paths through lake area)
        mod["Socket_154"] = 0       # Path Subdivision
        # Sparse park trees (1-2 per block)
        mod["Socket_158"] = 20.0   # Tree Distance Min
        mod["Socket_159"] = 0.15   # Tree Density Factor
        mod["Socket_161"] = 0.5
        mod["Socket_162"] = 1.0

        # Mark single face as park
        mesh = block_obj.data
        if "assign Park" not in mesh.attributes:
            mesh.attributes.new(name="assign Park", type='INT', domain='FACE')
        mesh.attributes["assign Park"].data[0].value = 1

        # --- Step 2: Create irregular lake surface above center ---
        bpy.ops.mesh.primitive_circle_add(
            vertices=lake_vertices,
            radius=lake_size,
            location=(0, 0, 0.15)
        )
        lake_obj = context.object
        lake_obj.name = "CG_Lake"

        # Jitter circle vertices radially for natural shoreline
        lake_mesh = lake_obj.data
        for v in lake_mesh.vertices:
            dx = v.co.x
            dy = v.co.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0.001:
                offset = random.uniform(-edge_irregular, edge_irregular) * lake_size * 0.35
                factor = 1.0 + offset / dist
                v.co.x *= factor
                v.co.y *= factor

        # Fill the face
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Add Solidify for visible water edge
        solid_mod = lake_obj.modifiers.new(name="Solidify_Water", type='SOLIDIFY')
        solid_mod.thickness = 0.15
        solid_mod.offset = 0.0

        # --- Step 3: Create/reuse water material ---
        water_mat = bpy.data.materials.get("CG_Water_Material")
        if water_mat is None:
            water_mat = bpy.data.materials.new("CG_Water_Material")
        water_mat.use_nodes = True
        nodes = water_mat.node_tree.nodes
        links = water_mat.node_tree.links
        nodes.clear()

        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs['Base Color'].default_value = water_color
        bsdf.inputs['Transmission Weight'].default_value = 0.92
        bsdf.inputs['Roughness'].default_value = 0.0
        bsdf.inputs['Alpha'].default_value = 0.85
        bsdf.inputs['IOR'].default_value = 1.33
        bsdf.inputs['Specular IOR Level'].default_value = 0.5

        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.location = (-400, -200)
        noise.inputs['Scale'].default_value = ripple_scale
        noise.inputs['Detail'].default_value = 4.0

        normal_map = nodes.new(type='ShaderNodeNormalMap')
        normal_map.location = (-200, -200)
        normal_map.inputs['Strength'].default_value = ripple_strength

        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (200, 0)

        links.new(noise.outputs['Fac'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        if lake_obj.data.materials:
            lake_obj.data.materials[0] = water_mat
        else:
            lake_obj.data.materials.append(water_mat)

        # --- Step 4: Parent lake to block ---
        lake_obj.parent = block_obj

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        block_obj.select_set(True)
        lake_obj.select_set(True)
        context.view_layer.objects.active = block_obj

        self.report({'INFO'}, "Lake block generated successfully.")
        return {'FINISHED'}


class CG_OT_Eco_Generate_River(bpy.types.Operator):
    bl_idname = "cg.eco_generate_river"
    bl_label = "Generate River"
    bl_description = "Generate a river path with water surface along a bezier curve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        river_width = scene.cg_river_width

        # Create bezier curve for river path
        bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0.1))
        curve_obj = context.object
        curve_obj.name = "CG_River_Path"

        # Shape the bezier curve into an S-curve
        curve_data = curve_obj.data
        curve_data.dimensions = '3D'
        spline = curve_data.splines[0]
        spline.use_smooth = True

        bp0 = spline.bezier_points[0]
        bp0.co = (-30, -15, 0)
        bp0.handle_right_type = 'AUTO'
        bp0.handle_left_type = 'AUTO'

        bp1 = spline.bezier_points[1]
        bp1.co = (30, 15, 0)
        bp1.handle_right_type = 'AUTO'
        bp1.handle_left_type = 'AUTO'

        # Create river surface mesh (subdivided plane)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.05))
        river_obj = context.object
        river_obj.name = "CG_River_Surface"

        # Subdivide plane for smooth deformation
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide(number_cuts=30)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Scale to match river width along Y axis
        river_obj.scale = (1, river_width, 1)

        # Add Curve modifier to deform plane along river path
        curve_mod = river_obj.modifiers.new(name="River_Curve", type='CURVE')
        curve_mod.object = curve_obj
        curve_mod.deform_axis = 'POS_X'

        # Apply water material (reuse or create)
        water_mat = bpy.data.materials.get("CG_Water_Material")
        if water_mat is None:
            water_mat = bpy.data.materials.new("CG_Water_Material")
            water_mat.use_nodes = True
            nodes = water_mat.node_tree.nodes
            links = water_mat.node_tree.links
            nodes.clear()

            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf.location = (0, 0)
            bsdf.inputs['Base Color'].default_value = (0.05, 0.2, 0.4, 1.0)
            bsdf.inputs['Transmission Weight'].default_value = 0.92
            bsdf.inputs['Roughness'].default_value = 0.0
            bsdf.inputs['Alpha'].default_value = 0.85
            bsdf.inputs['IOR'].default_value = 1.33
            bsdf.inputs['Specular IOR Level'].default_value = 0.5

            noise = nodes.new(type='ShaderNodeTexNoise')
            noise.location = (-400, -200)
            noise.inputs['Scale'].default_value = 2.0
            noise.inputs['Detail'].default_value = 4.0

            normal_map = nodes.new(type='ShaderNodeNormalMap')
            normal_map.location = (-200, -200)
            normal_map.inputs['Strength'].default_value = 0.05

            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (200, 0)

            links.new(noise.outputs['Fac'], normal_map.inputs['Color'])
            links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        if river_obj.data.materials:
            river_obj.data.materials[0] = water_mat
        else:
            river_obj.data.materials.append(water_mat)

        # Select both curve and surface
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        river_obj.select_set(True)
        context.view_layer.objects.active = river_obj

        self.report({'INFO'}, "River generated successfully.")
        return {'FINISHED'}


class CG_OT_Eco_Add_Boat(bpy.types.Operator):
    bl_idname = "cg.eco_add_boat"
    bl_label = "Add Boat"
    bl_description = "Add a procedural boat that follows the river path"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        boat_scale = scene.cg_boat_scale
        flow_speed = scene.cg_river_flow_speed

        # Check if river path exists
        river_curve = bpy.data.objects.get("CG_River_Path")
        if river_curve is None:
            self.report({'WARNING'}, "No river found. Generate a river first.")
            return {'CANCELLED'}

        # --- Build a simple boat from primitives ---
        # Hull: flattened cube
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.3))
        hull = context.object
        hull.name = "CG_Boat_Hull"
        hull.scale = (1.5, 0.5, 0.2)

        # Taper the front in edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select front-right and front-left top vertices and move them down + in
        mesh = hull.data
        bpy.ops.object.mode_set(mode='OBJECT')
        for v in mesh.vertices:
            if v.co.x > 0.5 and v.co.z > 0:
                v.co.z -= 0.3
            if v.co.x > 0.7:
                v.co.x -= 0.3

        bpy.ops.object.mode_set(mode='OBJECT')

        # Cabin: small cube on top
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.55))
        cabin = context.object
        cabin.name = "CG_Boat_Cabin"
        cabin.scale = (0.5, 0.3, 0.15)

        # Parent cabin to hull
        cabin.parent = hull

        # Join cabin into hull
        bpy.ops.object.select_all(action='DESELECT')
        hull.select_set(True)
        cabin.select_set(True)
        context.view_layer.objects.active = hull
        bpy.ops.object.join()

        # Rename and scale the boat
        hull.name = "CG_Boat"
        hull.scale *= boat_scale

        # --- Add Follow Path constraint ---
        follow_constraint = hull.constraints.new(type='FOLLOW_PATH')
        follow_constraint.target = river_curve
        follow_constraint.use_curve_follow = True
        follow_constraint.forward_axis = 'FORWARD_X'
        follow_constraint.up_axis = 'UP_Z'
        follow_constraint.use_fixed_location = True

        hull.location = (0, 0, 0)

        # --- Animate: keyframe offset for looped movement ---
        con = follow_constraint
        con.offset = 0
        con.keyframe_insert(data_path="offset", frame=1)
        con.offset = 100.0 * flow_speed
        con.keyframe_insert(data_path="offset", frame=250)

        # Make animation loop by setting extrapolation
        if hull.animation_data and hull.animation_data.action:
            for fcurve in hull.animation_data.action.fcurves:
                if fcurve.data_path.startswith('constraints["') and fcurve.data_path.endswith('"].offset'):
                    for kf in fcurve.keyframe_points:
                        kf.interpolation = 'LINEAR'
                    fcurve.modifiers.new('CYCLES')

        # Select the boat
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        hull.select_set(True)
        context.view_layer.objects.active = hull

        self.report({'INFO'}, "Boat added successfully. Play animation to see it move.")
        return {'FINISHED'}
