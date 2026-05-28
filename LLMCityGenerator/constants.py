import os

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_FILE = "City_Generator2.0.blend"



TEMPLATE_SOCKET_MAP = {
    "road_width": "Socket_9",
    "lane_amount": "Socket_12",
    "sidewalk_scale": "Socket_16",
    "road_material": "Socket_57",
    "sidewalk_material": "Socket_59",
    "tree_collection": "Socket_166",
    "tree_distance": "Socket_171",
    "tree_min_scale": "Socket_182",
    "tree_max_scale": "Socket_183",
    "sidewalk_asset_collection": "Socket_69",
    "sidewalk_asset_probability": "Socket_72",
    "sidewalk_asset_distance": "Socket_73",
}

SCENE_TEMPLATES = {
    "0": {
        "label": "Waterfront Block",
        "description": "Slow road, dense trees, waterfront seats.",
        "road_width": 16,
        "lane_amount": 2,
        "sidewalk_scale": 7.0,
        "road_material": "CityGen_Streets",
        "road_color": (0.06, 0.065, 0.07, 1.0),
        "tree_collection": "CG_Template_Trees_Waterfront",
        "tree_objects": ("Tree 04 MR.001", "Tree 04 MR.002"),
        "tree_distance": 12.0,
        "tree_min_scale": 0.8,
        "tree_max_scale": 1.25,
        "sidewalk_asset_collection": "Universal side walk assets",
        "sidewalk_asset_probability": 0.6,
        "sidewalk_asset_distance": 12.0,
    },
    "1": {
        "label": "Commercial Street",
        "description": "Wide walking area, regular trees, metal seats.",
        "road_width": 14,
        "lane_amount": 1,
        "sidewalk_scale": 6.0,
        "road_material": "CityGenconcrete",
        "road_color": (0.22, 0.20, 0.18, 1.0),
        "tree_collection": "CG_Template_Trees_Commercial",
        "tree_objects": ("Tree 04 MR.003", "Tree 04 MR.004"),
        "tree_distance": 14.0,
        "tree_min_scale": 0.85,
        "tree_max_scale": 1.2,
        "sidewalk_asset_collection": "Asian side walk assets",
        "sidewalk_asset_probability": 0.9,
        "sidewalk_asset_distance": 8.0,
    },
    "2": {
        "label": "Transit Hub",
        "description": "Wide roads, sparse trees, transit furniture.",
        "road_width": 20,
        "lane_amount": 4,
        "sidewalk_scale": 8.5,
        "road_material": "CityGensimple concrete 1",
        "road_color": (0.32, 0.33, 0.32, 1.0),
        "tree_collection": "CG_Template_Trees_Transit",
        "tree_objects": ("Tree 04 MR.001", "Tree 04 MR.005"),
        "tree_distance": 15.0,
        "tree_min_scale": 0.75,
        "tree_max_scale": 1.1,
        "sidewalk_asset_collection": "Universal side walk assets",
        "sidewalk_asset_probability": 0.35,
        "sidewalk_asset_distance": 20.0,
    },
}

TEMPLATE_ENUM_ITEMS = tuple(
    (template_id, f"{template_id} - {template['label']}", template["description"])
    for template_id, template in SCENE_TEMPLATES.items()
)
