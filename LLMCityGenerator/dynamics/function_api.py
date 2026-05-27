"""LLM-callable function API for dynamic simulation (Task 1 / 成员 D).

Architecture
-----------
Model loading lives HERE (not in car_system / pedestrian_system).
Each simulation function first resolves car / pedestrian collections from
the bundled City_Generator2.0.blend, then passes them down to
SimulationManager → CarManager / PedestrianManager.

For 成员 B
---------
Import ``FUNCTION_REGISTRY`` directly::

    from bl_ext.user_default.LLMCityGenerator.dynamics.function_api import (
        FUNCTION_REGISTRY,       # {functionName: {function, description, params}}
        dispatch_blender_job,    # unified entry
    )

Return format (every function)
-------------------------------
{"success": bool, "data": dict | None, "message": str}
"""

import os
import bpy
from .simulation_manager import SimulationManager
from .road_analyzer import RoadAnalyzer
from ..constants import (
    ADDON_DIR,
    BLEND_FILE,
    DEFAULT_CAR_DENSITY,
    DEFAULT_CAR_SPEED_MIN,
    DEFAULT_CAR_SPEED_MAX,
    DEFAULT_PEDESTRIAN_DENSITY,
    DEFAULT_PEDESTRIAN_SPEED,
    DEFAULT_TRAFFIC_LIGHT_GREEN,
    DEFAULT_TRAFFIC_LIGHT_YELLOW,
    DEFAULT_TRAFFIC_LIGHT_RED,
)


# ---------------------------------------------------------------------------
# Model-resolution helpers (operate at the blend-file / bpy.data level)
# ---------------------------------------------------------------------------

# Cached after first scan so we don't re-read the blend file every call
_BLEND_COLLECTIONS = None
_CAR_COLLECTION_NAME = None
_PED_COLLECTION_NAME = None


def _scan_blend_collections():
    """Return a set of collection names available in City_Generator2.0.blend."""
    global _BLEND_COLLECTIONS
    if _BLEND_COLLECTIONS is not None:
        return _BLEND_COLLECTIONS

    blend_path = os.path.join(ADDON_DIR, BLEND_FILE)
    try:
        with bpy.data.libraries.load(str(blend_path), link=False) as (df, _dt):
            _BLEND_COLLECTIONS = set(df.collections or [])
    except Exception:
        _BLEND_COLLECTIONS = set()
    return _BLEND_COLLECTIONS


def _resolve_car_collection():
    """Return a car-model collection, importing from .blend if necessary.

    Priority order:
    1. Previously cached successful name
    2. Geo Nodes modifier Socket_102
    3. Known exact names from City_Generator2.0.blend: 'car model', 'Car Assets'
    4. Any collection in bpy.data whose name suggests cars
    5. Import from blend file
    6. Return None → fall back to procedural boxes
    """
    global _CAR_COLLECTION_NAME

    # 1. Cached
    if _CAR_COLLECTION_NAME:
        coll = bpy.data.collections.get(_CAR_COLLECTION_NAME)
        if coll is not None:
            return coll

    # 2. Geo Nodes modifier Socket_102
    obj = bpy.context.object
    if obj and obj.modifiers:
        mod = obj.modifiers.get("City_Generator_2.0")
        if mod and '["Socket_102"]' in mod:
            name = str(mod['["Socket_102"]'])
            coll = bpy.data.collections.get(name)
            if coll is not None:
                _CAR_COLLECTION_NAME = name
                return coll

    # 3. Known exact names (confirmed in City_Generator2.0.blend)
    for known in ("car model", "Car Assets", "car light", "traffic lights"):
        coll = bpy.data.collections.get(known)
        if coll is not None:
            _CAR_COLLECTION_NAME = known
            return coll
        # Try to import from blend
        coll = _import_collection(known)
        if coll is not None:
            _CAR_COLLECTION_NAME = known
            return coll

    # 4. Broad search by keyword in bpy.data
    car_kw = ("car", "vehicle", "auto")
    for coll in bpy.data.collections:
        low = coll.name.lower()
        if any(kw in low for kw in car_kw) and "car" not in low:
            _CAR_COLLECTION_NAME = coll.name
            return coll

    # 5. Broad import from blend file
    available = _scan_blend_collections()
    for cname in sorted(available):
        low = cname.lower()
        if any(kw in low for kw in car_kw):
            coll = _import_collection(cname)
            if coll is not None:
                _CAR_COLLECTION_NAME = cname
                return coll

    return None


