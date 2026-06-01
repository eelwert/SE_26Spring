import bpy

# dA_add
# from .constants import TEMPLATE_ENUM_ITEMS
from .constants import (
    CITY_3D_ASSET_ENUM_ITEMS,
    PAVEMENT_TEXTURE_ENUM_ITEMS,
    ROAD_TEXTURE_ENUM_ITEMS,
    TEMPLATE_ENUM_ITEMS,
)
from .layout_template_constants import LAYOUT_TEMPLATE_ENUM_ITEMS


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


    # dA_add
    bpy.types.Scene.city_template_id = bpy.props.EnumProperty(
        name="Scene Template",
        description="Select a predefined scene template",
        items=TEMPLATE_ENUM_ITEMS,
        default="0",
    )
    bpy.types.Scene.layout_template_id = bpy.props.EnumProperty(
        name="Layout Template",
        description="Select an experimental source mesh layout template",
        items=LAYOUT_TEMPLATE_ENUM_ITEMS,
        default="linear_blocks",
    )
    bpy.types.Scene.layout_template_rows = bpy.props.IntProperty(
        name="Rows",
        description="Number of block rows to create before applying the City Generator node group",
        default=1,
        min=1,
        max=6,
    )
    bpy.types.Scene.layout_template_columns = bpy.props.IntProperty(
        name="Columns",
        description="Number of block columns to create before applying the City Generator node group",
        default=2,
        min=1,
        max=6,
    )
    bpy.types.Scene.layout_template_clear_previous = bpy.props.BoolProperty(
        name="Replace Previous Layout",
        description="Remove layout objects generated by this experimental feature before creating a new one",
        default=True,
    )
    bpy.types.Scene.road_texture_id = bpy.props.EnumProperty(
        name="Road Texture",
        description="Select road texture asset",
        items=ROAD_TEXTURE_ENUM_ITEMS,
        default="road_4_clean",
    )
    bpy.types.Scene.pavement_texture_id = bpy.props.EnumProperty(
        name="Pavement Texture",
        description="Select pavement texture asset",
        items=PAVEMENT_TEXTURE_ENUM_ITEMS,
        default="pavement_25",
    )

    # dA_5_add
    bpy.types.Scene.added_3d_asset_id = bpy.props.EnumProperty(
        name="Added 3D Asset",
        description="Select an added 3D city furniture asset",
        items=CITY_3D_ASSET_ENUM_ITEMS,
        default="wooden_picnic_table",
    )
    bpy.types.Scene.added_3d_asset_min_count = bpy.props.IntProperty(
        name="Min Count",
        description="Minimum number of instances per street segment",
        default=3,
        min=1,
        max=200,
    )
    bpy.types.Scene.added_3d_asset_max_count = bpy.props.IntProperty(
        name="Max Count",
        description="Maximum number of instances per street segment",
        default=6,
        min=1,
        max=200,
    )
    bpy.types.Scene.added_3d_asset_spacing = bpy.props.FloatProperty(
        name="Spacing",
        description="Strict distance in non-random layout; minimum distance in random layout",
        default=5.0,
        min=0.5,
        max=200.0,
        subtype="DISTANCE",
    )
    # dA_5_add
    bpy.types.Scene.added_3d_asset_randomize = bpy.props.BoolProperty(
        name="Random Layout",
        description="Randomize placement within each street segment",
        default=False,
    )
    bpy.types.Scene.added_3d_asset_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Uniform scale for generated 3D asset instances",
        default=1.0,
        min=0.01,
        max=20.0,
    )
    bpy.types.Scene.added_3d_asset_placement_offset = bpy.props.FloatProperty(
        name="Placement Offset",
        description="Move generated assets inward with positive values or outward with negative values",
        default=0.0,
        min=-20.0,
        max=20.0,
        subtype="DISTANCE",
    )
    bpy.types.Scene.added_3d_asset_clear_previous = bpy.props.BoolProperty(
        name="Replace Same Asset",
        description="Remove previously generated instances of the same 3D asset before applying the current one",
        default=True,
    )
    bpy.types.Scene.added_3d_group_edit_min_count = bpy.props.IntProperty(
        name="Min Count",
        description="Minimum number of instances for the selected generated 3D asset group",
        default=3,
        min=1,
        max=200,
    )
    bpy.types.Scene.added_3d_group_edit_max_count = bpy.props.IntProperty(
        name="Max Count",
        description="Maximum number of instances for the selected generated 3D asset group",
        default=6,
        min=1,
        max=200,
    )
    bpy.types.Scene.added_3d_group_edit_spacing = bpy.props.FloatProperty(
        name="Spacing",
        description="Center-to-center spacing for the selected generated 3D asset group",
        default=5.0,
        min=0.5,
        max=200.0,
        subtype="DISTANCE",
    )
    bpy.types.Scene.added_3d_group_edit_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Uniform scale for the selected generated 3D asset group",
        default=1.0,
        min=0.01,
        max=20.0,
    )
    bpy.types.Scene.added_3d_group_edit_placement_offset = bpy.props.FloatProperty(
        name="Placement Offset",
        description="Move the selected generated 3D asset group inward with positive values or outward with negative values",
        default=0.0,
        min=-20.0,
        max=20.0,
        subtype="DISTANCE",
    )
    bpy.types.Scene.added_3d_active_group_id = bpy.props.StringProperty(
        name="Active Added 3D Group",
        description="Internal id of the selected generated 3D asset group",
        default="",
    )



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


    # dA_add
    del bpy.types.Scene.city_template_id
    del bpy.types.Scene.layout_template_id
    del bpy.types.Scene.layout_template_rows
    del bpy.types.Scene.layout_template_columns
    del bpy.types.Scene.layout_template_clear_previous
    del bpy.types.Scene.road_texture_id
    del bpy.types.Scene.pavement_texture_id
    # dA_5_add
    del bpy.types.Scene.added_3d_asset_id
    del bpy.types.Scene.added_3d_asset_min_count
    del bpy.types.Scene.added_3d_asset_max_count
    del bpy.types.Scene.added_3d_asset_spacing
    del bpy.types.Scene.added_3d_asset_randomize
    del bpy.types.Scene.added_3d_asset_scale
    del bpy.types.Scene.added_3d_asset_placement_offset
    del bpy.types.Scene.added_3d_asset_clear_previous
    del bpy.types.Scene.added_3d_group_edit_min_count
    del bpy.types.Scene.added_3d_group_edit_max_count
    del bpy.types.Scene.added_3d_group_edit_spacing
    del bpy.types.Scene.added_3d_group_edit_scale
    del bpy.types.Scene.added_3d_group_edit_placement_offset
    del bpy.types.Scene.added_3d_active_group_id

    del bpy.types.Scene.room_seed
    del bpy.types.Scene.close_roller_shutter
    del bpy.types.Scene.close_curtains
    del bpy.types.Scene.curtain_shutter_seed
    del bpy.types.Scene.randomise_hue
    del bpy.types.Scene.change_hue
    del bpy.types.Scene.emission_strength
    del bpy.types.Scene.light_probability
    del bpy.types.Scene.seed
