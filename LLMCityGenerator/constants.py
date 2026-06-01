import os

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
BLEND_FILE = "City_Generator2.0.blend"



# --- Dynamic Simulation Constants ---
DYNAMICS_COLLECTION_NAME = "Dynamic_Traffic"
DYNAMICS_ROAD_PATHS_COLLECTION = "Dynamic_Traffic_Paths"
DYNAMICS_SIDEWALK_PATHS_COLLECTION = "Dynamic_Sidewalk_Paths"
DYNAMICS_CARS_COLLECTION = "Dynamic_Cars"
DYNAMICS_PEDESTRIANS_COLLECTION = "Dynamic_Pedestrians"
DYNAMICS_TRAFFIC_LIGHTS_COLLECTION = "Dynamic_Traffic_Lights"

DEFAULT_CAR_DENSITY = 10
DEFAULT_CAR_SPEED_MIN = 2.0
DEFAULT_CAR_SPEED_MAX = 8.0
DEFAULT_PEDESTRIAN_DENSITY = 5
DEFAULT_PEDESTRIAN_SPEED = 1.5
DEFAULT_TRAFFIC_LIGHT_GREEN = 120
DEFAULT_TRAFFIC_LIGHT_YELLOW = 30
DEFAULT_TRAFFIC_LIGHT_RED = 120
DEFAULT_MIN_EDGE_LENGTH = 0.5
DEFAULT_SIDEWALK_OFFSET = 5.0  # outside car lanes (LANE_HALF_WIDTH=2.0)
DEFAULT_CAR_FOLLOW_DISTANCE = 3.0


ROAD_MATERIAL_SOCKET = "Socket_57"
ROAD_UV_SCALE_SOCKET = "Socket_58"
PAVEMENT_MATERIAL_SOCKET = "Socket_59"
PAVEMENT_UV_SCALE_SOCKET = "Socket_60"

ROAD_TEXTURE_ASSETS = {
    "road_4_clean": {
        "label": "清爽沥青路面",
        "material_name": "NKU_Road_4_Clean",
        "base_color": "assets_add/textures/road/road_4/Road 4 clean_BaseColor.jpg",
        "normal": "assets_add/textures/road/road_4/Road 4 clean_Normal.jpg",
        "roughness": "assets_add/textures/road/road_4/Road 4 clean_Roughness.jpg",
        "height": "assets_add/textures/road/road_4/Road 4 clean_Height.jpg",
        "uv_scale": 18.0,
    },
    "road_8_dirty": {
        "label": "旧痕柏油路面",
        "material_name": "NKU_Road_8_Dirty",
        "base_color": "assets_add/textures/road/road_8/Road 8 dirty_BaseColor.jpg",
        "normal": "assets_add/textures/road/road_8/Road 8 dirty_Normal.jpg",
        "roughness": "assets_add/textures/road/road_8/Road 8 dirty_Roughness.jpg",
        "height": "assets_add/textures/road/road_8/Road 8 dirty_Height.jpg",
        "uv_scale": 18.0,
    },
    "road_11_dirty": {
        "label": "重度磨损路面",
        "material_name": "NKU_Road_11_Dirty",
        "base_color": "assets_add/textures/road/road_11/Road 11 dirty_BaseColor.jpg",
        "normal": "assets_add/textures/road/road_11/Road 11 dirty_Normal.jpg",
        "roughness": "assets_add/textures/road/road_11/Road 11 dirty_Roughness.jpg",
        "height": "assets_add/textures/road/road_11/Road 11 dirty_Height.jpg",
        "uv_scale": 18.0,
    },
    "spongebob_fun": {
        "label": "海绵宝宝彩蛋路面",
        "material_name": "NKU_Road_SpongeBob",
        "base_color": "assets_add/textures/road/road_forFun/spongebob_road_basecolor.jpg",
        "normal": None,
        "roughness": None,
        "height": None,
        "uv_scale": 8.0,
    },
}

ROAD_TEXTURE_ENUM_ITEMS = tuple(
    (texture_id, texture["label"], texture["base_color"])
    for texture_id, texture in ROAD_TEXTURE_ASSETS.items()
)

