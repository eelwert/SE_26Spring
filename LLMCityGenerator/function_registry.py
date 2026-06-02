"""Function registry for LLM-callable Blender operations.

Each entry maps a function name (matching the frontend PluginFunction.name)
to metadata and a handler that executes the operation in Blender.
"""

import bpy

MODIFIER_NAME = "City_Generator_2.0"


def _get_modifier(obj):
    """Return the City_Generator_2.0 GN modifier from obj, or None."""
    if obj and obj.modifiers:
        return obj.modifiers.get(MODIFIER_NAME)
    return None


def _set_socket(mod, socket_id, value):
    """Set a GN modifier input socket value through the full RNA path
    and force a dependency graph update to apply the change to geometry.
    Returns (success, error_string).
    """
    mod_name = mod.name
    obj = mod.id_data
    errors = []

    # Path 1: full RNA path through object
    try:
        obj.modifiers[mod_name][socket_id] = value
        _refresh_depsgraph(obj)
        return True, None
    except Exception as e:
        errors.append(str(e))

    # Path 2: direct modifier access
    try:
        mod[socket_id] = value
        _refresh_depsgraph(obj)
        return True, None
    except Exception as e:
        errors.append(str(e))

    return False, f"Socket '{socket_id}' 无法设置 (值={value!r}, 错误: {'; '.join(errors)})"


def _refresh_depsgraph(obj):
    """Try to update the dependency graph and object."""
    try:
        obj.update_tag()
    except Exception:
        pass
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass


def _build_set_code(var_name, key, value):
    """Build a safe exec string for setting a Blender RNA property."""
    if isinstance(value, bool):
        return f"{var_name}['{key}'] = {int(value)}"
    elif isinstance(value, (int, float)):
        return f"{var_name}['{key}'] = {value}"
    elif isinstance(value, str):
        safe = value.replace("'", "\\'")
        return f"{var_name}['{key}'] = '{safe}'"
    else:
        return f"{var_name}['{key}'] = {value!r}"


def _get_active_mod(context):
    """Get the City_Generator_2.0 modifier — searches all objects, not just active."""
    # First try the active object
    obj = context.object if hasattr(context, 'object') else context.view_layer.objects.active
    mod = _get_modifier(obj)
    if mod:
        return mod
    # Search all objects in the scene
    for obj in context.scene.objects if hasattr(context, 'scene') else bpy.data.objects:
        mod = _get_modifier(obj)
        if mod:
            return mod
    return None


# --- Template definitions (0-9) ---

TEMPLATES = {
    0: {"name": "默认", "tree_type": "默认", "road_type": "默认", "seat_type": "默认"},
    1: {"name": "滨水活力街区", "tree_type": "国槐 + 银杏混植", "road_type": "慢行优先断面", "seat_type": "滨水木质长椅"},
    2: {"name": "商业步行街", "tree_type": "法桐阵列", "road_type": "商业步行街断面", "seat_type": "模块化金属座椅"},
    3: {"name": "枢纽换乘片区", "tree_type": "低维护乔木", "road_type": "公交优先断面", "seat_type": "候车廊一体座椅"},
    4: {"name": "校园安全疏散", "tree_type": "白蜡 + 灌木带", "road_type": "校园混行道路", "seat_type": "校园石材座椅"},
    5: {"name": "生态公园", "tree_type": "柳树 + 水生植物", "road_type": "慢行优先断面", "seat_type": "自然石材座椅"},
    6: {"name": "科技园区", "tree_type": "银杏阵列", "road_type": "现代简洁断面", "seat_type": "几何金属座椅"},
    7: {"name": "历史街区", "tree_type": "古槐保留", "road_type": "窄街巷断面", "seat_type": "仿古木质座椅"},
    8: {"name": "住宅社区", "tree_type": "樱花 + 桂花", "road_type": "生活性道路", "seat_type": "庭院式座椅"},
    9: {"name": "工业物流区", "tree_type": "抗污染乔木", "road_type": "宽幅货运道路", "seat_type": "简约混凝土座椅"},
}


# --- Handler functions ---

