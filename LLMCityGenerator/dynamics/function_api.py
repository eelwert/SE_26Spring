"""LLM-callable function API for member D (Tasks 8+10).

Hybrid architecture
-------------------
* **Cars**       → Geo Nodes native simulation (Socket_89–109) — zero Python bugs
* **Pedestrians** → our timer-driven PedestrianManager
* **Traffic lights** → our TrafficLightManager driving emission-material cycles
* **Road layout** → our PointSolver / SketchProcessor

All functions return ``{"success": bool, "data": ..., "message": str}``.
"""

import bpy
from .simulation_manager import SimulationManager
from ..constants import (
    DEFAULT_CAR_DENSITY,
    DEFAULT_CAR_SPEED_MIN,
    DEFAULT_CAR_SPEED_MAX,
    DEFAULT_PEDESTRIAN_DENSITY,
    DEFAULT_PEDESTRIAN_SPEED,
    DEFAULT_TRAFFIC_LIGHT_GREEN,
    DEFAULT_TRAFFIC_LIGHT_YELLOW,
    DEFAULT_TRAFFIC_LIGHT_RED,
)

# Re-export for layout integration
from ..layout.layout_api import (
    LAYOUT_REGISTRY,
    solve_point_layout,
    extract_sketch_topology,
    clear_road_layout,
)

_LAYOUT_HANDLERS = {
    "solve_point_layout": solve_point_layout,
    "extract_sketch_topology": extract_sketch_topology,
    "clear_road_layout": clear_road_layout,
}


# ---------------------------------------------------------------------------
# Geo Nodes helpers
# ---------------------------------------------------------------------------

def _get_city_modifier(mesh_obj=None):
    """Return the City_Generator_2.0 modifier on *mesh_obj*, or None."""
    if mesh_obj is None:
        mesh_obj = bpy.context.object
    if mesh_obj is None:
        return None
    return mesh_obj.modifiers.get("City_Generator_2.0")


def _set_socket(mod, socket_id, value):
    """Safely set a Geo Nodes modifier socket."""
    if socket_id in mod:
        mod[socket_id] = value


def _configure_geo_traffic(params, mesh_obj=None):
    """Apply traffic-related parameter overrides to the Geo Nodes modifier."""
    mod = _get_city_modifier(mesh_obj)
    if mod is None:
        return None

    scene = bpy.context.scene
    fps = max(scene.render.fps, 1)

    socket_map = {
        "car_density":      ("Socket_90", int),
        "speed_min":        ("Socket_98", float),
        "speed_max":        ("Socket_99", float),
        "car_distance_min": ("Socket_94", float),
        "delete_prob":      ("Socket_96", float),
    }
    for param_key, (socket_id, cast) in socket_map.items():
        if param_key in params:
            val = cast(params[param_key])
            if socket_id in ("Socket_98", "Socket_99"):
                val = val / fps  # m/s → m/frame for sim nodes
            _set_socket(mod, socket_id, val)

    # Enable traffic
    _set_socket(mod, "Socket_144", True)
    return mod