PAVEMENT_TEXTURE_ASSETS = {
    "pavement_25": {
        "label": "灰色方砖人行道",
        "material_name": "NKU_Pavement_25",
        "base_color": "assets_add/textures/pavement/pavement_25/pavement_25_basecolor-2K.png",
        "normal": "assets_add/textures/pavement/pavement_25/pavement_25_normal-2K.png",
        "roughness": "assets_add/textures/pavement/pavement_25/pavement_25_roughness-2K.png",
        "height": None,
        "uv_scale": 8.0,
    },
    "tiles_038": {
        "label": "深灰石砖人行道",
        "material_name": "NKU_Pavement_Tiles_038",
        "base_color": "assets_add/textures/pavement/Tiles038/Tiles038_2K-JPG_Color.jpg",
        "normal": "assets_add/textures/pavement/Tiles038/Tiles038_2K-JPG_NormalGL.jpg",
        "roughness": "assets_add/textures/pavement/Tiles038/Tiles038_2K-JPG_Roughness.jpg",
        "height": "assets_add/textures/pavement/Tiles038/Tiles038_2K-JPG_Displacement.jpg",
        "uv_scale": 8.0,
    },
    "patrick_fun": {
        "label": "派大星彩蛋人行道",
        "material_name": "NKU_Pavement_Patrick",
        "base_color": "assets_add/textures/pavement/pavement_forFun/patrick.jpg",
        "normal": None,
        "roughness": None,
        "height": None,
        "uv_scale": 5.0,
    },
}

PAVEMENT_TEXTURE_ENUM_ITEMS = tuple(
    (texture_id, texture["label"], texture["base_color"])
    for texture_id, texture in PAVEMENT_TEXTURE_ASSETS.items()
)


# dA_5_add
CITY_3D_ASSETS = {
    "wooden_picnic_table": {
        "label": "野餐椅",
        "description": "适合沿街边人行道摆放的公共休憩资产。",
        "blend_path": "assets_add/3D_assets/wooden_picnic_table_1k.blend/wooden_picnic_table_1k.blend",
        "object_names": ("wooden_picnic_table",),
        "collection_name": "CG_Added3D_Wooden_Picnic_Table_Source",
        "default_count": 6,
        "default_spacing": 12.0,
        "default_scale": 0.72,
        "street_band": (0.88, 1.02),
        "sidewalk_band": (0.52, 0.82),
        "road_distance": (3.3, 8.0),
        "street_inset": 3.0,
        "sidewalk_position": 0.62,
        "avoid_radius": 1.35,
        "z_lift": 0.05,
    },
    "small_lpg_tank": {
        "label": "小消防罐",
        "description": "适合靠近建筑一侧摆放的小型设施资产。",
        "blend_path": "assets_add/3D_assets/small_lpg_tank_1k.blend/small_lpg_tank_1k.blend",
        "object_names": ("small_lpg_tank",),
        "collection_name": "CG_Added3D_Small_LPG_Tank_Source",
        "default_count": 5,
        "default_spacing": 14.0,
        "default_scale": 1.0,
        "street_band": (0.88, 1.02),
        "sidewalk_band": (0.55, 0.86),
        "road_distance": (2.2, 5.5),
        "street_inset": 2.2,
        "sidewalk_position": 0.42,
        "avoid_radius": 0.75,
        "z_lift": 0.12,
    },
    "rubber_duck_toy": {
        "label": "小黄鸭",
        "description": "用于演示新增 3D 资产功能的醒目彩蛋资产。",
        "blend_path": "assets_add/3D_assets/rubber_duck_toy_1k.blend/rubber_duck_toy_1k.blend",
        "object_names": ("rubber_duck_toy",),
        "collection_name": "CG_Added3D_Rubber_Duck_Source",
        "default_count": 4,
        "default_spacing": 16.0,
        "default_scale": 3.0,
        "street_band": (0.88, 1.02),
        "sidewalk_band": (0.48, 0.85),
        "road_distance": (2.2, 9.0),
        "street_inset": 2.4,
        "sidewalk_position": 0.55,
        "avoid_radius": 1.1,
        "z_lift": 0.08,
    },
}

# dA_5_add
CITY_3D_ASSET_ENUM_ITEMS = tuple(
    (asset_id, asset["label"], asset["description"])
    for asset_id, asset in CITY_3D_ASSETS.items()
)

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