def _handle_apply_template(params, context):
    """Apply a template by ID to configure trees, road, and seats."""
    template_id = int(params.get("template_id", 0))
    tree_density = int(params.get("tree_density", 60))
    road_width = int(params.get("road_width", 8))

    template = TEMPLATES.get(template_id, TEMPLATES[0])
    mod = _get_active_mod(context)
    results = []

    if mod:
        _set_socket(mod, "Socket_159", tree_density)
        _set_socket(mod, "Socket_9", road_width)
        results.append(f"模板「{template['name']}」已应用")
        results.append(f"树木类型: {template['tree_type']}")
        results.append(f"道路类型: {template['road_type']}")
        results.append(f"座椅类型: {template['seat_type']}")

    context.scene.llm_template_id = template_id
    context.scene.llm_template_name = template["name"]

    if not results:
        results.append("未找到 City_Generator_2.0 修改器，请先点击 Import City Generator 再点击 Apply Node Group。")

    return {"success": bool(mod), "results": results, "applied": {
        "template": template["name"],
        "tree_type": template["tree_type"],
        "road_type": template["road_type"],
        "seat_type": template["seat_type"],
        "tree_density": tree_density,
        "road_width": road_width,
    }}


def _handle_set_weather(params, context):
    weather = params.get("weather", "晴")
    time_of_day = params.get("time_of_day", "12:00")
    context.scene.llm_weather = weather
    context.scene.llm_time_of_day = time_of_day
    results = [f"天气已设置为「{weather}」", f"时间已设置为「{time_of_day}」"]

    if context.scene.world and context.scene.world.node_tree:
        try:
            hour = int(time_of_day.split(":")[0])
            if 6 <= hour < 10:
                color, strength = (1.0, 0.9, 0.7), 0.8
            elif 10 <= hour < 16:
                color, strength = (1.0, 1.0, 0.95), 1.2
            elif 16 <= hour < 19:
                color, strength = (1.0, 0.7, 0.4), 0.7
            else:
                color, strength = (0.3, 0.4, 0.8), 0.3
            for node in context.scene.world.node_tree.nodes:
                if node.type == 'BACKGROUND':
                    node.inputs['Color'].default_value = (*color, 1.0)
                    node.inputs['Strength'].default_value = strength
                    results.append(f"环境光已调整")
                    break
        except Exception:
            pass

    return {"success": True, "results": results, "applied": {"weather": weather, "time_of_day": time_of_day}}


def _handle_set_street_width(params, context):
    width = float(params.get("width", 8))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到 City_Generator_2.0 修改器。请先导入并应用节点组。"]}
    ok, err = _set_socket(mod, "Socket_9", width)
    if ok:
        return {"success": True, "results": [f"道路宽度已设置为 {width}m"]}
    return {"success": False, "results": [f"设置道路宽度失败: {err}"]}


def _handle_set_lane_amount(params, context):
    lanes = int(params.get("lanes", 4))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到 City_Generator_2.0 修改器。"]}
    ok, err = _set_socket(mod, "Socket_12", lanes)
    if ok:
        return {"success": True, "results": [f"车道数量已设置为 {lanes}"]}
    return {"success": False, "results": [f"设置车道数量失败: {err}"]}


def _handle_set_tree_density(params, context):
    """Set park tree density (Socket_159) and street tree delete prob (Socket_172).
    Street tree delete is inverted: density 0 → delete prob 1 (remove all)."""
    density = float(params.get("density", 0.5))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到 City_Generator_2.0 修改器。"]}
    results = []
    # Park tree density
    ok, err = _set_socket(mod, "Socket_159", density)
    if ok:
        results.append(f"公园树木密度已设置为 {density}")
    else:
        results.append(f"公园树木密度失败: {err}")
    # Street tree delete probability (inverse of density)
    street_delete = max(0.0, min(1.0, 1.0 - density))
    ok2, err2 = _set_socket(mod, "Socket_172", street_delete)
    if ok2:
        results.append(f"街道树木删除概率已设置为 {street_delete:.2f}")
    else:
        results.append(f"街道树木删除失败: {err2}")
    return {"success": True, "results": results}


