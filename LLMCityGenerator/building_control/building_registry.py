"""Building registry -- singleton that tracks controlled buildings with a
dual-layer index: Blender custom properties (persistence) + in-memory dict
(fast lookup).

BuildingRecord: lightweight data object holding one building's metadata.
BuildingRegistry: singleton managing the id-to-record dict and spatial index.

Lifecycle:
    1. On blend file load (load_post handler), rebuild_from_scene() scans
       all objects with cg.is_controlled_building and reconstructs the index.
    2. On register() call after placing a new building, the record is added.
    3. On unregister() / delete, the record (and spatial entry) is removed.
"""

from dataclasses import dataclass, field

from .spatial_index import GridSpatialIndex


@dataclass
class BuildingRecord:
    """Metadata for one controlled building."""
    id: str           # e.g. "B_0001"
    obj_name: str     # Blender object name
    x: float          # center X
    y: float          # center Y
    width: float      # extent along X
    depth: float      # extent along Y
    height: float     # extent along Z
    color: str = ""   # hex color string, e.g. "#CC8844"


class BuildingRegistry:
    """Singleton -- one instance per Blender session."""

    _instance = None

    def __init__(self):
        self._buildings = {}        # {building_id: BuildingRecord}
        self._spatial = GridSpatialIndex(cell_size=10.0)

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Drop the current instance (useful for testing or reload)."""
        cls._instance = None

    # ------------------------------------------------------------------
    # Spatial delegate
    # ------------------------------------------------------------------

    def check_overlap(self, x, y, width, depth, exclude_id=None):
        """Return conflicting building ID, or None."""
        return self._spatial.query_overlap(x, y, width, depth, exclude_id)

    def find_at_point(self, x, y):
        """Return building ID at (x, y), or None."""
        return self._spatial.query_point(x, y)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def register(self, building_id, obj_name, x, y, width, depth, height, color=""):
        """Add a new building record and insert into spatial index."""
        building_id = str(building_id)
        if building_id in self._buildings:
            raise KeyError(f"building_id {building_id} already registered")
        record = BuildingRecord(
            id=building_id, obj_name=obj_name,
            x=x, y=y, width=width, depth=depth, height=height, color=color,
        )
        self._buildings[building_id] = record
        self._spatial.add(building_id, x, y, width, depth)
        return record

    def unregister(self, building_id):
        """Remove a building record and its spatial entry."""
        building_id = str(building_id)
        if building_id not in self._buildings:
            raise KeyError(f"building_id {building_id!r} not found")
        del self._buildings[building_id]
        self._spatial.remove(building_id)

    def move(self, building_id, new_x, new_y):
        """Update a building's position in both the record and spatial index."""
        building_id = str(building_id)
        record = self._buildings.get(building_id)
        if record is None:
            raise KeyError(f"building_id {building_id!r} not found")
        self._spatial.move(building_id, new_x, new_y)
        record.x = new_x
        record.y = new_y

    def get(self, building_id):
        """Return BuildingRecord or None."""
        return self._buildings.get(str(building_id))

    def list_all(self):
        """Return a list of BuildingRecord sorted by id."""
        return sorted(self._buildings.values(), key=lambda r: r.id)

    @property
    def count(self):
        return len(self._buildings)

    # ------------------------------------------------------------------
    # Persistence: rebuild from Blender scene objects
    # ------------------------------------------------------------------

    def rebuild_from_scene(self):
        """Scan all objects in bpy.data.objects for cg.is_controlled_building.

        Drop current in-memory state and repopulate from Blender data.
        """
        import bpy

        self._buildings.clear()
        self._spatial.clear()

        for obj in bpy.data.objects:
            if not obj.get("cg.is_controlled_building", False):
                continue
            bid = obj.get("cg.building_id", "")
            if not bid:
                continue
            w = obj.get("cg.building_width", 10.0)
            d = obj.get("cg.building_depth", 10.0)
            h = obj.get("cg.building_height", 20.0)
            color = obj.get("cg.building_color", "")
            record = BuildingRecord(
                id=str(bid), obj_name=obj.name,
                x=obj.location.x, y=obj.location.y,
                width=w, depth=d, height=h, color=str(color),
            )
            self._buildings[str(bid)] = record
            self._spatial.add(str(bid), obj.location.x, obj.location.y, w, d)