def _bake_simulation(mod):
    """Delete old cache then recalculate — mirrors Traffic Simulation panel workflow."""
    try:
        obj = mod.id_data
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        # 1. Delete old cache so new socket values take effect
        bpy.ops.object.simulation_nodes_cache_delete(selected=True)
        # 2. Recalculate to current frame
        obj.update_tag()
        bpy.context.view_layer.update()
        bpy.ops.object.simulation_nodes_cache_calculate_to_frame(selected=True)
        return True
    except Exception as e:
        print(f"[CityGen] Bake failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def _resolve_car_collections():
    """Return (body, front_wheels, back_wheels, car_lights) from the blend file."""
    body = None
    front = None
    back = None
    lights = None

    for name in ("car model", "Car Assets", "car light"):
        body = bpy.data.collections.get(name)
        if body:
            break
    if body is None:
        body = _import_collection("car model")

    for name in ("front wheels", "front wheel"):
        front = bpy.data.collections.get(name)
        if front:
            break
    if front is None:
        front = _import_collection("front wheels")

    for name in ("back wheels", "back wheel"):
        back = bpy.data.collections.get(name)
        if back:
            break
    if back is None:
        back = _import_collection("back wheels")

    for name in ("car light", "car lights", "Car Lights"):
        lights = bpy.data.collections.get(name)
        if lights:
            break

    return body, front, back, lights


def _resolve_pedestrian_collection():
    """Load pedestrian models from assets/pedestrians.blend (Procedural Crowds format).

    The file contains two collections: ``people`` (mesh objects) and ``armatures``
    (armature objects).  Each mesh in *people* has an Armature modifier pointing
    to the matching armature in *armatures*.

    Returns the ``people`` collection, or None.
    """
    # Already loaded?
    for test_name in ("people", "People"):
        coll = bpy.data.collections.get(test_name)
        if coll and len(coll.objects) > 0:
            mesh_count = sum(1 for o in coll.all_objects if o.type == "MESH")
            print(f"[CityGen] Using cached '{coll.name}' ({mesh_count} meshes)")
            return coll

    import os
    from ..constants import ADDON_DIR

    blend_path = None
    for dirname in ("assets", "asserts"):
        candidate = os.path.join(ADDON_DIR, dirname, "pedestrians.blend")
        if os.path.exists(candidate):
            blend_path = candidate
            break

    if blend_path is None:
        print(f"[CityGen] pedestrians.blend not found")
        return None

    print(f"[CityGen] Loading pedestrians from {blend_path} ...")

    # Discover available collections
    try:
        with bpy.data.libraries.load(str(blend_path), link=False) as (df, _dt):
            all_colls = list(df.collections or [])
            print(f"[CityGen] Collections in file: {all_colls}")
    except Exception as e:
        print(f"[CityGen] Failed to inspect pedestrians.blend: {e}")
        return None

    # Load people + armatures (case-insensitive match)
    load_list = []
    for c in all_colls:
        name = str(c)
        if name.lower() in ("people", "armatures", "assets"):
            load_list.append(name)

    if not load_list:
        print(f"[CityGen] No 'people'/'armatures'/'assets' collections found")
        return None

    print(f"[CityGen] Loading: {load_list}")
    try:
        with bpy.data.libraries.load(str(blend_path), link=False) as (_df, dt):
            setattr(dt, "collections", load_list)
    except Exception as e:
        print(f"[CityGen] Failed to load collections: {e}")
        return None

    # Find the people collection — it may be a top-level collection named
    # "People" (Procedural Crowds format) or a child of "ASSETS".
    people_coll = None
    armatures_coll = None
    for candidate_name in ("People", "people"):
        people_coll = bpy.data.collections.get(candidate_name)
        if people_coll is not None:
            break
    # Not found at top-level — try as child of ASSETS
    if people_coll is None:
        assets = bpy.data.collections.get("ASSETS") or bpy.data.collections.get("Assets")
        if assets:
            for child in assets.children_recursive:
                if child.name.lower() == "people":
                    people_coll = child
                    break
    # Still nothing — search all loaded collections for mesh objects
    if people_coll is None:
        for coll_name in load_list:
            c = bpy.data.collections.get(str(coll_name))
            if c and any(o.type == "MESH" for o in c.all_objects):
                people_coll = c
                break

    # Find armatures similarly
    for candidate_name in ("Armatures", "armatures"):
        armatures_coll = bpy.data.collections.get(candidate_name)
        if armatures_coll is not None:
            break
    if armatures_coll is None:
        assets = bpy.data.collections.get("ASSETS") or bpy.data.collections.get("Assets")
        if assets:
            for child in assets.children_recursive:
                if child.name.lower() == "armatures":
                    armatures_coll = child
                    break

    if people_coll is None:
        print("[CityGen] 'people' collection not found after loading")
        return None

    mesh_count = sum(1 for o in people_coll.all_objects if o.type == "MESH")
    print(f"[CityGen] Loaded 'people' ({mesh_count} meshes, {len(people_coll.objects)} top-level objects)")

    if armatures_coll:
        print(f"[CityGen] Loaded 'armatures' ({len(armatures_coll.objects)} armatures)")

    # Hide source collections
    people_coll.hide_viewport = True
    people_coll.hide_render = True
    if armatures_coll:
        armatures_coll.hide_viewport = True
        armatures_coll.hide_render = True

    if mesh_count == 0:
        print("[CityGen] No mesh objects in 'people' collection")
        return None

    return people_coll


def _import_collection(name):
    """Import a collection from the bundled blend file."""
    import os
    from ..constants import ADDON_DIR, BLEND_FILE

    blend_path = os.path.join(ADDON_DIR, BLEND_FILE)
    try:
        with bpy.data.libraries.load(str(blend_path), link=False) as (_df, dt):
            setattr(dt, "collections", [name])
    except Exception:
        return None

    coll = bpy.data.collections.get(name)
    if coll and coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    return coll


# ---------------------------------------------------------------------------
# LLM-callable functions
# ---------------------------------------------------------------------------

def run_traffic_simulation(mesh_obj=None, params=None):
    """Start vehicle traffic via the built-in Geo Nodes simulation.

    Requires a City_Generator_2.0 modifier on the active mesh.
    """
    params = params or {}
    mesh_obj = _resolve_mesh(mesh_obj)
    if mesh_obj is None:
        return {"success": False, "message": "No mesh object selected"}

    mod = _configure_geo_traffic(params, mesh_obj=mesh_obj)
    if mod is None:
        return {"success": False, "message": "City_Generator_2.0 modifier not found — run Import City Generator and Apply Node Group first"}

    # Load and assign car asset collections (mirrors Traffic Simulation panel)
    body, front_w, back_w, lights = _resolve_car_collections()
    if body:
        mod["Socket_102"] = body
    if front_w:
        mod["Socket_103"] = front_w
    if back_w:
        mod["Socket_104"] = back_w
    if lights:
        mod["Socket_105"] = lights

    baked = _bake_simulation(mod)

    return {
        "success": True,
        "data": {"car_model": body.name if body else "default", "baked": baked},
        "message": f"Geo Nodes traffic configured (bake: {'OK' if baked else 'manual bake needed'})",
    }


def run_crowd_simulation(mesh_obj=None, params=None):
    """Start pedestrian simulation (Python-driven)."""
    params = params or {}
    mesh_obj = _resolve_mesh(mesh_obj)
    if mesh_obj is None:
        return {"success": False, "message": "No mesh object selected"}

    scene = bpy.context.scene
    if "pedestrian_density" in params:
        scene.cg_pedestrian_density = int(params["pedestrian_density"])
    if "walking_speed" in params:
        scene.cg_pedestrian_speed = float(params["walking_speed"])

    ped_coll = _resolve_pedestrian_collection()

    sim = SimulationManager.get_instance()
    if sim.active:
        return {"success": False, "message": "Simulation already active — call stop_simulation() first"}

    sim.setup(mesh_obj, scene=scene,
              enable_pedestrians=True,
              enable_traffic_lights=params.get("traffic_lights", True),
              pedestrian_collection=ped_coll)

    return {
        "success": True,
        "data": {"pedestrian_count": len(sim.pedestrian_manager.pedestrians)},
        "message": f"{len(sim.pedestrian_manager.pedestrians)} pedestrians spawned",
    }


def run_full_simulation(mesh_obj=None, params=None):
    """Start Geo Nodes car traffic + Python pedestrians + traffic lights."""
    params = params or {}
    mesh_obj = _resolve_mesh(mesh_obj)
    if mesh_obj is None:
        return {"success": False, "message": "No mesh object selected"}

    scene = bpy.context.scene

    # ---- scene property overrides ----
    overrides = {
        "pedestrian_density": ("cg_pedestrian_density", int),
        "walking_speed":      ("cg_pedestrian_speed", float),
        "green_duration":     ("cg_traffic_light_green", int),
        "yellow_duration":    ("cg_traffic_light_yellow", int),
        "red_duration":       ("cg_traffic_light_red", int),
    }
    for key, (attr, cast) in overrides.items():
        if key in params:
            setattr(scene, attr, cast(params[key]))

    # ---- cars via Geo Nodes ----
    mod = _configure_geo_traffic(params, mesh_obj=mesh_obj)
    if mod is None:
        return {"success": False, "message": "City_Generator_2.0 modifier not found — run Import City Generator and Apply Node Group first"}

    body, front_w, back_w, lights = _resolve_car_collections()
    if body:
        mod["Socket_102"] = body
    if front_w:
        mod["Socket_103"] = front_w
    if back_w:
        mod["Socket_104"] = back_w
    if lights:
        mod["Socket_105"] = lights
    baked = _bake_simulation(mod)

    # ---- pedestrians + traffic lights via Python ----
    ped_coll = _resolve_pedestrian_collection()

    sim = SimulationManager.get_instance()
    if sim.active:
        return {"success": False, "message": "Simulation already active — call stop_simulation() first"}

    sim.setup(mesh_obj, scene=scene,
              enable_pedestrians=True,
              enable_traffic_lights=True,
              pedestrian_collection=ped_coll)

    return {
        "success": True,
        "data": {
            "pedestrian_count": len(sim.pedestrian_manager.pedestrians),
            "traffic_light_count": len(sim.traffic_light_manager.traffic_lights),
            "road_count": len(sim.road_data),
            "car_model": body.name if body else "default",
            "geo_baked": baked,
        },
        "message": (
            f"Geo cars (bake: {'OK' if baked else 'manual'}), "
            f"{len(sim.pedestrian_manager.pedestrians)} pedestrians, "
            f"{len(sim.traffic_light_manager.traffic_lights)} traffic lights"
        ),
    }


def stop_simulation(params=None):
    """Stop dynamic simulation and clean up."""
    sim = SimulationManager.get_instance()
    if not sim.active:
        return {"success": False, "message": "No simulation active"}

    ped_n = len(sim.pedestrian_manager.pedestrians)
    light_n = len(sim.traffic_light_manager.traffic_lights)
    SimulationManager.reset_instance()

    # Also delete Geo Nodes simulation cache
    mod = _get_city_modifier()  # uses bpy.context.object (convenience)
    if mod:
        try:
            obj = mod.id_data
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.simulation_nodes_cache_delete(selected=True)
        except Exception:
            pass

    return {"success": True, "message": f"Stopped — removed {ped_n} pedestrians, {light_n} lights"}


def set_traffic_light_timing(params=None):
    """Adjust traffic-light cycle durations."""
    params = params or {}
    scene = bpy.context.scene
    for key, attr in [("green", "cg_traffic_light_green"),
                       ("yellow", "cg_traffic_light_yellow"),
                       ("red", "cg_traffic_light_red")]:
        if key in params:
            setattr(scene, attr, int(params[key]))
    return {"success": True, "message": "Timing updated (re-apply simulation to take effect)"}


def set_car_model(params=None):
    """Set car model collection for Geo Nodes traffic."""
    if not params or "collection" not in params:
        return {"success": False, "message": "Missing 'collection' parameter"}
    mod = _get_city_modifier()
    if mod is None:
        return {"success": False, "message": "No City_Generator_2.0 modifier found"}
    mod["Socket_102"] = bpy.data.collections.get(params["collection"])
    return {"success": True, "message": f"Car model socket set to '{params['collection']}'"}


def set_pedestrian_model(params=None):
    """Set pedestrian model (stub — no dedicated pedestrian models in blend)."""
    return {"success": True, "message": "No pedestrian models in blend — using procedural"}


def list_available_models(params=None):
    """Return collections in the blend file that can be used as models."""
    import os
    from ..constants import ADDON_DIR, BLEND_FILE

    blend_path = os.path.join(ADDON_DIR, BLEND_FILE)
    all_colls = []
    try:
        with bpy.data.libraries.load(str(blend_path), link=False) as (df, _dt):
            all_colls = sorted(df.collections or [])
    except Exception:
        pass

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
    """Return current state."""
    sim = SimulationManager.get_instance()
    mod = _get_city_modifier()
    return {
        "success": True,
        "data": {
            "active": sim.active,
            "pedestrian_count": len(sim.pedestrian_manager.pedestrians),
            "traffic_light_count": len(sim.traffic_light_manager.traffic_lights),
            "road_count": len(sim.road_data),
            "has_geo_cars": mod is not None,
        },
    }


# ---------------------------------------------------------------------------
# Unified dispatch
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
_HANDLERS.update(_LAYOUT_HANDLERS)


def dispatch_blender_job(function_name, params=None):
    """Unified entry point for LLM-driven Blender job execution."""
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
# Function registry for member B
# ---------------------------------------------------------------------------

FUNCTION_REGISTRY = {
    "run_traffic_simulation": {
        "function": run_traffic_simulation,
        "description": "Geo Nodes 车辆仿真 — 配置 Socket 参数并触发模拟缓存",
        "params": {
            "car_density": {"type": "int", "min": 0, "max": 200, "default": DEFAULT_CAR_DENSITY},
            "speed_min": {"type": "float", "min": 1.0, "max": 50.0, "default": DEFAULT_CAR_SPEED_MIN},
            "speed_max": {"type": "float", "min": 1.0, "max": 50.0, "default": DEFAULT_CAR_SPEED_MAX},
        },
    },
    "run_crowd_simulation": {
        "function": run_crowd_simulation,
        "description": "Python 行人仿真 — 沿人行道生成行走的行人",
        "params": {
            "pedestrian_density": {"type": "int", "min": 0, "max": 200, "default": DEFAULT_PEDESTRIAN_DENSITY},
            "walking_speed": {"type": "float", "min": 0.5, "max": 5.0, "default": DEFAULT_PEDESTRIAN_SPEED},
            "traffic_lights": {"type": "bool", "default": True},
        },
    },
    "run_full_simulation": {
        "function": run_full_simulation,
        "description": "综合仿真 — Geo Nodes 车流 + Python 行人 + 交通灯",
        "params": {
            "car_density": {"type": "int", "min": 0, "max": 200, "default": DEFAULT_CAR_DENSITY},
            "speed_min": {"type": "float", "min": 1.0, "max": 50.0, "default": DEFAULT_CAR_SPEED_MIN},
            "speed_max": {"type": "float", "min": 1.0, "max": 50.0, "default": DEFAULT_CAR_SPEED_MAX},
            "pedestrian_density": {"type": "int", "min": 0, "max": 200, "default": DEFAULT_PEDESTRIAN_DENSITY},
            "walking_speed": {"type": "float", "min": 0.5, "max": 5.0, "default": DEFAULT_PEDESTRIAN_SPEED},
            "green_duration": {"type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_GREEN},
            "yellow_duration": {"type": "int", "min": 10, "max": 120, "default": DEFAULT_TRAFFIC_LIGHT_YELLOW},
            "red_duration": {"type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_RED},
        },
    },
    "stop_simulation": {
        "function": stop_simulation,
        "description": "停止仿真并清理所有动态对象",
        "params": {},
    },
    "set_traffic_light_timing": {
        "function": set_traffic_light_timing,
        "description": "调整交通灯红/黄/绿灯持续帧数",
        "params": {
            "green": {"type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_GREEN},
            "yellow": {"type": "int", "min": 10, "max": 120, "default": DEFAULT_TRAFFIC_LIGHT_YELLOW},
            "red": {"type": "int", "min": 30, "max": 600, "default": DEFAULT_TRAFFIC_LIGHT_RED},
        },
    },
    "set_car_model": {
        "function": set_car_model,
        "description": "设置 Geo Nodes 使用的车辆模型集合",
        "params": {"collection": {"type": "string", "default": ""}},
    },
    "set_pedestrian_model": {
        "function": set_pedestrian_model,
        "description": "设置行人模型集合（当前无专用模型，使用程序化几何体）",
        "params": {},
    },
    "list_available_models": {
        "function": list_available_models,
        "description": "列出 blend 文件中可用的模型集合",
        "params": {},
    },
    "get_simulation_status": {
        "function": get_simulation_status,
        "description": "查询当前仿真状态",
        "params": {},
    },
}
FUNCTION_REGISTRY.update(LAYOUT_REGISTRY)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_mesh(mesh_obj):
    if mesh_obj is not None:
        return mesh_obj
    obj = bpy.context.object
    if obj is not None and obj.type == "MESH":
        return obj
    return None
