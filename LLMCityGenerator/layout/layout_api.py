"""LLM-callable function API for road layout control (Task 2 / 成员 D).

Exports ``LAYOUT_REGISTRY`` dict — member B imports it directly into
``function_registry.py`` to register these functions for LLM dispatch.
"""

import bpy
from .point_solver import PointSolver
from .sketch_processor import SketchProcessor


# ---------------------------------------------------------------------------
# Individual functions
# ---------------------------------------------------------------------------

def solve_point_layout(params=None):
    """Generate a road-layout mesh from coordinate points.

    Args:
        params (dict):
            points (required):  ``[[x1,y1], [x2,y2], ...]``
            connections:       ``[[i,j], [k,l], ...]`` (optional — if omitted,
                               points are connected sequentially)
            mesh_name:         name for the new mesh object (default "RoadLayout")

    Returns:
        {"success": True, "data": {"mesh_name": str, "vertex_count": int, "edge_count": int}}
    """
    if params is None:
        params = {}

    points = params.get("points")
    if not points:
        return {"success": False, "message": "Missing required param 'points'"}

    connections = params.get("connections", None)
    mesh_name = params.get("mesh_name", "RoadLayout")

    try:
        obj = PointSolver.create_mesh(points, connections, mesh_name)
        return {
            "success": True,
            "data": {
                "mesh_name": obj.name,
                "vertex_count": len(obj.data.vertices),
                "edge_count": len(obj.data.edges),
            },
            "message": f"Mesh '{obj.name}' created — "
                       f"{len(obj.data.vertices)} vertices, "
                       f"{len(obj.data.edges)} edges",
        }
    except Exception as exc:
        return {"success": False, "message": str(exc)}


def extract_sketch_topology(params=None):
    """Extract road topology from a hand-drawn sketch image.

    Args:
        params (dict):
            image_path (required):  absolute path to the sketch image
            method:                 "cv2", "llm", or "auto" (default)
            threshold:              edge-detection threshold 0.1-1.0
            min_line_length:        minimum line length in pixels (default 30)
            mesh_name:              output mesh name (default "RoadLayout")

    Returns:
        {"success": True, "data": {"mesh_name": ..., "vertex_count": ..., "method": ...}}
    """
    if params is None:
        params = {}

    image_path = params.get("image_path")
    if not image_path:
        return {"success": False, "message": "Missing required param 'image_path'"}

    method = params.get("method", "auto")
    threshold = float(params.get("threshold", 0.5))
    min_line_length = int(params.get("min_line_length", 30))
    mesh_name = params.get("mesh_name", "RoadLayout")

    return SketchProcessor.process(
        image_path=image_path,
        method=method,
        threshold=threshold,
        min_line_length=min_line_length,
        mesh_name=mesh_name,
    )


def clear_road_layout(params=None):
    """Delete the current road-layout mesh if it exists.

    Returns:
        {"success": True, "message": "..."}
    """
    obj = bpy.data.objects.get("RoadLayout")
    if obj is not None:
        mesh = obj.data
        bpy.data.objects.remove(obj)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
        return {"success": True, "message": "RoadLayout mesh removed"}
    return {"success": False, "message": "No RoadLayout mesh found"}


# ---------------------------------------------------------------------------
# Handler map
# ---------------------------------------------------------------------------

_LAYOUT_HANDLERS = {
    "solve_point_layout": solve_point_layout,
    "extract_sketch_topology": extract_sketch_topology,
    "clear_road_layout": clear_road_layout,
}


def layout_dispatch(function_name, params=None):
    """Dispatch a layout function by name (used by the unified dispatcher)."""
    handler = _LAYOUT_HANDLERS.get(function_name)
    if handler is None:
        return {"success": False, "message": f"Unknown layout function: {function_name}"}
    try:
        return handler(params=params)
    except Exception as exc:
        return {"success": False, "message": str(exc)}


# ---------------------------------------------------------------------------
# Registry for member B
# ---------------------------------------------------------------------------

LAYOUT_REGISTRY = {
    "solve_point_layout": {
        "function": solve_point_layout,
        "description": "根据坐标点集生成道路布局 mesh（顶点=路口，边=道路）",
        "params": {
            "points": {
                "type": "array",
                "description": "路口坐标列表，格式 [[x1,y1],[x2,y2],...]",
                "required": True,
            },
            "connections": {
                "type": "array",
                "description": "边连接关系 [[i,j],[k,l],...]，不填则按顺序连接",
                "required": False,
                "default": None,
            },
            "mesh_name": {
                "type": "string",
                "description": "输出 mesh 名称",
                "default": "RoadLayout",
            },
        },
    },
    "extract_sketch_topology": {
        "function": extract_sketch_topology,
        "description": "从手绘草图图像提取道路拓扑并生成 mesh",
        "params": {
            "image_path": {
                "type": "string",
                "description": "草图图像文件的绝对路径",
                "required": True,
            },
            "method": {
                "type": "string",
                "enum": ["cv2", "llm", "auto"],
                "default": "auto",
                "description": "auto=优先 cv2，不可用时用 LLM",
            },
            "threshold": {
                "type": "float", "min": 0.1, "max": 1.0, "default": 0.5,
                "description": "边缘检测阈值（cv2 模式）",
            },
            "min_line_length": {
                "type": "int", "min": 5, "max": 500, "default": 30,
                "description": "最小线段长度（像素）",
            },
            "mesh_name": {
                "type": "string", "default": "RoadLayout",
                "description": "输出 mesh 名称",
            },
        },
    },
    "clear_road_layout": {
        "function": clear_road_layout,
        "description": "删除当前道路布局 mesh",
        "params": {},
    },
}
