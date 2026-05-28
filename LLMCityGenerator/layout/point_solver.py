"""Point solver — converts coordinate point sets into road-defining meshes.

Every City Generator road is a mesh edge.  This module creates (or updates)
a mesh whose vertices = intersections and edges = road segments.
"""

import bpy
from mathutils import Vector


class PointSolver:
    """Build a road-layout mesh from a list of coordinates."""

    @staticmethod
    def create_mesh(points, connections=None, mesh_name="RoadLayout"):
        """Create a new mesh object from 2-D coordinate points.

        Args:
            points: list of ``(x, y)`` or ``(x, y, z)`` iterables.
            connections: optional list of ``(i, j)`` index pairs.
                When omitted points are connected sequentially (0→1, 1→2, …).
            mesh_name: name for the created object & mesh data.

        Returns:
            The newly-created ``bpy.types.Object`` (type=MESH).
        """
        # Normalise to 3-D
        verts = []
        for p in points:
            if len(p) == 2:
                verts.append(Vector((p[0], p[1], 0.0)))
            else:
                verts.append(Vector((p[0], p[1], p[2])))

        # Build edge list
        if connections:
            edges = [tuple(c) for c in connections]
        else:
            edges = [(i, i + 1) for i in range(len(verts) - 1)]

        # Create mesh data
        mesh_data = bpy.data.meshes.new(mesh_name)
        mesh_data.from_pydata(verts, edges, [])
        mesh_data.update()

        obj = bpy.data.objects.new(mesh_name, mesh_data)
        bpy.context.scene.collection.objects.link(obj)

        return obj

    @staticmethod
    def update_mesh(obj, points, connections=None):
        """Replace the geometry of an existing mesh *obj*.

        Args:
            obj: a ``bpy.types.Object`` of type MESH.
            points, connections: same as ``create_mesh``.
        """
        verts = []
        for p in points:
            if len(p) == 2:
                verts.append(Vector((p[0], p[1], 0.0)))
            else:
                verts.append(Vector((p[0], p[1], p[2])))

        if connections:
            edges = [tuple(c) for c in connections]
        else:
            edges = [(i, i + 1) for i in range(len(verts) - 1)]

        mesh = obj.data
        mesh.clear_geometry()
        mesh.from_pydata(verts, edges, [])
        mesh.update()