def _resolve_pedestrian_collection():
    """Like _resolve_car_collection, but for pedestrian / crowd models."""
    global _PED_COLLECTION_NAME

    if _PED_COLLECTION_NAME:
        coll = bpy.data.collections.get(_PED_COLLECTION_NAME)
        if coll is not None:
            return coll

    ped_kw = ("pedestrian", "crowd", "people", "person", "human", "walk")
    for coll in bpy.data.collections:
        low = coll.name.lower()
        if any(kw in low for kw in ped_kw):
            _PED_COLLECTION_NAME = coll.name
            return coll

    available = _scan_blend_collections()
    for cname in sorted(available):
        low = cname.lower()
        if any(kw in low for kw in ped_kw):
            coll = _import_collection(cname)
            if coll is not None:
                _PED_COLLECTION_NAME = cname
                return coll

    return None


def _import_collection(name):
    """Import a single collection from the bundled blend file."""
    blend_path = os.path.join(ADDON_DIR, BLEND_FILE)
    try:
        with bpy.data.libraries.load(str(blend_path), link=False) as (_df, dt):
            setattr(dt, "collections", [name])
    except Exception:
        return None

    coll = bpy.data.collections.get(name)
    if coll is None:
        return None
    # Link to scene so it's available
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    # Hide from viewport (don't clutter the outliner)
    coll.hide_viewport = True
    return coll


# ---------------------------------------------------------------------------
# Individual LLM-callable functions
# ---------------------------------------------------------------------------

def run_traffic_simulation(mesh_obj=None, params=None):
    """Start vehicle traffic simulation.

    Args:
        mesh_obj: optional mesh whose edges define roads.
        params (dict):
            car_density      int   0-200  (default 10)
            speed_min        float 1-50   (default 5.0 m/s)
            speed_max        float 1-50   (default 15.0 m/s)
            traffic_lights   bool         (default True)
            car_collection   str          explicit collection name override

    Returns:
        {"success": True, "data": {"car_count": N, "road_count": M}, "message": "..."}
    """
    if params is None:
        params = {}

    mesh_obj = _resolve_mesh(mesh_obj)
    if mesh_obj is None:
        return {"success": False, "message": "No mesh object selected or provided"}

    scene = bpy.context.scene

    # ---- parameter overrides ----
    if "car_density" in params:
        scene.cg_car_density = int(params["car_density"])
    if "speed_min" in params:
        scene.cg_car_speed_min = float(params["speed_min"])
    if "speed_max" in params:
        scene.cg_car_speed_max = float(params["speed_max"])

    # ---- resolve car model ----
    car_coll = None
    if "car_collection" in params:
        car_coll = bpy.data.collections.get(params["car_collection"])
    if car_coll is None:
        car_coll = _resolve_car_collection()

    enable_lights = params.get("traffic_lights", True)

    sim = SimulationManager.get_instance()
    if sim.active:
        return {"success": False, "message": "Simulation already active. Call stop_simulation() first."}

    sim.setup(mesh_obj, scene=scene,
              enable_cars=True,
              enable_pedestrians=False,
              enable_traffic_lights=enable_lights,
              car_collection=car_coll,
              front_wheels_coll=_import_collection("front wheels"),
              back_wheels_coll=_import_collection("back wheels"))

    return {
        "success": True,
        "data": {
            "car_count": len(sim.car_manager.cars),
            "road_count": len(sim.road_data),
            "car_model": car_coll.name if car_coll else "fallback",
        },
        "message": f"{len(sim.car_manager.cars)} cars on {len(sim.road_data)} roads "
                   f"(model: {car_coll.name if car_coll else 'procedural'})",
    }


