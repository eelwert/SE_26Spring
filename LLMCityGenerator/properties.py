import bpy


# --- Update callbacks for Scene properties ---

def update_customheight(self, context):
    value = context.scene.height_value
    if context.object.mode == 'EDIT' and context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = context.object.data
        for poly in mesh.polygons:
            if poly.select:
                if "Custom_Height" not in mesh.attributes:
                    mesh.attributes.new(name="Custom_Height", type='INT', domain='FACE')
                mesh.attributes["Custom_Height"].data[poly.index].value = value
        bpy.ops.object.mode_set(mode='EDIT')


def update_custom_facade_asset_index(self, context):
    value = context.scene.custom_facade_asset_index
    if context.object.mode == 'EDIT' and context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = context.object.data
        for poly in mesh.polygons:
            if poly.select:
                if "custom Facade Asset index" not in mesh.attributes:
                    mesh.attributes.new(name="custom Facade Asset index", type='INT', domain='FACE')
                mesh.attributes["custom Facade Asset index"].data[poly.index].value = value
        bpy.ops.object.mode_set(mode='EDIT')


def update_custom_ground_asset_index(self, context):
    value = context.scene.custom_ground_asset
    if context.object.mode == 'EDIT' and context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = context.object.data
        for poly in mesh.polygons:
            if poly.select:
                if "custom Ground Floor Asset index" not in mesh.attributes:
                    mesh.attributes.new(name="custom Ground Floor Asset index", type='INT', domain='FACE')
                mesh.attributes["custom Ground Floor Asset index"].data[poly.index].value = value
        bpy.ops.object.mode_set(mode='EDIT')


def update_zshape_amount(self, context):
    value = context.scene.zshape
    if context.object.mode == 'EDIT' and context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = context.object.data
        for poly in mesh.polygons:
            if poly.select:
                if "Zshape Amount" not in mesh.attributes:
                    mesh.attributes.new(name="Zshape Amount", type='INT', domain='FACE')
                mesh.attributes["Zshape Amount"].data[poly.index].value = value
        bpy.ops.object.mode_set(mode='EDIT')


def update_zshape_height(self, context):
    value = context.scene.zshape_height
    if context.object.mode == 'EDIT' and context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = context.object.data
        for poly in mesh.polygons:
            if poly.select:
                if "Zshape Height" not in mesh.attributes:
                    mesh.attributes.new(name="Zshape Height", type='INT', domain='FACE')
                mesh.attributes["Zshape Height"].data[poly.index].value = value
        bpy.ops.object.mode_set(mode='EDIT')


def update_zshape_insert(self, context):
    value = context.scene.zshape_insert
    if context.object.mode == 'EDIT' and context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = context.object.data
        for poly in mesh.polygons:
            if poly.select:
                # Create a float attribute if it doesn't exist
                if "Zshape insert" not in mesh.attributes:
                    mesh.attributes.new(name="Zshape insert", type='FLOAT', domain='FACE')
                # Assign the float value to the attribute
                mesh.attributes["Zshape insert"].data[poly.index].value = value
        bpy.ops.object.mode_set(mode='EDIT')


# --- Emission settings ---

def update_emission_settings(self, context):
    # List of materials to update
    material_names = [
        "CityGen_Red_Emission",
        "CityGen_Green_Emission",
        "CityGen_Blue_Emission",
        "CityGenLamp_Emission",
        "CityGen_Yellow_Emission"
    ]

    # Get the shared emission strength value
    emission_strength = context.scene.global_emission_strength

    # Update each material's emission strength
    for mat_name in material_names:
        mat = bpy.data.materials.get(mat_name)
        if mat is not None:
            node = mat.node_tree.nodes.get("Emission")  # Assuming the node is named "Emission"
            if node is not None:
                node.inputs[1].default_value = emission_strength  # Assuming input 1 is Emission Strength


def add_emission_properties():
    bpy.types.Scene.global_emission_strength = bpy.props.FloatProperty(
        name="Global Emission Strength",
        description="Adjust the emission strength for all CityGen emission materials",
        default=1.0,
        min=0.0,
        max=100.0,
        update=update_emission_settings
    )


# --- Interior parallax update ---

def update_parallax_settings(scene, context=None):
    # List of relevant materials
    material_names = [
        "CityGen_Interior_Room_Shader",
        "CityGen_Interior_Office_Shader",
        "CityGen_Interior_Store_Shader"
    ]

    # Iterate through materials and update their node inputs
    for mat_name in material_names:
        mat = bpy.data.materials.get(mat_name)
        if mat is not None:
            node = mat.node_tree.nodes.get("Group")
            if node is not None:
                node.inputs[0].default_value = scene.room_seed
                node.inputs[1].default_value = scene.close_roller_shutter
                node.inputs[2].default_value = scene.close_curtains
                node.inputs[3].default_value = scene.curtain_shutter_seed
                node.inputs[4].default_value = scene.randomise_hue
                node.inputs[5].default_value = scene.change_hue
                node.inputs[6].default_value = scene.emission_strength
                node.inputs[7].default_value = scene.light_probability
                node.inputs[8].default_value = scene.seed


