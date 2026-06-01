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


# --- LLM result line PropertyGroup ---

class CG_LLMResultLine(bpy.types.PropertyGroup):
    text: bpy.props.StringProperty(name="Line", default="")


# --- LLM properties ---

def _update_llm_text(self, context):
    """Placeholder update callback for llm_text_input."""


# --- Dynamics-related scene properties ---


def _dynamics_property_update(self, context):
    """Placeholder update callback for dynamics properties."""
    pass


def _add_dynamics_properties():
    """Register dynamics-related scene properties."""
    bpy.types.Scene.cg_car_density = bpy.props.IntProperty(
        name="Car Density",
        description="Number of cars per road segment",
        default=10,
        min=0,
        max=200,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_car_speed_min = bpy.props.FloatProperty(
        name="Min Speed",
        description="Minimum car speed (m/s)",
        default=2.0,
        min=0.5,
        max=20.0,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_car_speed_max = bpy.props.FloatProperty(
        name="Max Speed",
        description="Maximum car speed (m/s)",
        default=8.0,
        min=1.0,
        max=25.0,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_pedestrian_density = bpy.props.IntProperty(
        name="Pedestrian Density",
        description="Number of pedestrians per sidewalk segment",
        default=5,
        min=0,
        max=200,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_pedestrian_speed = bpy.props.FloatProperty(
        name="Walking Speed",
        description="Pedestrian walking speed (m/s)",
        default=1.5,
        min=0.5,
        max=5.0,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_traffic_light_green = bpy.props.IntProperty(
        name="Green Duration",
        description="Green light duration in frames",
        default=120,
        min=30,
        max=600,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_traffic_light_yellow = bpy.props.IntProperty(
        name="Yellow Duration",
        description="Yellow light duration in frames",
        default=30,
        min=10,
        max=120,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_traffic_light_red = bpy.props.IntProperty(
        name="Red Duration",
        description="Red light duration in frames",
        default=120,
        min=30,
        max=600,
        update=_dynamics_property_update,
    )
    bpy.types.Scene.cg_dynamics_active = bpy.props.BoolProperty(
        name="Dynamics Active",
        description="Whether the dynamic simulation is currently active",
        default=False,
    )


# --- Layout-related scene properties ---


def _add_layout_properties():
    """Register layout-related scene properties."""
    bpy.types.Scene.cg_layout_points_text = bpy.props.StringProperty(
        name="",
        description="Coordinate points, e.g. 0,0;50,0;50,50;0,50",
        default="",
    )
    bpy.types.Scene.cg_sketch_image_path = bpy.props.StringProperty(
        name="",
        description="Path to sketch image file",
        default="",
        subtype="FILE_PATH",
    )
    bpy.types.Scene.cg_sketch_threshold = bpy.props.FloatProperty(
        name="Threshold",
        description="Edge detection threshold",
        default=0.5,
        min=0.1,
        max=1.0,
    )
    bpy.types.Scene.cg_sketch_min_line_length = bpy.props.IntProperty(
        name="Min Length",
        description="Minimum line length in pixels",
        default=30,
        min=5,
        max=500,
    )


def _remove_layout_properties():
    """Remove layout-related scene properties."""
    del bpy.types.Scene.cg_layout_points_text
    del bpy.types.Scene.cg_sketch_image_path
    del bpy.types.Scene.cg_sketch_threshold
    del bpy.types.Scene.cg_sketch_min_line_length


def _remove_dynamics_properties():
    """Remove dynamics-related scene properties."""
    del bpy.types.Scene.cg_car_density
    del bpy.types.Scene.cg_car_speed_min
    del bpy.types.Scene.cg_car_speed_max
    del bpy.types.Scene.cg_pedestrian_density
    del bpy.types.Scene.cg_pedestrian_speed
    del bpy.types.Scene.cg_traffic_light_green
    del bpy.types.Scene.cg_traffic_light_yellow
    del bpy.types.Scene.cg_traffic_light_red
    del bpy.types.Scene.cg_dynamics_active


# --- Scene property registration (called from register) ---

def register_scene_properties():
    """Register all bpy.types.Scene custom properties."""

    # LLM control properties
    bpy.types.Scene.llm_text_input = bpy.props.StringProperty(
        name="Instruction",
        description="Describe the city scene changes you want in natural language",
        default="",
        update=_update_llm_text,
    )
    bpy.types.Scene.llm_api_key = bpy.props.StringProperty(
        name="API Key",
        description="DeepSeek API Key (or set DEEPSEEK_API_KEY environment variable)",
        default="",
        subtype='PASSWORD',
    )
    bpy.types.Scene.llm_result = bpy.props.StringProperty(
        name="LLM Result",
        description="Result of the last LLM execution",
        default="",
    )
    bpy.types.Scene.llm_status = bpy.props.StringProperty(
        name="LLM Status",
        description="Status of the LLM execution (idle/calling/executing/done/error)",
        default="idle",
    )
    bpy.types.Scene.llm_template_id = bpy.props.IntProperty(
        name="Template ID",
        description="Last applied template ID",
        default=0,
        min=0,
        max=9,
    )
    bpy.types.Scene.llm_template_name = bpy.props.StringProperty(
        name="Template Name",
        description="Name of the last applied template",
        default="",
    )
    bpy.types.Scene.llm_weather = bpy.props.StringProperty(
        name="LLM Weather",
        description="Weather set by LLM",
        default="晴",
    )
    bpy.types.Scene.llm_time_of_day = bpy.props.StringProperty(
        name="LLM Time of Day",
        description="Time of day set by LLM",
        default="12:00",
    )
    bpy.types.Scene.llm_result_lines = bpy.props.CollectionProperty(
        type=CG_LLMResultLine,
    )
    bpy.types.Scene.llm_result_index = bpy.props.IntProperty(
        name="Result Index",
        default=0,
    )
    bpy.types.Scene.llm_show_examples = bpy.props.BoolProperty(
        name="Show Examples",
        description="Toggle quick example buttons",
        default=False,
    )

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
        default=15.0, min=0.1, max=30.0)
    bpy.types.Scene.cg_terrain_noise_detail = bpy.props.IntProperty(
        name="Noise Detail",
        description="Detail level of noise texture (0 = smooth dome hills, 0-16)",
        default=0, min=0, max=16)
    bpy.types.Scene.cg_terrain_grid_size = bpy.props.FloatProperty(
        name="Grid Size",
        description="Size of the terrain grid",
        default=50.0, min=20.0, max=500.0, subtype='DISTANCE')
    bpy.types.Scene.cg_terrain_subdivisions = bpy.props.IntProperty(
        name="Subdivisions",
        description="Number of grid subdivisions per axis",
        default=30, min=10, max=200)
    bpy.types.Scene.cg_terrain_detail_height = bpy.props.FloatProperty(
        name="Detail Height",
        description="Height of the secondary noise detail layer",
        default=5.0, min=0.0, max=100.0, subtype='DISTANCE')
    bpy.types.Scene.cg_terrain_detail_enabled = bpy.props.BoolProperty(
        name="Enable Detail Layer",
        description="Add a second noise layer for fine surface details",
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
    bpy.types.Scene.cg_lake_block_size = bpy.props.FloatProperty(
        name="Block Size",
        description="Size of the square ground block containing the lake",
        default=30.0, min=10.0, max=500.0, subtype='DISTANCE')
    bpy.types.Scene.cg_lake_edge_irregularity = bpy.props.FloatProperty(
        name="Edge Irregularity",
        description="Randomness of the lake shoreline (0 = perfect circle, 1 = very irregular)",
        default=0.3, min=0.0, max=1.0, subtype='FACTOR')
    bpy.types.Scene.cg_lake_seed = bpy.props.IntProperty(
        name="Lake Seed",
        description="Random seed for lake shoreline shape",
        default=0, min=0, max=1000)
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
    bpy.types.Scene.cg_river_seed = bpy.props.IntProperty(
        name="River Seed",
        description="Random seed for river path shape",
        default=0, min=0, max=1000)
    bpy.types.Scene.cg_river_flow_speed = bpy.props.FloatProperty(
        name="Flow Speed",
        description="Speed of river flow and boat movement",
        default=1.0, min=0.1, max=5.0)
    bpy.types.Scene.cg_boat_scale = bpy.props.FloatProperty(
        name="Boat Scale",
        description="Scale of the boat model",
        default=1.0, min=0.1, max=5.0)

    add_custom_properties()
    _add_dynamics_properties()
    _add_layout_properties()
    # Note: add_emission_properties() is not called here as in the original code
    # It is defined but never activated in register().


def unregister_scene_properties():
    """Delete all bpy.types.Scene custom properties."""
    # LLM properties
    del bpy.types.Scene.llm_text_input
    del bpy.types.Scene.llm_api_key
    del bpy.types.Scene.llm_result
    del bpy.types.Scene.llm_status
    del bpy.types.Scene.llm_template_id
    del bpy.types.Scene.llm_template_name
    del bpy.types.Scene.llm_weather
    del bpy.types.Scene.llm_time_of_day
    del bpy.types.Scene.llm_result_lines
    del bpy.types.Scene.llm_result_index
    del bpy.types.Scene.llm_show_examples

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
    del bpy.types.Scene.cg_terrain_low_color
    del bpy.types.Scene.cg_terrain_high_color
    del bpy.types.Scene.cg_lake_size
    del bpy.types.Scene.cg_lake_block_size
    del bpy.types.Scene.cg_lake_edge_irregularity
    del bpy.types.Scene.cg_lake_seed
    del bpy.types.Scene.cg_lake_vertices
    del bpy.types.Scene.cg_lake_ripple_strength
    del bpy.types.Scene.cg_lake_ripple_scale
    del bpy.types.Scene.cg_lake_water_color
    del bpy.types.Scene.cg_river_width
    del bpy.types.Scene.cg_river_seed
    del bpy.types.Scene.cg_river_flow_speed
    del bpy.types.Scene.cg_boat_scale

    _remove_dynamics_properties()
    _remove_layout_properties()