def run_crowd_simulation(mesh_obj=None, params=None):
    """Start pedestrian / crowd simulation.

    Args:
        mesh_obj: optional mesh.
        params (dict):
            pedestrian_density  int   0-200  (default 10)
            walking_speed       float 0.5-5  (default 1.5 m/s)
            traffic_lights      bool         (default True)
            pedestrian_collection str        explicit collection name override

    Returns:
        {"success": True, "data": {"pedestrian_count": N}, "message": "..."}
    """
    if params is None:
        params = {}

    mesh_obj = _resolve_mesh(mesh_obj)
    if mesh_obj is None:
        return {"success": False, "message": "No mesh object selected or provided"}

    scene = bpy.context.scene

    if "pedestrian_density" in params:
        scene.cg_pedestrian_density = int(params["pedestrian_density"])
    if "walking_speed" in params:
        scene.cg_pedestrian_speed = float(params["walking_speed"])

    ped_coll = None
    if "pedestrian_collection" in params:
        ped_coll = bpy.data.collections.get(params["pedestrian_collection"])
    if ped_coll is None:
        ped_coll = _resolve_pedestrian_collection()

    enable_lights = params.get("traffic_lights", True)

    sim = SimulationManager.get_instance()
    if sim.active:
        return {"success": False, "message": "Simulation already active. Call stop_simulation() first."}

    sim.setup(mesh_obj, scene=scene,
              enable_cars=False,
              enable_pedestrians=True,
              enable_traffic_lights=enable_lights,
              pedestrian_collection=ped_coll)

    return {
        "success": True,
        "data": {
            "pedestrian_count": len(sim.pedestrian_manager.pedestrians),
            "pedestrian_model": ped_coll.name if ped_coll else "fallback",
        },
        "message": f"{len(sim.pedestrian_manager.pedestrians)} pedestrians "
                   f"(model: {ped_coll.name if ped_coll else 'procedural'})",
    }


def run_full_simulation(mesh_obj=None, params=None):
    """Start both car AND pedestrian simulation.

    Args:
        mesh_obj: optional mesh.
        params (dict): all traffic + crowd parameters, plus:
            car_collection         str  explicit car collection name
            pedestrian_collection  str  explicit pedestrian collection name
            green_duration         int  30-600  green light frames
            yellow_duration        int  10-120  yellow light frames
            red_duration           int  30-600  red light frames
    """
    if params is None:
        params = {}

    mesh_obj = _resolve_mesh(mesh_obj)
    if mesh_obj is None:
        return {"success": False, "message": "No mesh object selected or provided"}

    scene = bpy.context.scene

    # ---- scene property overrides ----
    for key, attr in [
        ("car_density", "cg_car_density"),
        ("speed_min", "cg_car_speed_min"),
        ("speed_max", "cg_car_speed_max"),
        ("pedestrian_density", "cg_pedestrian_density"),
        ("walking_speed", "cg_pedestrian_speed"),
        ("green_duration", "cg_traffic_light_green"),
        ("yellow_duration", "cg_traffic_light_yellow"),
        ("red_duration", "cg_traffic_light_red"),
    ]:
        if key in params:
            setattr(scene, attr, _coerce(params[key], getattr(scene, attr)))

    # ---- resolve models ----
    car_coll = None
    if "car_collection" in params:
        car_coll = bpy.data.collections.get(params["car_collection"])
    if car_coll is None:
        car_coll = _resolve_car_collection()

    ped_coll = None
    if "pedestrian_collection" in params:
        ped_coll = bpy.data.collections.get(params["pedestrian_collection"])
    if ped_coll is None:
        ped_coll = _resolve_pedestrian_collection()

    sim = SimulationManager.get_instance()
    if sim.active:
        return {"success": False, "message": "Simulation already active. Call stop_simulation() first."}

    sim.setup(mesh_obj, scene=scene,
              enable_cars=True,
              enable_pedestrians=True,
              enable_traffic_lights=True,
              car_collection=car_coll,
              front_wheels_coll=_import_collection("front wheels"),
              back_wheels_coll=_import_collection("back wheels"),
              pedestrian_collection=ped_coll)

    return {
        "success": True,
        "data": {
            "car_count": len(sim.car_manager.cars),
            "pedestrian_count": len(sim.pedestrian_manager.pedestrians),
            "traffic_light_count": len(sim.traffic_light_manager.traffic_lights),
            "road_count": len(sim.road_data),
            "car_model": car_coll.name if car_coll else "procedural",
            "pedestrian_model": ped_coll.name if ped_coll else "procedural",
        },
        "message": (
            f"{len(sim.car_manager.cars)} cars, "
            f"{len(sim.pedestrian_manager.pedestrians)} pedestrians, "
            f"{len(sim.traffic_light_manager.traffic_lights)} traffic lights"
        ),
    }