def property_update_callback(self, context):
    update_parallax_settings(context.scene)


def add_custom_properties():
    bpy.types.Scene.room_seed = bpy.props.FloatProperty(
        name="Room Seed",
        description="Adjust the room seed of all materials",
        default=0.0,
        min=0.0,
        max=100.0,
        update=property_update_callback
    )
    bpy.types.Scene.close_roller_shutter = bpy.props.FloatProperty(
        name="Close Roller Shutter",
        description="Adjust the roller shutter closure of all materials",
        default=0.0,
        min=0.0,
        max=1.0,
        update=property_update_callback
    )
    bpy.types.Scene.close_curtains = bpy.props.FloatProperty(
        name="Close Curtains",
        description="Adjust the curtain closure of all materials",
        default=0.5,
        min=0.0,
        max=1.0,
        update=property_update_callback
    )
    bpy.types.Scene.curtain_shutter_seed = bpy.props.FloatProperty(
        name="Curtain | Shutter Seed",
        description="Adjust the curtain or shutter seed of all materials",
        default=0.0,
        min=0.0,
        max=100.0,
        update=property_update_callback
    )
    bpy.types.Scene.randomise_hue = bpy.props.FloatProperty(
        name="Randomise Hue",
        description="Randomise the hue of all materials",
        default=0.0,
        min=0.0,
        max=1.0,
        update=property_update_callback
    )
    bpy.types.Scene.change_hue = bpy.props.FloatProperty(
        name="Change Hue",
        description="Adjust the hue change of all materials",
        default=0.5,
        min=-1.0,
        max=1.0,
        update=property_update_callback
    )
    bpy.types.Scene.emission_strength = bpy.props.FloatProperty(
        name="Emission Strength",
        description="Adjust the emission strength of all materials",
        default=0.0,
        min=0.0,
        max=100.0,
        update=property_update_callback
    )
    bpy.types.Scene.light_probability = bpy.props.FloatProperty(
        name="Light Probability",
        description="Adjust the light probability of all materials",
        default=0.5,
        min=0.0,
        max=1.0,
        update=property_update_callback
    )
    bpy.types.Scene.seed = bpy.props.FloatProperty(
        name="Seed",
        description="Adjust the seed of all materials",
        default=0.0,
        min=0.0,
        max=100.0,
        update=property_update_callback
    )


# --- Scene property registration (called from register) ---

