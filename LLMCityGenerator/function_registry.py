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
    """Get the GN modifier from the active object."""
    obj = context.object if hasattr(context, 'object') else context.view_layer.objects.active
    return _get_modifier(obj)


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
    prob = float(params.get("probability", 0.8))
    mod = _get_active_mod(context)
    if not mod:
        return {"success": False, "results": ["未找到修改器。"]}
    ok, err = _set_socket(mod, "Socket_64", max(0.0, min(1.0, prob)))
    if ok:
        return {"success": True, "results": [f"路灯密度已设置为 {prob}"]}
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
    height = int(params.get("height", 10))
    context.scene.height_value = height
    return {"success": True, "results": [f"建筑高度值已设为 {height}m（需选中面后使用 Assign Height 按钮应用）"]}


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
        "title": "路灯密度",
        "category": "environment",
        "description": "调整路灯的密度",
        "risk": "low",
        "schemaSummary": "probability",
        "parameters": {"probability": {"type": "number", "description": "密度概率 (0.0-1.0)", "required": True}},
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
