"""Pedestrian system — spawns pedestrians along sidewalk paths.

Sidewalk curves are offset copies of road curves.  Pedestrians are coloured
cylinders placed directly on those curves and moved each frame by
SimulationManager via direct location assignment.
"""

import math
import random
import bpy
from mathutils import Vector
from ..constants import (
    DYNAMICS_COLLECTION_NAME,
    DYNAMICS_SIDEWALK_PATHS_COLLECTION,
    DYNAMICS_PEDESTRIANS_COLLECTION,
    DEFAULT_PEDESTRIAN_DENSITY,
    DEFAULT_PEDESTRIAN_SPEED,
    DEFAULT_SIDEWALK_OFFSET,
)
from .car_system import CarManager  # for place_on_curve


class PedestrianManager:
    """Manages pedestrian spawning on sidewalk paths."""

    def __init__(self):
        self.pedestrians = []
        self.sidewalk_curves = []

    def spawn_pedestrians(self, road_data, pedestrian_collection=None,
                          density=None, speed=None, sidewalk_offset=None):
        scene = bpy.context.scene

        if density is None:
            density = getattr(scene, "cg_pedestrian_density", DEFAULT_PEDESTRIAN_DENSITY)
        if speed is None:
            speed = getattr(scene, "cg_pedestrian_speed", DEFAULT_PEDESTRIAN_SPEED)
        if sidewalk_offset is None:
            sidewalk_offset = DEFAULT_SIDEWALK_OFFSET

        sidewalk_coll = self._get_or_create_collection(
            DYNAMICS_SIDEWALK_PATHS_COLLECTION, parent_name=DYNAMICS_COLLECTION_NAME)
        peds_coll = self._get_or_create_collection(
            DYNAMICS_PEDESTRIANS_COLLECTION, parent_name=DYNAMICS_COLLECTION_NAME)

        for road in road_data:
            curve = road["curve"]
            length = road["length"]
            start = road["start"]
            end = road["end"]

            direction = (end - start).normalized()
            perp_left = Vector((-direction.y, direction.x, 0))
            perp_right = Vector((direction.y, -direction.x, 0))

            for side_label, perp in [("L", perp_left), ("R", perp_right)]:
                sw_curve = self._make_sidewalk_curve(
                    name=f"{curve.name}_SW_{side_label}",
                    start=start, end=end, perp=perp,
                    offset=sidewalk_offset,
                    collection=sidewalk_coll,
                )
                self.sidewalk_curves.append(sw_curve)

                ped_count = max(1, int(length / 5.0))
                ped_count = min(ped_count, density)

                for i in range(ped_count):
                    walk_dir = -1
                    offset = random.random()
                    walk_speed = random.uniform(speed * 0.7, speed * 1.3)

                    ped_obj = self._make_ped_mesh(
                        name=f"Ped_{road['edge_index']}_{side_label}_{i}",
                        collection=peds_coll,
                        ped_asset_coll=pedestrian_collection,
                    )

                    ped_obj["cg.is_pedestrian"] = True
                    ped_obj["cg.ped_speed"] = walk_speed
                    ped_obj["cg.ped_direction"] = walk_dir
                    ped_obj["cg.ped_offset"] = offset
                    ped_obj["cg.ped_curve_length"] = sw_curve["cg.road_length"]
                    ped_obj["cg.ped_stopped"] = False
                    ped_obj["cg.ped_edge_id"] = road["edge_index"]

                    CarManager.place_on_curve(ped_obj, sw_curve, offset, walk_dir)

                    self.pedestrians.append({
                        "obj": ped_obj,
                        "curve": sw_curve,   # direct reference
                        "speed": walk_speed,
                        "offset": offset,
                        "direction": walk_dir,
                    })

        return self.pedestrians

    # ------------------------------------------------------------------
    # Sidewalk curve
    # ------------------------------------------------------------------

    def _make_sidewalk_curve(self, name, start, end, perp, offset, collection):
        sd_data = bpy.data.curves.new(name=name, type="CURVE")
        sd_data.dimensions = "3D"
        sd_data.resolution_u = 2

        spline = sd_data.splines.new(type="BEZIER")
        spline.bezier_points.add(1)

        s0 = start + perp * offset
        s1 = end + perp * offset
        third = (s1 - s0) / 3.0

        bp0 = spline.bezier_points[0]
        bp0.co = s0
        bp0.handle_left = s0 - third
        bp0.handle_right = s0 + third
        bp0.handle_left_type = bp0.handle_right_type = "FREE"

        bp1 = spline.bezier_points[1]
        bp1.co = s1
        bp1.handle_left = s1 - third
        bp1.handle_right = s1 + third
        bp1.handle_left_type = bp1.handle_right_type = "FREE"

        sd_obj = bpy.data.objects.new(name=name, object_data=sd_data)
        sd_obj["cg.is_sidewalk_path"] = True
        sd_obj["cg.road_length"] = (end - start).length
        collection.objects.link(sd_obj)
        return sd_obj

    # ------------------------------------------------------------------
    # Pedestrian mesh (no bpy.ops — avoids context pollution)
    # ------------------------------------------------------------------

    def _make_ped_mesh(self, name, collection, ped_asset_coll=None):
        """Create a pedestrian — linked duplicate of a random character mesh, or cylinder fallback."""
        if ped_asset_coll is not None:
            # ped_asset_coll may be:
            #   a) a collection whose (recursive) objects include character meshes
            #   b) a list of sub-collections → randomly pick one and instance it
            if isinstance(ped_asset_coll, list):
                char_coll = random.choice(ped_asset_coll)
                obj = bpy.data.objects.new(name, None)
                obj.instance_type = "COLLECTION"
                obj.instance_collection = char_coll
                obj.empty_display_size = 0.5
                collection.objects.link(obj)
                return obj

            # Collection with mesh objects → pick a random mesh, create linked duplicate
            _EXCLUDE = {
                "DFS_Man_01", "DFS_Man_02", "DFS_Man_03", "DFS_Man_04",
                "DFS_Man_05", "DFS_Man_06",
                "DFS_Woman_01_01", "DFS_Woman_01_02",
                "DFS_Woman_02_01", "DFS_Woman_02_02", "DFS_Woman_02_3",
                "DFS_Woman_03_01", "DFS_Woman_03_02",
                "DFS_Woman_04_01", "DFS_Woman_04_02",
                "DFS_Woman_05_01", "DFS_Woman_05_02",
            }
            mesh_objs = [
                o for o in ped_asset_coll.all_objects
                if o.type == "MESH" and o.name not in _EXCLUDE
            ]
            if mesh_objs:
                proto = random.choice(mesh_objs)
                obj = bpy.data.objects.new(name, proto.data)
                # Copy materials from prototype
                for mat in proto.data.materials:
                    if mat and mat.name not in [m.name for m in obj.data.materials]:
                        obj.data.materials.append(mat)
                obj.location = (0, 0, 0)
                collection.objects.link(obj)
                return obj

        # Fallback: procedural cylinder
        mesh = bpy.data.meshes.new(name + "_mesh")
        verts, faces = [], []
        segs = 8
        r, h = 0.25, 1.7
        for i in range(segs):
            angle = 2 * math.pi * i / segs
            verts.append((r * math.cos(angle), r * math.sin(angle), 0.0))
        for i in range(segs):
            angle = 2 * math.pi * i / segs
            verts.append((r * math.cos(angle), r * math.sin(angle), h))
        for i in range(segs):
            nxt = (i + 1) % segs
            faces.append((i, nxt, nxt + segs, i + segs))
        faces.append(tuple(range(segs - 1, -1, -1)))
        faces.append(tuple(range(segs, 2 * segs)))

        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)

        mat = bpy.data.materials.new(name + "_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (
                random.uniform(0.2, 0.9),
                random.uniform(0.2, 0.9),
                random.uniform(0.2, 0.9),
                1.0,
            )
        mesh.materials.append(mat)
        return obj

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

    def cleanup_pedestrians(self):
        for coll_name in [DYNAMICS_PEDESTRIANS_COLLECTION, DYNAMICS_SIDEWALK_PATHS_COLLECTION]:
            coll = bpy.data.collections.get(coll_name)
            if coll:
                for obj in list(coll.objects):
                    data = obj.data
                    bpy.data.objects.remove(obj)
                    if data and hasattr(data, "users") and data.users == 0:
                        if isinstance(data, bpy.types.Curve):
                            bpy.data.curves.remove(data)
                        elif isinstance(data, bpy.types.Mesh):
                            bpy.data.meshes.remove(data)
                bpy.data.collections.remove(coll)
        self.pedestrians.clear()
        self.sidewalk_curves.clear()