def register_scene_properties():
    """Register all bpy.types.Scene custom properties."""
    bpy.types.Scene.height_value = bpy.props.IntProperty(
        name="Height Value",
        default=0,
        min=0,
        max=1000,
        update=update_customheight
    )

    bpy.types.Scene.custom_facade_asset_index = bpy.props.IntProperty(
        name="Custom Facade Asset Index",
        default=0,
        min=0,
        max=500,
        update=update_custom_facade_asset_index
    )

    bpy.types.Scene.custom_ground_asset = bpy.props.IntProperty(
        name="Custom Ground Floor Asset Index",
        default=0,
        min=0,
        max=500,
        update=update_custom_ground_asset_index
    )

    bpy.types.Scene.assign_low_poly = bpy.props.IntProperty(
        name="Assign Low Poly",
        default=0,
        min=0,
        max=500,
        update=update_custom_ground_asset_index
    )

    bpy.types.Scene.zshape = bpy.props.IntProperty(
        name="Zshape Amount",
        default=0,
        min=0,
        max=500,
        update=update_zshape_amount
    )

    bpy.types.Scene.zshape_height = bpy.props.IntProperty(
        name="Zshape Height",
        default=0,
        min=0,
        max=500,
        update=update_zshape_height
    )

    bpy.types.Scene.zshape_insert = bpy.props.FloatProperty(
        name="Zshape Insert",
        default=0,
        min=-0.75,
        max=500,
        subtype='DISTANCE',
        update=update_zshape_insert
    )

    # --- Eco scene properties ---
    # Terrain
    bpy.types.Scene.cg_terrain_hill_height = bpy.props.FloatProperty(
        name="Hill Height",
        description="Maximum height of terrain hills",
        default=60.0, min=0.0, max=500.0, subtype='DISTANCE')
    bpy.types.Scene.cg_terrain_noise_scale = bpy.props.FloatProperty(
        name="Noise Scale",
        description="Scale of the noise texture (larger = fewer/broader hills, 8-15 for 2-3 hills)",
        default=8.0, min=0.1, max=25.0)
    bpy.types.Scene.cg_terrain_noise_detail = bpy.props.IntProperty(
        name="Noise Detail",
        description="Detail level of noise texture (0 = smooth dome hills, 0-16)",
        default=0, min=0, max=16)
    bpy.types.Scene.cg_terrain_grid_size = bpy.props.FloatProperty(
        name="Grid Size",
        description="Size of the terrain grid",
        default=200.0, min=50.0, max=1000.0, subtype='DISTANCE')
    bpy.types.Scene.cg_terrain_subdivisions = bpy.props.IntProperty(
        name="Subdivisions",
        description="Number of grid subdivisions per axis",
        default=50, min=10, max=200)
    bpy.types.Scene.cg_terrain_detail_height = bpy.props.FloatProperty(
        name="Detail Height",
        description="Height of the secondary noise detail layer",
        default=5.0, min=0.0, max=100.0, subtype='DISTANCE')
    bpy.types.Scene.cg_terrain_detail_enabled = bpy.props.BoolProperty(
        name="Enable Detail Layer",
        description="Add a second noise layer for fine surface details",
        default=False)
    bpy.types.Scene.cg_terrain_apply_to_city = bpy.props.BoolProperty(
        name="Apply to City Grid",
        description="Also apply terrain displacement to the city grid object",
        default=False)
    bpy.types.Scene.cg_terrain_low_color = bpy.props.FloatVectorProperty(
        name="Low Color",
        description="Color for low ground areas",
        default=(0.15, 0.35, 0.08, 1.0),
        min=0.0, max=1.0, subtype='COLOR', size=4)
    bpy.types.Scene.cg_terrain_high_color = bpy.props.FloatVectorProperty(
        name="High Color",
        description="Color for hill peaks",
        default=(0.45, 0.33, 0.18, 1.0),
        min=0.0, max=1.0, subtype='COLOR', size=4)

    # Lake
    bpy.types.Scene.cg_lake_size = bpy.props.FloatProperty(
        name="Lake Size",
        description="Radius of the lake",
        default=20.0, min=1.0, max=100.0, subtype='DISTANCE')
    bpy.types.Scene.cg_lake_vertices = bpy.props.IntProperty(
        name="Vertices",
        description="Number of vertices for circular lake",
        default=32, min=8, max=128)
    bpy.types.Scene.cg_lake_ripple_strength = bpy.props.FloatProperty(
        name="Ripple Strength",
        description="Strength of water ripple normal effect",
        default=0.05, min=0.0, max=1.0, subtype='FACTOR')
    bpy.types.Scene.cg_lake_ripple_scale = bpy.props.FloatProperty(
        name="Ripple Scale",
        description="Scale of ripple noise texture",
        default=2.0, min=0.1, max=10.0)
    bpy.types.Scene.cg_lake_water_color = bpy.props.FloatVectorProperty(
        name="Water Color",
        description="Base color of the water",
        default=(0.05, 0.2, 0.4, 1.0),
        min=0.0, max=1.0,
        subtype='COLOR',
        size=4)

    # River & Boat
    bpy.types.Scene.cg_river_width = bpy.props.FloatProperty(
        name="River Width",
        description="Width of the river surface",
        default=3.0, min=0.5, max=20.0, subtype='DISTANCE')
    bpy.types.Scene.cg_river_flow_speed = bpy.props.FloatProperty(
        name="Flow Speed",
        description="Speed of river flow and boat movement",
        default=1.0, min=0.1, max=5.0)
    bpy.types.Scene.cg_boat_scale = bpy.props.FloatProperty(
        name="Boat Scale",
        description="Scale of the boat model",
        default=1.0, min=0.1, max=5.0)

    add_custom_properties()
    # Note: add_emission_properties() is not called here as in the original code
    # It is defined but never activated in register().


def unregister_scene_properties():
    """Delete all bpy.types.Scene custom properties."""
    del bpy.types.Scene.height_value
    del bpy.types.Scene.custom_facade_asset_index
    del bpy.types.Scene.custom_ground_asset
    del bpy.types.Scene.assign_low_poly
    del bpy.types.Scene.zshape
    del bpy.types.Scene.zshape_height
    del bpy.types.Scene.zshape_insert

    del bpy.types.Scene.room_seed
    del bpy.types.Scene.close_roller_shutter
    del bpy.types.Scene.close_curtains
    del bpy.types.Scene.curtain_shutter_seed
    del bpy.types.Scene.randomise_hue
    del bpy.types.Scene.change_hue
    del bpy.types.Scene.emission_strength
    del bpy.types.Scene.light_probability
    del bpy.types.Scene.seed

    # Eco scene properties
    del bpy.types.Scene.cg_terrain_hill_height
    del bpy.types.Scene.cg_terrain_noise_scale
    del bpy.types.Scene.cg_terrain_noise_detail
    del bpy.types.Scene.cg_terrain_grid_size
    del bpy.types.Scene.cg_terrain_subdivisions
    del bpy.types.Scene.cg_terrain_detail_height
    del bpy.types.Scene.cg_terrain_detail_enabled
    del bpy.types.Scene.cg_terrain_apply_to_city
    del bpy.types.Scene.cg_terrain_low_color
    del bpy.types.Scene.cg_terrain_high_color
    del bpy.types.Scene.cg_lake_size
    del bpy.types.Scene.cg_lake_vertices
    del bpy.types.Scene.cg_lake_ripple_strength
    del bpy.types.Scene.cg_lake_ripple_scale
    del bpy.types.Scene.cg_lake_water_color
    del bpy.types.Scene.cg_river_width
    del bpy.types.Scene.cg_river_flow_speed
    del bpy.types.Scene.cg_boat_scale
