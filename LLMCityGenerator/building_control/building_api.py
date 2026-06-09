"""LLM-callable handler functions for building position control.

Each handler follows the function_registry.py convention:
    handler(params: dict, context: bpy.types.Context) -> dict
    Returns {"success": bool, "results": list[str], "data": ...}
"""

import bpy

from .building_registry import BuildingRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val, default=0.0):
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default


def _safe_str(val, default=""):
    if val is None:
        return default
    return str(val)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _handle_place_building(params, context):
    """Place a new controlled building with overlap detection.

    Required params: x, y
    Optional params: width (default 10), depth (default 10),
                     height (default 20), color (default "")
    """
    x = _safe_float(params.get("x"), 0.0)
    y = _safe_float(params.get("y"), 0.0)
    width = _safe_float(params.get("width"), 10.0)
    depth = _safe_float(params.get("depth"), 10.0)
    height = _safe_float(params.get("height"), 20.0)
    color = _safe_str(params.get("color", ""), "#A0A0A0")

    # Clamp to reasonable ranges
    width = max(1.0, min(width, 500.0))
    depth = max(1.0, min(depth, 500.0))
    height = max(1.0, min(height, 1000.0))

    registry = BuildingRegistry.instance()

    # Overlap check
    conflict = registry.check_overlap(x, y, width, depth)
    if conflict is not None:
        return {
            "success": False,
            "results": [f"位置 ({x:.1f}, {y:.1f}) 与建筑 {conflict} 重叠，放置已取消"],
            "data": {"conflict_id": conflict},
        }

    # Delegate to Blender operator
    try:
        result = bpy.ops.cg.place_building(
            x=x, y=y, width=width, depth=depth, height=height, color=color,
        )
    except Exception as exc:
        return {"success": False, "results": [f"建筑放置失败: {str(exc)}"]}

    if result == {'CANCELLED'}:
        return {"success": False, "results": [f"建筑放置被取消"]}

    # Find the newly created building ID from the last registered building
    all_buildings = registry.list_all()
    if not all_buildings:
        return {"success": False, "results": ["建筑创建完成但注册表中未找到记录"]}

    newest = all_buildings[-1]
    return {
        "success": True,
        "results": [f"建筑 {newest.id} 已放置在 ({x:.1f}, {y:.1f})，尺寸 {width:.1f}x{depth:.1f}x{height:.1f}m"],
        "data": {
            "building_id": newest.id,
            "x": x, "y": y,
            "width": width, "depth": depth, "height": height,
            "color": color,
        },
    }


def _handle_move_building(params, context):
    """Move an existing controlled building.

    Required params: building_id, x, y
    """
    building_id = _safe_str(params.get("building_id"), "")
    x = _safe_float(params.get("x"), 0.0)
    y = _safe_float(params.get("y"), 0.0)

    if not building_id:
        return {"success": False, "results": ["缺少参数 building_id"]}

    registry = BuildingRegistry.instance()

    record = registry.get(building_id)
    if record is None:
        return {"success": False, "results": [f"未找到建筑 {building_id}"]}

    old_x, old_y = record.x, record.y

    try:
        result = bpy.ops.cg.move_building(building_id=building_id, x=x, y=y)
    except Exception as exc:
        return {"success": False, "results": [f"移动建筑失败: {str(exc)}"]}

    if result == {'CANCELLED'}:
        return {"success": False, "results": [f"建筑 {building_id} 移动被取消（可能因目标位置重叠）"]}

    return {
        "success": True,
        "results": [f"建筑 {building_id} 已从 ({old_x:.1f}, {old_y:.1f}) 移动到 ({x:.1f}, {y:.1f})"],
        "data": {"building_id": building_id, "x": x, "y": y,
                  "old_x": old_x, "old_y": old_y},
    }


def _handle_delete_building(params, context):
    """Delete a controlled building.

    Required params: building_id
    """
    building_id = _safe_str(params.get("building_id"), "")

    if not building_id:
        return {"success": False, "results": ["缺少参数 building_id"]}

    registry = BuildingRegistry.instance()

    record = registry.get(building_id)
    if record is None:
        return {"success": False, "results": [f"未找到建筑 {building_id}"]}

    old_x, old_y = record.x, record.y
    try:
        bpy.ops.cg.delete_building(building_id=building_id)
    except Exception as exc:
        return {"success": False, "results": [f"删除建筑失败: {str(exc)}"]}

    return {
        "success": True,
        "results": [f"建筑 {building_id}（位于 ({old_x:.1f}, {old_y:.1f})）已删除"],
        "data": {"building_id": building_id},
    }


def _handle_list_buildings(params, context):
    """List all controlled buildings with their positions and dimensions."""
    registry = BuildingRegistry.instance()
    records = registry.list_all()

    if not records:
        return {
            "success": True,
            "results": ["当前没有受控建筑。使用 place_building 函数创建新建筑。"],
            "data": {"buildings": [], "count": 0},
        }

    building_list = []
    lines = [f"共 {len(records)} 栋受控建筑:"]
    for r in records:
        building_list.append({
            "id": r.id,
            "x": r.x, "y": r.y,
            "width": r.width, "depth": r.depth, "height": r.height,
            "color": r.color,
        })
        lines.append(
            f"  {r.id}: 位置({r.x:.1f}, {r.y:.1f}), "
            f"尺寸 {r.width:.1f}x{r.depth:.1f}x{r.height:.1f}m"
        )

    return {
        "success": True,
        "results": lines,
        "data": {"buildings": building_list, "count": len(records)},
    }


def _handle_query_space(params, context):
    """Check whether a rectangular region is available for building.

    Required params: x, y, width, depth
    """
    x = _safe_float(params.get("x"), 0.0)
    y = _safe_float(params.get("y"), 0.0)
    width = _safe_float(params.get("width"), 10.0)
    depth = _safe_float(params.get("depth"), 10.0)

    registry = BuildingRegistry.instance()
    conflict = registry.check_overlap(x, y, width, depth)

    if conflict is None:
        return {
            "success": True,
            "results": [f"区域 ({x:.1f}, {y:.1f}) 尺寸 {width:.1f}x{depth:.1f}m 可用"],
            "data": {"available": True, "conflict_id": None},
        }
    else:
        conflict_record = registry.get(conflict)
        info = ""
        if conflict_record:
            info = f"（{conflict_record.width:.1f}x{conflict_record.depth:.1f}m）"
        return {
            "success": True,
            "results": [f"区域 ({x:.1f}, {y:.1f}) 与建筑 {conflict} {info} 重叠"],
            "data": {"available": False, "conflict_id": conflict},
        }
