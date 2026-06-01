"""Road curve extraction from the City Generator base mesh.

Creates **two one-way lane curves** per mesh edge (forward / backward)
so bidirectional traffic never shares a centreline.

At intersection vertices short Bezier **turn arcs** are added so cars
can transition between connected edges with natural curvature.
"""

import math
import bpy
from mathutils import Vector
from collections import defaultdict
from ..constants import (
    DYNAMICS_ROAD_PATHS_COLLECTION,
    DYNAMICS_COLLECTION_NAME,
    DEFAULT_MIN_EDGE_LENGTH,
)

LANE_HALF_WIDTH = 2.0      # metres from centreline to lane centre
TURN_RADIUS = 3.0          # arc radius at intersections


class RoadAnalyzer:
    """Extracts one-way lane curves + turn arcs from a road-defining mesh."""

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

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    def extract_roads(mesh_obj, min_edge_length=None):
        if min_edge_length is None:
            min_edge_length = DEFAULT_MIN_EDGE_LENGTH

        mesh = mesh_obj.data
        if not mesh.edges:
            return []

        matrix = mesh_obj.matrix_world
        vertices = mesh.vertices
        edges = mesh.edges

        RoadAnalyzer._get_or_create_collection(DYNAMICS_COLLECTION_NAME)
        paths_coll = RoadAnalyzer._get_or_create_collection(
            DYNAMICS_ROAD_PATHS_COLLECTION,
            parent_name=DYNAMICS_COLLECTION_NAME,
        )

        road_data = []
        vert_to_edges = defaultdict(list)  # vertex index → list of edge dicts

        # ---- 1. Create two one-way lane curves per edge ----
        for edge_idx, edge in enumerate(edges):
            v0 = matrix @ vertices[edge.vertices[0]].co
            v1 = matrix @ vertices[edge.vertices[1]].co
            length = (v1 - v0).length
            if length < min_edge_length:
                continue

            direc = (v1 - v0).normalized()
            perp = Vector((-direc.y, direc.x, 0.0))

            # --- forward lane  (v0 → v1, right side) ---
            f0, f1 = v0 + perp * LANE_HALF_WIDTH, v1 + perp * LANE_HALF_WIDTH
            fwd_curve = RoadAnalyzer._make_curve(
                f"Lane_{edge_idx}_F", f0, f1, paths_coll, length)
            fwd_entry = {
                "curve": fwd_curve, "edge_index": edge_idx,
                "length": length, "start": v0, "end": v1,
                "direction": 1,
            }
            road_data.append(fwd_entry)
            vert_to_edges[edge.vertices[0]].append(fwd_entry)  # exit at v0?
            vert_to_edges[edge.vertices[1]].append(fwd_entry)

            # --- backward lane (v1 → v0, left side) ---
            b0, b1 = v1 - perp * LANE_HALF_WIDTH, v0 - perp * LANE_HALF_WIDTH
            bwd_curve = RoadAnalyzer._make_curve(
                f"Lane_{edge_idx}_B", b0, b1, paths_coll, length)
            bwd_entry = {
                "curve": bwd_curve, "edge_index": edge_idx,
                "length": length, "start": v1, "end": v0,
                "direction": -1,
            }
            road_data.append(bwd_entry)
            vert_to_edges[edge.vertices[1]].append(bwd_entry)
            vert_to_edges[edge.vertices[0]].append(bwd_entry)

        # ---- 2. Turn arcs at intersection vertices ----
        turn_count = 0
        for v_idx, lane_list in vert_to_edges.items():
            pos = matrix @ vertices[v_idx].co
            # Group lanes by which edge they belong to
            by_edge = defaultdict(list)
            for ld in lane_list:
                by_edge[ld["edge_index"]].append(ld)

            unique_edges = list(by_edge.keys())
            if len(unique_edges) < 2:
                continue

            # For every ordered pair of different edges, create a turn arc
            for ea in unique_edges:
                for eb in unique_edges:
                    if ea == eb:
                        continue
                    # Get lanes: incoming (ending at this vertex) and outgoing (starting)
                    incoming = [ld for ld in by_edge[ea] if _ends_at(ld, pos)]
                    outgoing = [ld for ld in by_edge[eb] if _starts_at(ld, pos)]
                    for ld_in in incoming:
                        for ld_out in outgoing:
                            # Skip if lanes are on the same straight line (no turn needed)
                            if _is_straight_through(ld_in, ld_out):
                                continue
                            arc = RoadAnalyzer._make_turn_arc(
                                f"Turn_{turn_count}", ld_in, ld_out, pos, paths_coll)
                            road_data.append({
                                "curve": arc,
                                "edge_index": -1,
                                "length": arc["cg.road_length"],
                                "start": ld_in["end"],
                                "end": ld_out["start"],
                                "direction": 1,
                                "is_turn": True,
                            })
                            turn_count += 1

        return road_data

    # ------------------------------------------------------------------
    # Curve builders
    # ------------------------------------------------------------------

    @staticmethod
    def _make_curve(name, p0, p1, collection, length):
        """Create a straight-line Bezier curve from *p0* to *p1*."""
        cd = bpy.data.curves.new(name, type="CURVE")
        cd.dimensions = "3D"
        cd.resolution_u = 4
        spline = cd.splines.new(type="BEZIER")
        spline.bezier_points.add(1)

        third = (p1 - p0) / 3.0
        for bp, pt in zip(spline.bezier_points, [p0, p1]):
            bp.co = pt
            bp.handle_left = pt - third
            bp.handle_right = pt + third
            bp.handle_left_type = bp.handle_right_type = "FREE"

        obj = bpy.data.objects.new(name, cd)
        obj["cg.is_road_path"] = True
        obj["cg.road_length"] = length
        collection.objects.link(obj)
        return obj

    @staticmethod
    def _make_turn_arc(name, lane_in, lane_out, vertex_pos, collection):
        """Build a 90°-ish Bezier arc from *lane_in* end to *lane_out* start.

        The arc curves around *vertex_pos* using a control point offset
        diagonally from the vertex so the car path stays natural.
        """
        p0 = lane_in["end"]
        p3 = lane_out["start"]

        # Compute tangent directions
        t_in = (p0 - vertex_pos)
        if t_in.length > 1e-6:
            t_in.normalize()
        else:
            t_in = Vector((1, 0, 0))
        t_out = (p3 - vertex_pos)
        if t_out.length > 1e-6:
            t_out.normalize()
        else:
            t_out = Vector((0, 1, 0))

        # Control-point offset is a blend of the two tangents, scaled by radius
        cp_offset = (t_in + t_out)
        if cp_offset.length > 1e-6:
            cp_offset.normalize()
        cp = vertex_pos + cp_offset * TURN_RADIUS

        cd = bpy.data.curves.new(name, type="CURVE")
        cd.dimensions = "3D"
        cd.resolution_u = 6
        spline = cd.splines.new(type="BEZIER")
        spline.bezier_points.add(1)

        bp0 = spline.bezier_points[0]
        bp0.co = p0
        bp0.handle_right = cp
        bp0.handle_left_type = bp0.handle_right_type = "FREE"

        bp1 = spline.bezier_points[1]
        bp1.co = p3
        bp1.handle_left = cp
        bp1.handle_left_type = bp1.handle_right_type = "FREE"

        length = (p3 - p0).length
        obj = bpy.data.objects.new(name, cd)
        obj["cg.is_road_path"] = True
        obj["cg.is_turn"] = True
        obj["cg.road_length"] = max(length, 0.5)
        collection.objects.link(obj)
        return obj

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    @staticmethod
    def cleanup_road_curves():
        paths_coll = bpy.data.collections.get(DYNAMICS_ROAD_PATHS_COLLECTION)
        if paths_coll:
            for obj in list(paths_coll.objects):
                data = obj.data
                bpy.data.objects.remove(obj)
                if data and data.users == 0:
                    bpy.data.curves.remove(data)
            bpy.data.collections.remove(paths_coll)


def _is_straight_through(ld_in, ld_out):
    """True if incoming and outgoing lanes are roughly collinear (straight-through)."""
    d_in = (ld_in["end"] - ld_in["start"])
    d_out = (ld_out["end"] - ld_out["start"])
    if d_in.length < 1e-3 or d_out.length < 1e-3:
        return True  # degenerate, skip
    d_in.normalize()
    d_out.normalize()
    dot = abs(d_in.dot(d_out))
    return dot > 0.85  # within ~30° of parallel


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _ends_at(ld, pos):
    """True if the lane dict *ld* 's end is close to *pos*."""
    return (ld["end"] - pos).length < 1e-3


def _starts_at(ld, pos):
    """True if the lane dict *ld* 's start is close to *pos*."""
    return (ld["start"] - pos).length < 1e-3
