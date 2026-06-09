"""Building control package -- position-aware building placement system.

Exports:
    GridSpatialIndex   -- spatial hash for AABB collision detection
    BuildingRecord     -- dataclass for one building's metadata
    BuildingRegistry   -- singleton tracking all controlled buildings

    CG_OT_PlaceBuilding  -- Blender Operator: place a building
    CG_OT_MoveBuilding   -- Blender Operator: move a building
    CG_OT_DeleteBuilding -- Blender Operator: delete a building

    building_handlers  -- dict of {function_name: handler} for function_registry.py
"""

from .spatial_index import GridSpatialIndex
from .building_registry import BuildingRecord, BuildingRegistry
from .building_ops import (
    CG_OT_PlaceBuilding,
    CG_OT_MoveBuilding,
    CG_OT_DeleteBuilding,
)
from .building_api import (
    _handle_place_building,
    _handle_move_building,
    _handle_delete_building,
    _handle_list_buildings,
    _handle_query_space,
)

# Handler map for registration into function_registry.py FUNCTION_REGISTRY
building_handlers = {
    "place_building": _handle_place_building,
    "move_building": _handle_move_building,
    "delete_building": _handle_delete_building,
    "list_buildings": _handle_list_buildings,
    "query_space": _handle_query_space,
}
