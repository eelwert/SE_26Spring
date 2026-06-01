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

        # --- Edge falloff vertex group (1 at center, 0 at edges) ---
        vg = terrain_obj.vertex_groups.new(name="Edge_Falloff")
        half = grid_size * 0.5
        for v in terrain_obj.data.vertices:
            dist = max(abs(v.co.x), abs(v.co.y)) / half  # 0 at center, 1 at edge
            weight = 1.0 - dist * dist  # quadratic falloff for smooth blend
            weight = max(0.0, min(1.0, weight))
            vg.add([v.index], weight, 'REPLACE')

        # Create main noise texture
        tex_main = bpy.data.textures.new("CG_Terrain_Noise_Main", 'CLOUDS')
        tex_main.noise_scale = noise_scale
        tex_main.noise_depth = noise_detail

        # Add main Displace modifier (uses edge falloff vertex group)
        disp_main = terrain_obj.modifiers.new(name="Displace_Main", type='DISPLACE')
        disp_main.texture = tex_main
        disp_main.strength = hill_height
        disp_main.mid_level = 0.5
        disp_main.texture_coords = 'LOCAL'
        disp_main.vertex_group = "Edge_Falloff"

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
            disp_detail.vertex_group = "Edge_Falloff"

        # --- Load baked CG park ground texture ---
        import os as _os
        from ..constants import ADDON_DIR

        terrain_mat = bpy.data.materials.get("CG_Terrain_Material")
        if terrain_mat is None:
            terrain_mat = bpy.data.materials.new("CG_Terrain_Material")
        terrain_mat.use_nodes = True
        nodes = terrain_mat.node_tree.nodes
        links = terrain_mat.node_tree.links
        nodes.clear()

        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (200, 0)
        bsdf.inputs['Roughness'].default_value = 0.80

        # Load baked park texture (tile it to match terrain size)
        tex_path = _os.path.join(ADDON_DIR, "CG_Park_Ground.png")
        if _os.path.exists(tex_path):
            img = bpy.data.images.load(tex_path)

            # Texture coordinate: use Object space, scale to tile properly
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            tex_coord.location = (-600, 0)

            mapping = nodes.new(type='ShaderNodeMapping')
            mapping.location = (-400, 0)
            # 2 tiles across the grid (Object coords span grid_size units)
            s = 4.0 / grid_size
            mapping.inputs['Scale'].default_value = (s, s, 1.0)

            tex_node = nodes.new(type='ShaderNodeTexImage')
            tex_node.location = (-200, 0)
            tex_node.image = img

            links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
            links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        else:
            bsdf.inputs['Base Color'].default_value = (0.12, 0.35, 0.06, 1.0)

        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        if terrain_obj.data.materials:
            terrain_obj.data.materials[0] = terrain_mat
        else:
            terrain_obj.data.materials.append(terrain_mat)

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
        import random
        import math

        scene = context.scene
        river_width = scene.cg_river_width
        river_seed = scene.cg_river_seed

        rng = random.Random(river_seed)

        # --- Create meandering bezier curve ---
        bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0.1))
        curve_obj = context.object
        curve_obj.name = "CG_River_Path"

        curve_data = curve_obj.data
        curve_data.dimensions = '3D'
        spline = curve_data.splines[0]
        spline.use_smooth = True

        # Generate random meandering path: sample points along a line,
        # offset each perpendicularly by a random amount
        start = (-30, -15)
        end = (30, 15)
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx * dx + dy * dy)
        nx = -dy / length  # perpendicular normal x
        ny = dx / length   # perpendicular normal y
        max_meander = length * 0.15  # max offset ~15% of length

        num_pts = 6  # number of control points
        points = []
        for i in range(num_pts):
            t = i / (num_pts - 1)
            cx = start[0] + dx * t
            cy = start[1] + dy * t
            offset = rng.uniform(-max_meander, max_meander)
            points.append((cx + nx * offset, cy + ny * offset, 0.0))

        # Rebuild spline with calculated points
        spline.bezier_points.add(num_pts - 2)  # already has 2
        for i, (px, py, pz) in enumerate(points):
            bp = spline.bezier_points[i]
            bp.co = (px, py, pz)
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'

        # Sample curve by converting to mesh (gives dense edge loop)
        curve_data.resolution_u = 64
        for obj in context.selected_objects:
            if obj != curve_obj:
                obj.select_set(False)
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj
        bpy.ops.object.duplicate()
        sampled_obj = context.object
        sampled_obj.name = "CG_River_Surface"
        bpy.ops.object.convert(target='MESH')

        # Build ribbon: offset center-line vertices left/right by half width
        mesh = sampled_obj.data
        center_verts = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]

        # Build new mesh with pairs of ribbon vertices + quad faces
        hw = river_width * 0.5
        verts = []
        faces = []
        for i, (cx, cy, cz) in enumerate(center_verts):
            verts.append((cx, cy - hw, cz))  # left
            verts.append((cx, cy + hw, cz))  # right
            if i > 0:
                a = (i - 1) * 2
                b = i * 2
                faces.append((a, a + 1, b + 1, b))

        # Replace mesh data
        new_mesh = bpy.data.meshes.new("River_Ribbon")
        new_mesh.from_pydata(verts, [], faces)
        new_mesh.update()
        sampled_obj.data = new_mesh
        bpy.data.meshes.remove(mesh)

        # Add Solidify for visible water edge
        solid_mod = sampled_obj.modifiers.new(name="Solidify_Water", type='SOLIDIFY')
        solid_mod.thickness = 0.15
        solid_mod.offset = 0.0

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

        if sampled_obj.data.materials:
            sampled_obj.data.materials[0] = water_mat
        else:
            sampled_obj.data.materials.append(water_mat)

        # Parent curve to surface so they stay together
        curve_obj.parent = sampled_obj

        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in context.selected_objects:
            if obj != sampled_obj:
                obj.select_set(False)
        sampled_obj.select_set(True)
        context.view_layer.objects.active = sampled_obj

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
        river_width = scene.cg_river_width

        # Use selected curve, or fall back to any CG_River_Path*
        river_curve = None
        if context.active_object and context.active_object.type == 'CURVE':
            river_curve = context.active_object
        else:
            for obj in bpy.data.objects:
                if obj.type == 'CURVE' and obj.name.startswith("CG_River_Path"):
                    river_curve = obj
                    break
        if river_curve is None:
            self.report({'WARNING'}, "No river found. Select a river curve first.")
            return {'CANCELLED'}

        # --- Load boat from external .blend, or build procedural fallback ---
        import os
        from ..constants import ADDON_DIR

        boat_file = os.path.join(ADDON_DIR, "Wooden Boat.blend")
        boat_obj = None

        if os.path.exists(boat_file):
            # Load ALL objects from the blend file, keep only meshes
            with bpy.data.libraries.load(boat_file) as (data_from, data_to):
                all_names = [n for n in (data_from.objects or [])]

            loaded = []
            directory = os.path.join(ADDON_DIR, "Wooden Boat.blend", "Object")
            for obj_name in all_names:
                if obj_name in bpy.data.objects:
                    continue
                bpy.ops.wm.append(
                    directory=directory, filename=obj_name, autoselect=True)
                candidate = bpy.data.objects.get(obj_name)
                if candidate and candidate.type == 'MESH':
                    loaded.append(candidate)
                elif candidate:
                    bpy.data.objects.remove(candidate, do_unlink=True)

            if loaded:
                # Pick the largest mesh (by vertex count) as the main boat
                boat_obj = max(loaded, key=lambda o: len(o.data.vertices))
                boat_obj.name = "CG_Boat"
                boat_obj.location = (0, 0, 0.75)
                boat_obj.scale *= boat_scale
                # Parent smaller parts (oars, sails, etc.) to the main boat
                for part in loaded:
                    if part != boat_obj:
                        part.parent = boat_obj
                        part.name = f"CG_Boat_Part"
                self.report({'INFO'},
                    f"Loaded boat from Wooden Boat.blend ({len(loaded)} parts)")

        if boat_obj is None:
            self.report({'WARNING'}, "Wooden Boat.blend not found or empty, "
                        "using procedural boat instead.")
            # Fallback: procedural boat
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.3))
            boat_obj = context.object
            boat_obj.name = "CG_Boat"
            boat_obj.scale = (1.5, 0.5, 0.2)
            boat_obj.scale *= boat_scale

            mesh = boat_obj.data
            for v in mesh.vertices:
                if v.co.x > 0.5 and v.co.z > 0:
                    v.co.z -= 0.3
                if v.co.x > 0.7:
                    v.co.x -= 0.3

            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.55))
            cabin = context.object
            cabin.name = "CG_Boat_Cabin"
            cabin.scale = (0.5, 0.3, 0.15)
            cabin.parent = boat_obj
            for obj in context.selected_objects:
                obj.select_set(False)
            boat_obj.select_set(True)
            cabin.select_set(True)
            context.view_layer.objects.active = boat_obj
            bpy.ops.object.join()

            boat_mat = bpy.data.materials.get("CG_Boat_Material")
            if boat_mat is None:
                boat_mat = bpy.data.materials.new("CG_Boat_Material")
                boat_mat.use_nodes = True
                nodes = boat_mat.node_tree.nodes
                nodes.clear()
                bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                bsdf.location = (0, 0)
                bsdf.inputs['Base Color'].default_value = (0.35, 0.20, 0.08, 1.0)
                bsdf.inputs['Roughness'].default_value = 0.65
                out = nodes.new(type='ShaderNodeOutputMaterial')
                out.location = (200, 0)
                boat_mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
            if boat_obj.data.materials:
                boat_obj.data.materials[0] = boat_mat
            else:
                boat_obj.data.materials.append(boat_mat)

            boat_obj.location = (0, 0, 0.75)

        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in context.selected_objects:
            if obj != boat_obj:
                obj.select_set(False)
        boat_obj.select_set(True)
        context.view_layer.objects.active = boat_obj
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        boat_obj.location.x = 0.0
        boat_obj.location.y = 0.0

        # --- Follow Path constraint for animation ---
        river_curve.data.use_path = True
        path_duration = max(2, int(250.0 / max(flow_speed, 0.01)))
        river_curve.data.path_duration = path_duration
        try:
            river_curve.data.driver_remove("eval_time")
        except TypeError:
            pass
        fcurve = river_curve.data.driver_add("eval_time")
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        driver.expression = f"frame % {path_duration}"
        follow_constraint = boat_obj.constraints.new(type='FOLLOW_PATH')
        follow_constraint.name = "CG_Boat_FollowPath"
        follow_constraint.target = river_curve
        follow_constraint.use_curve_follow = True
        follow_constraint.forward_axis = 'TRACK_NEGATIVE_Y'
        follow_constraint.up_axis = 'UP_Z'
        follow_constraint.use_fixed_location = False

        # --- Place boat at the river start with a small random head start ---
        import random as _random

        start_factor = 0.0
        head_start = _random.uniform(0.0, path_duration * 0.3)
        follow_constraint.offset = start_factor * path_duration - head_start

        # Select the boat
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in context.selected_objects:
            if obj != boat_obj:
                obj.select_set(False)
        boat_obj.select_set(True)
        context.view_layer.objects.active = boat_obj

        self.report({'INFO'},
            f"Boat on '{river_curve.name}'. Press Space to play animation.")
        return {'FINISHED'}
