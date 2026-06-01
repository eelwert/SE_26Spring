from .constants import CITY_3D_ASSETS, PAVEMENT_TEXTURE_ASSETS, ROAD_TEXTURE_ASSETS, SCENE_TEMPLATES
from .furniture_asset_engine import apply_added_3d_asset_function
from .layout_template_constants import LAYOUT_TEMPLATE_ASSETS
from .layout_template_engine import apply_layout_template_function
from .road_texture_engine import apply_pavement_texture_function, apply_road_texture_function
from .template_engine import apply_scene_template_function


def _template_enum():
    return list(SCENE_TEMPLATES.keys())


def _layout_template_enum():
    return list(LAYOUT_TEMPLATE_ASSETS.keys())


def _road_texture_enum():
    return list(ROAD_TEXTURE_ASSETS.keys())


def _pavement_texture_enum():
    return list(PAVEMENT_TEXTURE_ASSETS.keys())


# dA_5_add
def _added_3d_asset_enum():
    return list(CITY_3D_ASSETS.keys())


LLM_FUNCTION_SPECS = {
    "apply_scene_template": {
        "name": "apply_scene_template",
        "description": (
            "Apply a predefined city scene detail template to the active Blender City Generator object. "
            "The template changes coordinated scene details such as road material, tree type, sidewalk assets, "
            "tree spacing, and street-side furniture settings."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "enum": _template_enum(),
                    "description": "Template id. Use 0 for Waterfront Block, 1 for Commercial Street, 2 for Transit Hub.",
                }
            },
            "required": ["template_id"],
        },
        "returns": {
            "type": "object",
            "description": "Execution result containing template_id, template_name, applied fields, and warnings.",
        },
    },
    "apply_layout_template": {
        "name": "apply_layout_template",
        "description": (
            "Create an experimental source mesh layout for the active Blender scene, then apply the "
            "City Generator node group. This is separate from scene style templates and can control "
            "the number of generated city blocks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "layout_id": {
                    "type": "string",
                    "enum": _layout_template_enum(),
                    "description": "Layout template id. Currently linear_blocks creates side-by-side city blocks.",
                },
                "rows": {
                    "type": "integer",
                    "description": "Number of block rows to create.",
                },
                "columns": {
                    "type": "integer",
                    "description": "Number of block columns to create.",
                },
                "clear_previous": {
                    "type": "boolean",
                    "description": "Whether to remove previously generated experimental layout objects before applying.",
                },
            },
            "required": ["layout_id", "rows", "columns"],
        },
        "returns": {
            "type": "object",
            "description": "Execution result containing layout_id, rows, columns, generated object names, and mesh names.",
        },
    },
    "apply_road_texture": {
        "name": "apply_road_texture",
        "description": "Apply a selected 2D road texture asset to the active Blender City Generator object.",
        "parameters": {
            "type": "object",
            "properties": {
                "texture_id": {
                    "type": "string",
                    "enum": _road_texture_enum(),
                    "description": "Road texture id, such as road_4_clean, road_8_dirty, road_11_dirty, or spongebob_fun.",
                }
            },
            "required": ["texture_id"],
        },
        "returns": {
            "type": "object",
            "description": "Execution result containing texture_id, texture_name, material_name, applied fields, and warnings.",
        },
    },
    "apply_pavement_texture": {
        "name": "apply_pavement_texture",
        "description": "Apply a selected 2D pavement/sidewalk texture asset to the active Blender City Generator object.",
        "parameters": {
            "type": "object",
            "properties": {
                "texture_id": {
                    "type": "string",
                    "enum": _pavement_texture_enum(),
                    "description": "Pavement texture id, such as pavement_25, tiles_038, or patrick_fun.",
                }
            },
            "required": ["texture_id"],
        },
        "returns": {
            "type": "object",
            "description": "Execution result containing texture_id, texture_name, material_name, applied fields, and warnings.",
        },
    },
    # dA_5_add
    "apply_added_3d_asset": {
        "name": "apply_added_3d_asset",
        "description": (
            "Load an added 3D city furniture asset from the plugin asset library and instantiate it "
            "along street-side sidewalk segments around the active City Generator object by count range and spacing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "string",
                    "enum": _added_3d_asset_enum(),
                    "description": "3D asset id, such as wooden_picnic_table, small_lpg_tank, or rubber_duck_toy.",
                },
                "min_count": {
                    "type": "integer",
                    "description": "Minimum number of instances to create per street segment.",
                },
                "max_count": {
                    "type": "integer",
                    "description": "Maximum number of instances to create per street segment.",
                },
                "spacing": {
                    "type": "number",
                    "description": "Strict distance in non-random layout; minimum distance in random layout.",
                },
                "scale": {
                    "type": "number",
                    "description": "Uniform instance scale.",
                },
                "placement_offset": {
                    "type": "number",
                    "description": "Move placement inward with positive values or outward with negative values, measured in Blender meters.",
                },
                "randomize": {
                    "type": "boolean",
                    "description": "Whether to randomize placement within each street segment.",
                },
                "clear_previous": {
                    "type": "boolean",
                    "description": "Whether to remove previously generated instances of the same 3D asset before applying.",
                },
            },
            "required": ["asset_id"],
        },
        "returns": {
            "type": "object",
            "description": "Execution result containing asset_id, asset_name, count range, spacing, and created instance names.",
        },
    },
}


LLM_FUNCTION_HANDLERS = {
    "apply_scene_template": apply_scene_template_function,
    "apply_layout_template": apply_layout_template_function,
    "apply_road_texture": apply_road_texture_function,
    "apply_pavement_texture": apply_pavement_texture_function,
    # dA_5_add
    "apply_added_3d_asset": apply_added_3d_asset_function,
}


def get_llm_function_specs():
    """Return function specs that can be sent to the LLM."""
    return list(LLM_FUNCTION_SPECS.values())


def call_llm_function(context, function_name, arguments):
    """Dispatch an LLM-selected function call to the matching Blender implementation."""
    handler = LLM_FUNCTION_HANDLERS.get(function_name)
    if handler is None:
        raise ValueError(f"Unknown LLM function: {function_name}")

    if arguments is None:
        arguments = {}

    return handler(context, **arguments)