def stop_simulation(params=None):
    """Stop the running simulation and remove all dynamic objects."""
    sim = SimulationManager.get_instance()
    if not sim.active:
        return {"success": False, "message": "No simulation is currently active"}

    car_n = len(sim.car_manager.cars)
    ped_n = len(sim.pedestrian_manager.pedestrians)
    SimulationManager.reset_instance()

    return {
        "success": True,
        "message": f"Stopped — removed {car_n} cars, {ped_n} pedestrians",
    }


def set_traffic_light_timing(params=None):
    """Adjust traffic-light cycle durations.

    Args:
        params (dict): green, yellow, red (int, frames)
    """
    if params is None:
        params = {}
    scene = bpy.context.scene
    for key, attr in [
        ("green", "cg_traffic_light_green"),
        ("yellow", "cg_traffic_light_yellow"),
        ("red", "cg_traffic_light_red"),
    ]:
        if key in params:
            setattr(scene, attr, int(params[key]))

    return {
        "success": True,
        "data": {
            "green": scene.cg_traffic_light_green,
            "yellow": scene.cg_traffic_light_yellow,
            "red": scene.cg_traffic_light_red,
        },
        "message": "Timing updated (re-apply simulation to take effect)",
    }


def set_car_model(params=None):
    """Set the car model collection to use.

    Args:
        params (dict):
            collection  str  collection name (must exist in bpy.data or blend file)

    If *collection* is not found in bpy.data, attempts to import it from
    City_Generator2.0.blend.
    """
    if params is None or "collection" not in params:
        return {"success": False, "message": "Missing 'collection' parameter"}

    name = params["collection"]
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = _import_collection(name)
    if coll is None:
        available = sorted(_scan_blend_collections())
        return {
            "success": False,
            "message": f"Collection '{name}' not found. Available in blend: {available}",
        }

    global _CAR_COLLECTION_NAME
    _CAR_COLLECTION_NAME = name
    return {"success": True, "message": f"Car model set to '{name}'"}


def set_pedestrian_model(params=None):
    """Set the pedestrian model collection to use.

    Args:
        params (dict):
            collection  str  collection name
    """
    if params is None or "collection" not in params:
        return {"success": False, "message": "Missing 'collection' parameter"}

    name = params["collection"]
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = _import_collection(name)
    if coll is None:
        available = sorted(_scan_blend_collections())
        return {
            "success": False,
            "message": f"Collection '{name}' not found. Available in blend: {available}",
        }

    global _PED_COLLECTION_NAME
    _PED_COLLECTION_NAME = name
    return {"success": True, "message": f"Pedestrian model set to '{name}'"}


