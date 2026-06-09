"""Grid-based spatial hash index for AABB collision detection on the XY plane.

Pure Python implementation -- no external dependencies required.
Divides the XY plane into cells of CELL_SIZE x CELL_SIZE (default 10m).
Each cell stores a set of building IDs that overlap with it.

Typical use:
    idx = GridSpatialIndex(cell_size=10.0)
    idx.add("B_0001", 50.0, 30.0, 10.0, 10.0)
    conflict = idx.query_overlap(55.0, 35.0, 10.0, 10.0)  # -> "B_0001"
"""

import math
from collections import defaultdict


def _aabb_overlap(ax, ay, aw, ad, bx, by, bw, bd):
    """Return True if two axis-aligned rectangles (x,y,width,depth) overlap.

    Overlap is strict: edges that merely touch (share a boundary line) do NOT
    count as overlapping.
    """
    return not (
        ax + aw < bx or   # a is completely to the left of b
        bx + bw < ax or   # b is completely to the left of a
        ay + ad < by or   # a is completely below b
        by + bd < ay      # b is completely below a
    )


def _center_to_min(x, y, width, depth):
    """Convert center-based coordinates to min-corner format."""
    hw = width / 2.0
    hd = depth / 2.0
    return (x - hw, y - hd)


class GridSpatialIndex:
    """Spatial index for tracking rectangular building footprints on the XY plane.

    Coordinates use center-based convention: (x, y) is the center of the
    building footprint, width extends along X, depth extends along Y.
    """

    def __init__(self, cell_size=10.0):
        self._cell_size = float(cell_size)
        # self._grid: { (grid_x, grid_y): set of building IDs }
        self._grid = defaultdict(set)
        # self._id_cells: { building_id: set of (grid_x, grid_y) }
        self._id_cells = {}
        # self._id_bounds: { building_id: (min_x, min_y, width, depth) }
        self._id_bounds = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _grid_range(min_val, max_val, cell_size):
        """Return inclusive grid coordinate range for a continuous interval."""
        return range(
            int(math.floor(min_val / cell_size)),
            int(math.floor((max_val) / cell_size)) + 1,
        )

    def _cells_for(self, min_x, min_y, width, depth):
        """Yield (gx, gy) cell coordinates overlapping the given AABB."""
        max_x = min_x + width
        max_y = min_y + depth
        for gx in self._grid_range(min_x, max_x, self._cell_size):
            for gy in self._grid_range(min_y, max_y, self._cell_size):
                yield (gx, gy)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, building_id, x, y, width, depth):
        """Register a building footprint in the spatial index.

        Args:
            building_id: unique string identifier (e.g. "B_0001")
            x, y: center of footprint
            width: extent along X axis
            depth: extent along Y axis
        """
        building_id = str(building_id)
        min_x, min_y = _center_to_min(x, y, width, depth)

        cells = set(self._cells_for(min_x, min_y, width, depth))
        self._id_cells[building_id] = cells
        self._id_bounds[building_id] = (min_x, min_y, width, depth)

        for cell in cells:
            self._grid[cell].add(building_id)

    def remove(self, building_id):
        """Remove a building from the spatial index."""
        building_id = str(building_id)
        cells = self._id_cells.pop(building_id, set())
        self._id_bounds.pop(building_id, None)
        for cell in cells:
            cell_set = self._grid.get(cell)
            if cell_set:
                cell_set.discard(building_id)
                if not cell_set:
                    del self._grid[cell]

    def move(self, building_id, new_x, new_y, width=None, depth=None):
        """Update a building's position in the index.

        Equivalent to remove then add, but maintains the same building_id.
        If width/depth are not provided, the previous values are reused.
        """
        old = self._id_bounds.get(str(building_id))
        if old is None:
            raise KeyError(f"building_id {building_id!r} not found in spatial index")

        w = width if width is not None else old[2]
        d = depth if depth is not None else old[3]
        self.remove(building_id)
        self.add(building_id, new_x, new_y, w, d)

    def query_overlap(self, x, y, width, depth, exclude_id=None):
        """Check if a rectangular region overlaps any existing building.

        Args:
            x, y: center of query region
            width, depth: extent of query region
            exclude_id: optional building ID to ignore (for self-move check)

        Returns:
            The ID of the first overlapping building, or None if the area is clear.
        """
        min_x, min_y = _center_to_min(x, y, width, depth)
        candidates = set()

        for cell in self._cells_for(min_x, min_y, width, depth):
            candidates.update(self._grid.get(cell, set()))

        # Remove excluded ID from candidates
        if exclude_id is not None:
            candidates.discard(str(exclude_id))

        for bid in candidates:
            bx, by, bw, bd = self._id_bounds.get(bid, (0, 0, 0, 0))
            if _aabb_overlap(min_x, min_y, width, depth, bx, by, bw, bd):
                return bid

        return None

    def query_point(self, x, y):
        """Return the building ID that contains the given point, or None."""
        query_min_x = x
        query_min_y = y
        candidates = set()

        for cell in self._cells_for(query_min_x, query_min_y, 0.0, 0.0):
            candidates.update(self._grid.get(cell, set()))

        for bid in candidates:
            bx, by, bw, bd = self._id_bounds.get(bid, (0, 0, 0, 0))
            if bx <= x <= bx + bw and by <= y <= by + bd:
                return bid

        return None

    def get_bounds(self, building_id):
        """Return (min_x, min_y, width, depth) for a building, or None."""
        return self._id_bounds.get(str(building_id))

    @property
    def building_count(self):
        """Number of buildings currently tracked."""
        return len(self._id_cells)

    def clear(self):
        """Remove all buildings from the index."""
        self._grid.clear()
        self._id_cells.clear()
        self._id_bounds.clear()
