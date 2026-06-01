"""Point solver — converts coordinate point sets into road-defining meshes.

Every City Generator road is a mesh edge.  This module creates (or updates)
a mesh whose vertices = intersections and edges = road segments.
"""

import bpy
from mathutils import Vector


class PointSolver:
    """Build a road-layout mesh from a list of coordinates."""

    @staticmethod
    def _find_faces(edges):
        """Find quad faces from edge list by detecting 4-cycles."""
        # Build adjacency
        adj = {}
        for a, b in edges:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)

        faces = []
        # For every ordered pair (a,c) sharing a common neighbor b, check if
        # a→b→c→d→a forms a quad
        for a in adj:
            for b in adj[a]:
                for c in adj[b]:
                    if c == a or c == b:
                        continue
                    for d in adj[c]:
                        if d == a or d == b or d == c:
                            continue
                        if a in adj[d] and b not in adj.get(c, set()) and c not in adj.get(a, set()):
                            # Found quad a-b-c-d → check it's minimal (no diagonal)
                            if b not in adj.get(d, set()) or c not in adj.get(a, set()):
                                face = tuple(sorted([a, b, c, d]))
                                if face not in faces:
                                    # Order vertices for correct winding
                                    # a-b-c-d should go around the face
                                    ordered = (a, b, c, d)
                                    faces.append(ordered)
        return faces

    @staticmethod
    def create_mesh(points, connections=None, mesh_name="RoadLayout",
                    generate_faces=False, faces=None):
        """Create a new mesh object from 2-D coordinate points.

        Args:
            points: list of ``(x, y)`` or ``(x, y, z)`` iterables.
            connections: optional list of ``(i, j)`` index pairs.
            mesh_name: name for the created object & mesh data.
            generate_faces: auto-detect quad faces from edge loops.
            faces: explicit face list ``[(a,b,c,d), ...]``. Overrides auto-detect.

        Returns:
            The newly-created ``bpy.types.Object`` (type=MESH).
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

        if faces:
            face_list = [tuple(f) for f in faces]
        elif generate_faces:
            face_list = PointSolver._find_faces(edges)
        else:
            face_list = []

        mesh_data = bpy.data.meshes.new(mesh_name)
        mesh_data.from_pydata(verts, edges, face_list)
        mesh_data.update()

        obj = bpy.data.objects.new(mesh_name, mesh_data)
        bpy.context.scene.collection.objects.link(obj)

        return obj

    @staticmethod
    def update_mesh(obj, points, connections=None, generate_faces=False,
                    faces=None):
        """Replace the geometry of an existing mesh *obj*."""
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

        if faces:
            face_list = [tuple(f) for f in faces]
        elif generate_faces:
            face_list = PointSolver._find_faces(edges)
        else:
            face_list = []

        mesh = obj.data
        mesh.clear_geometry()
        mesh.from_pydata(verts, edges, face_list)
        mesh.update()