def list_available_models(params=None):
    """Return collections in the bundled blend file that could be used as models.

    Returns:
        {"success": True, "data": {"all": [...], "car_candidates": [...], "ped_candidates": [...]}}
    """
    all_colls = sorted(_scan_blend_collections())
    car_kw = ("car", "vehicle", "traffic", "auto")
    ped_kw = ("pedestrian", "crowd", "people", "person", "human", "walk")

    return {
        "success": True,
        "data": {
            "all": all_colls,
            "car_candidates": [c for c in all_colls if any(k in c.lower() for k in car_kw)],
            "ped_candidates": [c for c in all_colls if any(k in c.lower() for k in ped_kw)],
        },
    }


def get_simulation_status(params=None):
    """Return current simulation state."""
    sim = SimulationManager.get_instance()
    return {
        "success": True,
        "data": {
            "active": sim.active,
            "car_count": len(sim.car_manager.cars),
            "pedestrian_count": len(sim.pedestrian_manager.pedestrians),
            "traffic_light_count": len(sim.traffic_light_manager.traffic_lights),
            "road_count": len(sim.road_data),
        },
    }


# ---------------------------------------------------------------------------
# Unified dispatch — entry point for backend / LLM orchestrator
# ---------------------------------------------------------------------------

_HANDLERS = {
    "run_traffic_simulation": run_traffic_simulation,
    "run_crowd_simulation": run_crowd_simulation,
    "run_full_simulation": run_full_simulation,
    "stop_simulation": stop_simulation,
    "set_traffic_light_timing": set_traffic_light_timing,
    "set_car_model": set_car_model,
    "set_pedestrian_model": set_pedestrian_model,
    "list_available_models": list_available_models,
    "get_simulation_status": get_simulation_status,
}


def dispatch_blender_job(function_name, params=None):
    """Unified entry point for LLM-driven Blender job execution.

    Args:
        function_name (str): key from FUNCTION_REGISTRY.
        params (dict): keyword arguments for the function.

    Returns:
        {"success": bool, "data": ..., "message": str}
    """
    handler = _HANDLERS.get(function_name)
    if handler is None:
        return {
            "success": False,
            "message": f"Unknown function '{function_name}'. "
                       f"Available: {', '.join(sorted(_HANDLERS))}",
        }
    try:
        return handler(params=params)
    except Exception as exc:
        return {"success": False, "message": str(exc)}


# ---------------------------------------------------------------------------
# Function registry — 成员 B 直接导入此 dict
# ---------------------------------------------------------------------------

