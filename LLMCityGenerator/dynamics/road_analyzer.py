"""Road curve extraction from the City Generator base mesh.

Reads the mesh edges (which define the road network) and converts each
edge into a Bezier curve object for use by the dynamic simulation systems.
"""

import bpy
from mathutils import Vector
from ..constants import (
    DYNAMICS_ROAD_PATHS_COLLECTION,
    DYNAMICS_COLLECTION_NAME,
    DEFAULT_MIN_EDGE_LENGTH,
)


class RoadAnalyzer:
    """Extracts road curves from a base mesh whose edges represent roads."""

    @staticmethod
    def _get_or_create_collection(name, parent_name=None):
        coll = bpy.data.collections.get(name)
        if coll is None:
            coll = bpy.data.collections.new(name)
            if parent_name:
                parent = bpy.data.collections.get(parent_name)
                if parent:
                    parent.children.link(coll)
                else:
                    bpy.context.scene.collection.children.link(coll)
            else:
                bpy.context.scene.collection.children.link(coll)
        return coll

    @staticmethod
    def extract_roads(mesh_obj, min_edge_length=None):
        """Convert each qualifying mesh edge into a Bezier curve object."""
        if min_edge_length is None:
            min_edge_length = DEFAULT_MIN_EDGE_LENGTH

        mesh = mesh_obj.data
        if not mesh.edges:
            return []

        matrix = mesh_obj.matrix_world
        edges = mesh.edges
        vertices = mesh.vertices

        paths_coll = RoadAnalyzer._get_or_create_collection(
            DYNAMICS_ROAD_PATHS_COLLECTION,
            parent_name=DYNAMICS_COLLECTION_NAME,
        )

        road_data = []

        for edge_idx, edge in enumerate(edges):
            v0 = matrix @ vertices[edge.vertices[0]].co
            v1 = matrix @ vertices[edge.vertices[1]].co
            length = (v1 - v0).length

            if length < min_edge_length:
                continue

            curve_data = bpy.data.curves.new(
                name=f"RoadPath_{edge_idx}", type="CURVE"
            )
            curve_data.dimensions = "3D"
            curve_data.resolution_u = 2

            spline = curve_data.splines.new(type="BEZIER")
            spline.bezier_points.add(1)

            # ---- Explicit handles (NOT AUTO) so Bezier evaluation works
            #      immediately without waiting for depsgraph computation ----
            third = (v1 - v0) / 3.0

            bp0 = spline.bezier_points[0]
            bp0.co = v0
            bp0.handle_left = v0 - third
            bp0.handle_right = v0 + third
            bp0.handle_left_type = "FREE"
            bp0.handle_right_type = "FREE"

            bp1 = spline.bezier_points[1]
            bp1.co = v1
            bp1.handle_left = v1 - third
            bp1.handle_right = v1 + third
            bp1.handle_left_type = "FREE"
            bp1.handle_right_type = "FREE"

            curve_obj = bpy.data.objects.new(
                name=f"RoadPath_{edge_idx}", object_data=curve_data
            )
            curve_obj["cg.is_road_path"] = True
            curve_obj["cg.edge_index"] = edge_idx
            curve_obj["cg.road_length"] = length

            paths_coll.objects.link(curve_obj)

            road_data.append({
                "curve": curve_obj,
                "edge_index": edge_idx,
                "length": length,
                "start": v0,
                "end": v1,
            })

        return road_data

    @staticmethod
    def cleanup_road_curves():
        """Remove all road curve objects and their collection."""
        paths_coll = bpy.data.collections.get(DYNAMICS_ROAD_PATHS_COLLECTION)
        if paths_coll:
            for obj in list(paths_coll.objects):
                curve = obj.data
                bpy.data.objects.remove(obj)
                if curve and curve.users == 0:
                    bpy.data.curves.remove(curve)
            bpy.data.collections.remove(paths_coll)