def _handle_set_sidewalk_scale(params, context):
    scale = float(params.get("scale", 1.0))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_16", scale)
    if ok:
        return {"success": True, "results": [f"人行道缩放已设置为 {scale}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _handle_set_corner_radius(params, context):
    radius = float(params.get("radius", 3.0))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_22", radius)
    if ok:
        return {"success": True, "results": [f"路口圆角半径已设置为 {radius}m"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _handle_set_parking_probability(params, context):
    prob = float(params.get("probability", 0.5))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_20", max(0.0, min(1.0, prob)))
    if ok:
        return {"success": True, "results": [f"停车道概率已设置为 {prob}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _handle_set_street_lights(params, context):
    """Socket_64 is bool — switch street lights on/off."""
    enable = _to_bool(params.get("enable", True))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_64", enable)
    if ok:
        return {"success": True, "results": [f"路灯已{'开启' if enable else '关闭'}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _handle_set_traffic_lights(params, context):
    prob = float(params.get("probability", 0.6))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_83", max(0.0, min(1.0, prob)))
    if ok:
        return {"success": True, "results": [f"交通灯概率已设置为 {prob}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _handle_set_building_height(params, context):
    """Set Custom_Height face attribute on ALL faces of the active mesh."""
    height = int(params.get("height", 10))
    context.scene.height_value = height
    obj = context.object if hasattr(context, 'object') else context.view_layer.objects.active
    if not obj or obj.type != 'MESH':
        return {"success": False, "results": [f"建筑高度设置失败：活动对象不是网格（当前: {obj.type if obj else 'None'}）"]}

    orig_mode = obj.mode
    if orig_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    try:
        mesh = obj.data
        if "Custom_Height" not in mesh.attributes:
            mesh.attributes.new(name="Custom_Height", type='INT', domain='FACE')
        attr = mesh.attributes["Custom_Height"]
        count = 0
        for poly in mesh.polygons:
            try:
                attr.data[poly.index].value = height
                count += 1
            except Exception:
                pass
    except Exception as e:
        return {"success": False, "results": [f"建筑高度设置失败: {e}"]}
    finally:
        if orig_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=orig_mode)
            except Exception:
                pass

    obj.update_tag()
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass

    return {"success": True, "results": [f"建筑高度已设置为 {height}m（已应用到 {count} 个面）"]}


def _handle_set_seed(params, context):
    seed = float(params.get("seed", 0.0))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_21", seed)
    if ok:
        return {"success": True, "results": [f"随机种子已设置为 {seed}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _to_bool(val):
    """Convert value to bool safely. bool('false') == True in Python, so handle strings."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "on")
    if isinstance(val, (int, float)):
        return val != 0
    return False


def _handle_toggle_traffic(params, context):
    enable = _to_bool(params.get("enable", True))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_144", enable)
    state = "启用" if enable else "禁用"
    if ok:
        return {"success": True, "results": [f"交通元素已{state}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


def _handle_toggle_buildings(params, context):
    enable = _to_bool(params.get("enable", True))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_142", enable)
    state = "启用" if enable else "禁用"
    if ok:
        return {"success": True, "results": [f"建筑元素已{state}"]}
    return {"success": False, "results": [f"设置失败: {err}"]}


# --- Member C: Ecological Scene handlers ---

def _handle_generate_terrain(params, context):
    scene = context.scene
    if "hill_height" in params:
        scene.cg_terrain_hill_height = float(params["hill_height"])
    if "noise_scale" in params:
        scene.cg_terrain_noise_scale = float(params["noise_scale"])
    if "grid_size" in params:
        scene.cg_terrain_grid_size = float(params["grid_size"])
    if "subdivisions" in params:
        scene.cg_terrain_subdivisions = int(params["subdivisions"])
    bpy.ops.cg.eco_generate_terrain()
    return {"success": True, "results": [f"地形已生成（高度={scene.cg_terrain_hill_height}m）"]}


def _handle_generate_lake(params, context):
    scene = context.scene
    if "lake_size" in params:
        scene.cg_lake_size = float(params["lake_size"])
    if "ripple_strength" in params:
        scene.cg_lake_ripple_strength = float(params["ripple_strength"])
    if "water_color" in params and isinstance(params["water_color"], list):
        scene.cg_lake_water_color = tuple(params["water_color"])
    bpy.ops.cg.eco_generate_lake()
    return {"success": True, "results": [f"湖泊已生成（大小={scene.cg_lake_size}m）"]}


def _handle_generate_river(params, context):
    scene = context.scene
    if "river_width" in params:
        scene.cg_river_width = float(params["river_width"])
    if "seed" in params:
        scene.cg_river_seed = int(params["seed"])
    bpy.ops.cg.eco_generate_river()
    return {"success": True, "results": [f"河流已生成（宽度={scene.cg_river_width}m）"]}


def _handle_add_boat(params, context):
    scene = context.scene
    if "boat_scale" in params:
        scene.cg_boat_scale = float(params["boat_scale"])
    if "flow_speed" in params:
        scene.cg_river_flow_speed = float(params["flow_speed"])
    bpy.ops.cg.eco_add_boat()
    return {"success": True, "results": ["船只已添加到河流路径上"]}


# --- Member D: Dynamic Simulation handlers ---

def _handle_start_simulation(params, context):
    scene = context.scene
    if "car_density" in params:
        scene.cg_car_density = int(params["car_density"])
    if "car_speed_min" in params:
        scene.cg_car_speed_min = int(params["car_speed_min"])
    if "car_speed_max" in params:
        scene.cg_car_speed_max = int(params["car_speed_max"])
    if "pedestrian_density" in params:
        scene.cg_pedestrian_density = int(params["pedestrian_density"])
    if "traffic_light_green" in params:
        scene.cg_traffic_light_green = int(params["traffic_light_green"])
    try:
        bpy.ops.cg.add_dynamic_elements()
        return {"success": True, "results": ["仿真已启动（车辆+行人+红绿灯）"]}
    except Exception as e:
        return {"success": False, "results": [f"仿真启动失败: {str(e)}"]}


def _handle_stop_simulation(params, context):
    bpy.ops.cg.remove_dynamic_elements()
    return {"success": True, "results": ["仿真已停止，所有动态元素已清除"]}


# --- Member D: Layout handlers ---

def _handle_apply_layout(params, context):
    scene = context.scene
    if "points" in params:
        pts = params["points"]
        if isinstance(pts, list):
            scene.cg_layout_points_text = ";".join(
                f"{p[0]},{p[1]}" if isinstance(p, (list, tuple)) else str(p)
                for p in pts
            )
    bpy.ops.cg.apply_point_layout()
    return {"success": True, "results": ["道路布局已生成"]}


def _handle_sketch_layout(params, context):
    scene = context.scene
    if "image_path" in params:
        scene.cg_sketch_image_path = str(params["image_path"])
    if "threshold" in params:
        scene.cg_sketch_threshold = int(params["threshold"])
    bpy.ops.cg.apply_sketch_layout()
    return {"success": True, "results": ["草图布局提取已完成"]}


# --- Member A: Template, Texture, Asset handlers ---

def _ensure_cg_active(context):
    """Make the object with CG modifier the active object. Returns the modifier or None."""
    mod = _get_active_mod(context)
    if mod:
        try:
            context.view_layer.objects.active = mod.id_data
        except Exception:
            pass
    return mod


def _handle_apply_scene_template(params, context):
    template_id = str(params.get("template_id", 0))
    _ensure_cg_active(context)
    from .template_engine import apply_scene_template_function
    try:
        result = apply_scene_template_function(context, template_id)
        return {"success": True, "results": [f"模板「{result.get('template_name', template_id)}」已应用"]}
    except Exception as e:
        return {"success": False, "results": [f"模板失败: {str(e)}"]}


def _handle_apply_road_texture(params, context):
    tid = int(params.get("texture_id", 0))
    _ensure_cg_active(context)
    context.scene.road_texture_id = tid
    try:
        bpy.ops.cg.apply_road_texture()
        return {"success": True, "results": [f"道路纹理已切换为 ID {tid}"]}
    except Exception as e:
        return {"success": False, "results": [f"道路纹理失败: {str(e)}"]}


def _handle_apply_pavement_texture(params, context):
    tid = int(params.get("texture_id", 0))
    _ensure_cg_active(context)
    context.scene.pavement_texture_id = tid
    try:
        bpy.ops.cg.apply_pavement_texture()
        return {"success": True, "results": [f"人行道纹理已切换为 ID {tid}"]}
    except Exception as e:
        return {"success": False, "results": [f"人行道纹理失败: {str(e)}"]}


def _handle_place_furniture(params, context):
    """Place 3D furniture with all panel-exposed parameters."""
    scene = context.scene
    valid_assets = {"wooden_picnic_table", "small_lpg_tank", "rubber_duck_toy"}
    if "asset_id" in params:
        aid = str(params["asset_id"])
        if aid not in valid_assets:
            aid = "wooden_picnic_table"
        scene.added_3d_asset_id = aid
    if "min_count" in params:
        scene.added_3d_asset_min_count = int(params["min_count"])
    if "max_count" in params:
        scene.added_3d_asset_max_count = int(params["max_count"])
    if "spacing" in params:
        scene.added_3d_asset_spacing = float(params["spacing"])
    if "scale" in params:
        scene.added_3d_asset_scale = float(params["scale"])
    if "randomize" in params:
        scene.added_3d_asset_randomize = bool(params["randomize"])
    if "placement_offset" in params:
        scene.added_3d_asset_placement_offset = float(params["placement_offset"])
    if "clear_previous" in params:
        scene.added_3d_asset_clear_previous = bool(params["clear_previous"])
    _ensure_cg_active(context)
    try:
        bpy.ops.cg.apply_added_3d_asset()
        return {"success": True, "results": [f"家具「{scene.added_3d_asset_id}」已放置"]}
    except Exception as e:
        return {"success": False, "results": [f"家具放置失败: {str(e)}"]}


def _handle_delete_furniture(params, context):
    """Delete all placed instances of a specific 3D asset type."""
    scene = context.scene
    valid_assets = {"wooden_picnic_table", "small_lpg_tank", "rubber_duck_toy"}
    if "asset_id" in params:
        aid = str(params["asset_id"])
        if aid in valid_assets:
            scene.added_3d_asset_id = aid
    _ensure_cg_active(context)
    try:
        bpy.ops.cg.delete_selected_mesh_3d_asset()
        return {"success": True, "results": [f"已删除所有「{scene.added_3d_asset_id}」资产"]}
    except Exception as e:
        return {"success": False, "results": [f"删除失败: {str(e)}"]}


def _handle_apply_layout_template(params, context):
    scene = context.scene
    if "layout_id" in params:
        scene.layout_template_id = int(params["layout_id"])
    if "rows" in params:
        scene.layout_template_rows = int(params["rows"])
    if "columns" in params:
        scene.layout_template_columns = int(params["columns"])
    try:
        bpy.ops.cg.apply_layout_template()
        return {"success": True, "results": ["布局模板已应用"]}
    except Exception as e:
        return {"success": False, "results": [f"布局模板失败: {str(e)}"]}


# --- Registry ---

FUNCTION_REGISTRY = {
    "apply_template_linkage": {
        "name": "apply_template_linkage",
        "title": "模板联动配置",
        "category": "layout",
        "description": "根据模板规则联动道路、树木、座椅与密度。模板ID 0-9",
        "risk": "low",
        "schemaSummary": "template_id, tree_density, road_width",
        "parameters": {
            "template_id": {"type": "integer", "description": "模板编号 (0-9)", "required": True},
            "tree_density": {"type": "integer", "description": "树木密度百分比 (0-100)", "required": False},
            "road_width": {"type": "integer", "description": "道路宽度（米）", "required": False},
        },
        "handler": _handle_apply_template,
    },
    "set_weather_lighting": {
        "name": "set_weather_lighting",
        "title": "天气与天色控制",
        "category": "environment",
        "description": "设置天气状况和时间，自动调整环境光照",
        "risk": "low",
        "schemaSummary": "weather, time_of_day",
        "parameters": {
            "weather": {"type": "string", "description": "天气：晴/多云/阴/小雨/大雨/雪/雾", "required": True},
            "time_of_day": {"type": "string", "description": "时间 HH:MM，如 08:00, 14:30, 20:00", "required": True},
        },
        "handler": _handle_set_weather,
    },
    "set_street_width": {
        "name": "set_street_width",
        "title": "道路宽度设置",
        "category": "layout",
        "description": "调整城市道路的宽度",
        "risk": "low",
        "schemaSummary": "width",
        "parameters": {"width": {"type": "number", "description": "道路宽度（米）", "required": True}},
        "handler": _handle_set_street_width,
    },
    "set_lane_amount": {
        "name": "set_lane_amount",
        "title": "车道数量设置",
        "category": "layout",
        "description": "调整道路车道数量",
        "risk": "low",
        "schemaSummary": "lanes",
        "parameters": {"lanes": {"type": "integer", "description": "车道数量", "required": True}},
        "handler": _handle_set_lane_amount,
    },
    "set_tree_density": {
        "name": "set_tree_density",
        "title": "树木密度设置",
        "category": "environment",
        "description": "调整街道树木密度因子",
        "risk": "low",
        "schemaSummary": "density",
        "parameters": {"density": {"type": "number", "description": "树木密度因子 (0.0-1.0)", "required": True}},
        "handler": _handle_set_tree_density,
    },
    "set_sidewalk_scale": {
        "name": "set_sidewalk_scale",
        "title": "人行道缩放",
        "category": "layout",
        "description": "调整人行道宽度缩放比例",
        "risk": "low",
        "schemaSummary": "scale",
        "parameters": {"scale": {"type": "number", "description": "缩放比例 (0.5-3.0)", "required": True}},
        "handler": _handle_set_sidewalk_scale,
    },
    "set_corner_radius": {
        "name": "set_corner_radius",
        "title": "路口圆角半径",
        "category": "layout",
        "description": "调整道路交叉口的圆角半径",
        "risk": "low",
        "schemaSummary": "radius",
        "parameters": {"radius": {"type": "number", "description": "圆角半径（米）", "required": True}},
        "handler": _handle_set_corner_radius,
    },
    "set_parking_probability": {
        "name": "set_parking_probability",
        "title": "停车道概率",
        "category": "layout",
        "description": "调整路边停车道的出现概率",
        "risk": "low",
        "schemaSummary": "probability",
        "parameters": {"probability": {"type": "number", "description": "概率 (0.0-1.0)", "required": True}},
        "handler": _handle_set_parking_probability,
    },
    "set_street_lights": {
        "name": "set_street_lights",
        "title": "路灯开关",
        "category": "environment",
        "description": "开启或关闭路灯（Socket_64 为 bool 类型）",
        "risk": "low",
        "schemaSummary": "enable",
        "parameters": {"enable": {"type": "boolean", "description": "true=开, false=关", "required": True}},
        "handler": _handle_set_street_lights,
    },
    "set_traffic_lights": {
        "name": "set_traffic_lights",
        "title": "交通灯概率",
        "category": "layout",
        "description": "调整交通信号灯的分布概率",
        "risk": "low",
        "schemaSummary": "probability",
        "parameters": {"probability": {"type": "number", "description": "概率 (0.0-1.0)", "required": True}},
        "handler": _handle_set_traffic_lights,
    },
    "set_building_height": {
        "name": "set_building_height",
        "title": "建筑高度设置",
        "category": "layout",
        "description": "设置自定义建筑高度值（配合面选择使用）",
        "risk": "low",
        "schemaSummary": "height",
        "parameters": {"height": {"type": "integer", "description": "建筑高度（米）", "required": True}},
        "handler": _handle_set_building_height,
    },
    "set_seed": {
        "name": "set_seed",
        "title": "随机种子",
        "category": "layout",
        "description": "设置全局随机种子",
        "risk": "low",
        "schemaSummary": "seed",
        "parameters": {"seed": {"type": "number", "description": "随机种子值", "required": True}},
        "handler": _handle_set_seed,
    },
    "toggle_traffic": {
        "name": "toggle_traffic",
        "title": "交通元素开关",
        "category": "simulation",
        "description": "启用或禁用交通模拟元素",
        "risk": "medium",
        "schemaSummary": "enable",
        "parameters": {"enable": {"type": "boolean", "description": "true=启用, false=禁用", "required": True}},
        "handler": _handle_toggle_traffic,
    },
    "toggle_buildings": {
        "name": "toggle_buildings",
        "title": "建筑元素开关",
        "category": "layout",
        "description": "启用或禁用建筑元素显示",
        "risk": "medium",
        "schemaSummary": "enable",
        "parameters": {"enable": {"type": "boolean", "description": "true=启用, false=禁用", "required": True}},
        "handler": _handle_toggle_buildings,
    },
    # --- Member C: Ecological Scene ---
    "generate_terrain": {
        "name": "generate_terrain",
        "title": "生成山丘地形",
        "category": "environment",
        "description": "程序化生成有起伏的地形（噪声位移）",
        "risk": "low",
        "schemaSummary": "hill_height, noise_scale, grid_size",
        "parameters": {
            "hill_height": {"type": "number", "description": "山丘高度（米）", "required": False},
            "noise_scale": {"type": "number", "description": "噪声缩放（0.1-5.0）", "required": False},
            "grid_size": {"type": "number", "description": "地形网格大小（米）", "required": False},
        },
        "handler": _handle_generate_terrain,
    },
    "generate_lake": {
        "name": "generate_lake",
        "title": "生成湖泊",
        "category": "environment",
        "description": "生成圆形湖泊水面（含波纹材质）",
        "risk": "low",
        "schemaSummary": "lake_size, ripple_strength",
        "parameters": {
            "lake_size": {"type": "number", "description": "湖泊大小（半径米）", "required": False},
            "ripple_strength": {"type": "number", "description": "波纹强度 (0-1)", "required": False},
        },
        "handler": _handle_generate_lake,
    },
    "generate_river": {
        "name": "generate_river",
        "title": "生成河流",
        "category": "environment",
        "description": "沿曲线生成河流水面路径",
        "risk": "low",
        "schemaSummary": "river_width, seed",
        "parameters": {
            "river_width": {"type": "number", "description": "河流宽度（米）", "required": False},
            "seed": {"type": "integer", "description": "随机种子", "required": False},
        },
        "handler": _handle_generate_river,
    },
    "add_boat": {
        "name": "add_boat",
        "title": "添加船只",
        "category": "environment",
        "description": "在河流上添加动态船只（沿路径移动）",
        "risk": "low",
        "schemaSummary": "boat_scale, flow_speed",
        "parameters": {
            "boat_scale": {"type": "number", "description": "船只缩放比例", "required": False},
            "flow_speed": {"type": "number", "description": "水流速度", "required": False},
        },
        "handler": _handle_add_boat,
    },
    # --- Member D: Dynamic Simulation ---
    "run_traffic_simulation": {
        "name": "run_traffic_simulation",
        "title": "车辆仿真调度",
        "category": "simulation",
        "description": "启动车辆交通仿真",
        "risk": "medium",
        "schemaSummary": "rules_version, seed",
        "parameters": {
            "rules_version": {"type": "string", "description": "规则版本", "required": False},
            "seed": {"type": "integer", "description": "随机种子", "required": False},
        },
        "handler": _handle_start_simulation,
    },
    "run_crowd_simulation": {
        "name": "run_crowd_simulation",
        "title": "人群仿真调度",
        "category": "simulation",
        "description": "启动人群仿真",
        "risk": "medium",
        "schemaSummary": "rules_version, seed, agent_count",
        "parameters": {
            "rules_version": {"type": "string", "description": "规则版本", "required": False},
            "seed": {"type": "integer", "description": "随机种子", "required": False},
            "agent_count": {"type": "integer", "description": "行人数量", "required": False},
        },
        "handler": _handle_start_simulation,
    },
    "start_simulation": {
        "name": "start_simulation",
        "title": "启动交通仿真",
        "category": "simulation",
        "description": "启动车辆+行人+红绿灯的动态仿真",
        "risk": "medium",
        "schemaSummary": "car_density, pedestrian_density, car_speed_min, car_speed_max",
        "parameters": {
            "car_density": {"type": "number", "description": "车辆密度", "required": False},
            "car_speed_min": {"type": "number", "description": "最低车速 km/h", "required": False},
            "car_speed_max": {"type": "number", "description": "最高车速 km/h", "required": False},
            "pedestrian_density": {"type": "number", "description": "行人密度", "required": False},
        },
        "handler": _handle_start_simulation,
    },
    "stop_simulation": {
        "name": "stop_simulation",
        "title": "停止仿真",
        "category": "simulation",
        "description": "停止仿真并清除所有动态元素",
        "risk": "low",
        "schemaSummary": "none",
        "parameters": {},
        "handler": _handle_stop_simulation,
    },
    # --- Member D: Road Layout ---
    "apply_layout": {
        "name": "apply_layout",
        "title": "应用坐标布局",
        "category": "layout",
        "description": "根据手动坐标点集生成道路布局",
        "risk": "medium",
        "schemaSummary": "points",
        "parameters": {
            "points": {"type": "array", "description": "坐标点列表 [[x,y],[x,y],...]", "required": False},
        },
        "handler": _handle_apply_layout,
    },
    "sketch_layout": {
        "name": "sketch_layout",
        "title": "草图提取布局",
        "category": "layout",
        "description": "从草图图像提取道路拓扑并生成布局",
        "risk": "medium",
        "schemaSummary": "image_path, threshold",
        "parameters": {
            "image_path": {"type": "string", "description": "草图图像文件路径", "required": True},
            "threshold": {"type": "integer", "description": "边缘检测阈值", "required": False},
        },
        "handler": _handle_sketch_layout,
    },
    # --- Member A: Scene Template ---
    "apply_scene_template": {
        "name": "apply_scene_template",
        "title": "场景模板",
        "category": "layout",
        "description": "应用预设场景模板 (0=滨水, 1=商业街, 2=枢纽)",
        "risk": "low",
        "schemaSummary": "template_id",
        "parameters": {"template_id": {"type": "integer", "description": "模板号 0-2", "required": True}},
        "handler": _handle_apply_scene_template,
    },
    # --- Member A: Road Textures ---
    "apply_road_texture": {
        "name": "apply_road_texture",
        "title": "道路纹理",
        "category": "asset",
        "description": "切换道路纹理材质 (0=默认, 1=干净, 2=脏旧等)",
        "risk": "low",
        "schemaSummary": "texture_id",
        "parameters": {"texture_id": {"type": "integer", "description": "纹理ID", "required": True}},
        "handler": _handle_apply_road_texture,
    },
    "apply_pavement_texture": {
        "name": "apply_pavement_texture",
        "title": "人行道纹理",
        "category": "asset",
        "description": "切换人行道铺装纹理",
        "risk": "low",
        "schemaSummary": "texture_id",
        "parameters": {"texture_id": {"type": "integer", "description": "纹理ID", "required": True}},
        "handler": _handle_apply_pavement_texture,
    },
    # --- Member A: Furniture Assets ---
    "place_furniture": {
        "name": "place_furniture",
        "title": "放置城市家具",
        "category": "asset",
        "description": "在城市对象周围放置 3D 家具（野餐椅/小消防罐/小黄鸭）",
        "risk": "low",
        "schemaSummary": "asset_id, min_count, max_count, spacing, scale, randomize, placement_offset, clear_previous",
        "parameters": {
            "asset_id": {"type": "string", "description": "资产: wooden_picnic_table(野餐椅)/small_lpg_tank(小消防罐)/rubber_duck_toy(小黄鸭)", "required": False},
            "min_count": {"type": "integer", "description": "最少放置数量", "required": False},
            "max_count": {"type": "integer", "description": "最多放置数量", "required": False},
            "spacing": {"type": "number", "description": "资产间距（米）", "required": False},
            "scale": {"type": "number", "description": "缩放比例", "required": False},
            "randomize": {"type": "boolean", "description": "是否随机布局", "required": False},
            "placement_offset": {"type": "number", "description": "放置偏移（米）", "required": False},
            "clear_previous": {"type": "boolean", "description": "是否清除同类旧资产", "required": False},
        },
        "handler": _handle_place_furniture,
    },
    "delete_furniture": {
        "name": "delete_furniture",
        "title": "删除新增城市家具",
        "category": "asset",
        "description": "删除之前通过 place_furniture 新增到当前 CG 网格上的指定类型 3D 家具（野餐椅/小消防罐/小黄鸭）",
        "risk": "low",
        "schemaSummary": "asset_id",
        "parameters": {
            "asset_id": {"type": "string", "description": "资产: wooden_picnic_table(野餐椅)/small_lpg_tank(小消防罐)/rubber_duck_toy(小黄鸭)", "required": True},
        },
        "handler": _handle_delete_furniture,
    },
    # --- Member A: Layout Template ---
    "apply_layout_template": {
        "name": "apply_layout_template",
        "title": "布局模板",
        "category": "layout",
        "description": "应用预设网格布局模板",
        "risk": "low",
        "schemaSummary": "layout_id, rows, columns",
        "parameters": {
            "layout_id": {"type": "integer", "description": "布局ID", "required": False},
            "rows": {"type": "integer", "description": "行数", "required": False},
            "columns": {"type": "integer", "description": "列数", "required": False},
        },
        "handler": _handle_apply_layout_template,
    },
}


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


def get_registry_for_prompt():
    lines = []
    for name, func in FUNCTION_REGISTRY.items():
        params_desc = ", ".join(
            f"{p}({info['type']}{'*' if info.get('required') else ''})"
            for p, info in func["parameters"].items()
        )
        lines.append(f"- {name}: {func['description']} 参数: {params_desc}")
    return "\n".join(lines)


def execute_function(name, params, context):
    func = FUNCTION_REGISTRY.get(name)
    if not func:
        return {"success": False, "results": [f"未知函数: {name}"]}
    try:
        return func["handler"](params, context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "results": [f"执行 {name} 时出错: {str(e)}"]}


def execute_functions(function_calls, context):
    results = []
    for call in function_calls:
        name = call.get("name", "")
        params = call.get("params", {})
        result = execute_function(name, params, context)
        results.append({"function": name, **result})
    return results


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