FUNCTION_REGISTRY = {
    "run_traffic_simulation": {
        "function": run_traffic_simulation,
        "description": "城市道路车辆交通仿真 — 在路网上生成行驶的汽车",
        "params": {
            "car_density": {
                "type": "int", "min": 0, "max": 200,
                "default": DEFAULT_CAR_DENSITY,
                "description": "每条道路的汽车数量上限",
            },
            "speed_min": {
                "type": "float", "min": 1.0, "max": 50.0,
                "default": DEFAULT_CAR_SPEED_MIN,
                "description": "最低车速 (m/s)",
            },
            "speed_max": {
                "type": "float", "min": 1.0, "max": 50.0,
                "default": DEFAULT_CAR_SPEED_MAX,
                "description": "最高车速 (m/s)",
            },
            "car_collection": {
                "type": "string", "default": "",
                "description": "车辆模型集合名称（留空则自动搜索 blend 文件）",
            },
            "traffic_lights": {
                "type": "bool", "default": True,
                "description": "是否启用路口交通灯",
            },
        },
    },
    "run_crowd_simulation": {
        "function": run_crowd_simulation,
        "description": "城市行人与人群仿真 — 沿人行道生成行走的行人",
        "params": {
            "pedestrian_density": {
                "type": "int", "min": 0, "max": 200,
                "default": DEFAULT_PEDESTRIAN_DENSITY,
                "description": "每条人行道的行人数量上限",
            },
            "walking_speed": {
                "type": "float", "min": 0.5, "max": 5.0,
                "default": DEFAULT_PEDESTRIAN_SPEED,
                "description": "步行速度 (m/s)",
            },
            "pedestrian_collection": {
                "type": "string", "default": "",
                "description": "行人模型集合名称（留空则自动搜索）",
            },
            "traffic_lights": {
                "type": "bool", "default": True,
                "description": "是否启用路口交通灯",
            },
        },
    },
    "run_full_simulation": {
        "function": run_full_simulation,
        "description": "综合交通仿真 — 同时生成车辆、行人与交通灯",
        "params": {
            "car_density": {
                "type": "int", "min": 0, "max": 200, "default": DEFAULT_CAR_DENSITY,
                "description": "每条道路的汽车数量上限",
            },
            "speed_min": {
                "type": "float", "min": 1.0, "max": 50.0, "default": DEFAULT_CAR_SPEED_MIN,
                "description": "最低车速 (m/s)",
            },
            "speed_max": {
                "type": "float", "min": 1.0, "max": 50.0, "default": DEFAULT_CAR_SPEED_MAX,
                "description": "最高车速 (m/s)",
            },
            "car_collection": {
                "type": "string", "default": "",
                "description": "车辆模型集合名称（留空则自动搜索 blend 文件）",
            },
            "pedestrian_density": {
                "type": "int", "min": 0, "max": 200, "default": DEFAULT_PEDESTRIAN_DENSITY,
                "description": "每条人行道的行人数量上限",
            },
            "walking_speed": {
                "type": "float", "min": 0.5, "max": 5.0, "default": DEFAULT_PEDESTRIAN_SPEED,
                "description": "步行速度 (m/s)",
            },
            "pedestrian_collection": {
                "type": "string", "default": "",
                "description": "行人模型集合名称（留空则自动搜索）",
            },
            "green_duration": {
                "type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_GREEN,
                "description": "绿灯持续帧数",
            },
            "yellow_duration": {
                "type": "int", "min": 10, "max": 120, "default": DEFAULT_TRAFFIC_LIGHT_YELLOW,
                "description": "黄灯持续帧数",
            },
            "red_duration": {
                "type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_RED,
                "description": "红灯持续帧数",
            },
        },
    },
    "stop_simulation": {
        "function": stop_simulation,
        "description": "停止并清除运行中的动态仿真",
        "params": {},
    },
    "set_traffic_light_timing": {
        "function": set_traffic_light_timing,
        "description": "调整交通灯红/黄/绿灯持续时长",
        "params": {
            "green":  {"type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_GREEN},
            "yellow": {"type": "int", "min": 10, "max": 120, "default": DEFAULT_TRAFFIC_LIGHT_YELLOW},
            "red":    {"type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_RED},
        },
    },
    "set_car_model": {
        "function": set_car_model,
        "description": "设置车辆使用的模型集合（按名称从 blend 文件加载）",
        "params": {
            "collection": {
                "type": "string", "default": "",
                "description": "模型集合名称（如 'City_Gen_2.0_Assets'）",
            },
        },
    },
    "set_pedestrian_model": {
        "function": set_pedestrian_model,
        "description": "设置行人使用的模型集合",
        "params": {
            "collection": {"type": "string", "default": ""},
        },
    },
    "list_available_models": {
        "function": list_available_models,
        "description": "列出 blend 文件中可用的模型集合名称",
        "params": {},
    },
    "get_simulation_status": {
        "function": get_simulation_status,
        "description": "查询当前仿真状态",
        "params": {},
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_mesh(mesh_obj):
    if mesh_obj is not None:
        return mesh_obj
    obj = bpy.context.object
    if obj is not None and obj.type == "MESH":
        return obj
    return None


def _coerce(value, example):
    if isinstance(example, int):
        return int(value)
    if isinstance(example, float):
        return float(value)
    return value
