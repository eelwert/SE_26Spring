"""Car vehicle system — spawns and animates cars along road curves.

Each car is placed on its road curve at a random offset.  Movement is driven
by SimulationManager which directly sets obj.location / obj.rotation_euler
each frame — Follow Path constraints are NOT used because Blender 5.x does
not reliably re-evaluate constraint properties modified inside a frame handler.
"""

import random
import math
import bpy
from mathutils import Vector
from ..constants import (
    DYNAMICS_COLLECTION_NAME,
    DYNAMICS_CARS_COLLECTION,
    DEFAULT_CAR_DENSITY,
    DEFAULT_CAR_SPEED_MIN,
    DEFAULT_CAR_SPEED_MAX,
    DEFAULT_CAR_FOLLOW_DISTANCE,
)


class CarManager:
    """Manages car spawning on road curves."""

    def __init__(self):
        self.cars = []  # list of {obj, curve, speed, offset, direction}

    # ------------------------------------------------------------------
    # Spawn
    # ------------------------------------------------------------------

    def spawn_cars(self, road_data,
                   car_collection=None,
                   front_wheels_coll=None,
                   back_wheels_coll=None,
                   car_density=None, speed_min=None, speed_max=None):
        scene = bpy.context.scene

        if car_density is None:
            car_density = getattr(scene, "cg_car_density", DEFAULT_CAR_DENSITY)
        if speed_min is None:
            speed_min = getattr(scene, "cg_car_speed_min", DEFAULT_CAR_SPEED_MIN)
        if speed_max is None:
            speed_max = getattr(scene, "cg_car_speed_max", DEFAULT_CAR_SPEED_MAX)

        cars_coll = self._get_or_create_collection(
            DYNAMICS_CARS_COLLECTION, parent_name=DYNAMICS_COLLECTION_NAME
        )

        car_asset_coll = car_collection

        for road in road_data:
            curve = road["curve"]
            length = road["length"]
            is_turn = road.get("is_turn", False)

            # Fewer cars on turn arcs, one direction only (matching the lane)
            if is_turn:
                car_count = max(1, int(length / 10.0))
                car_count = min(car_count, max(1, car_density // 4))
            else:
                car_count = max(1, int(length / (DEFAULT_CAR_FOLLOW_DISTANCE * 2)))
                car_count = min(car_count, car_density)

            for i in range(car_count):
                direction = 1  # curve already points in travel direction
                offset = random.random()
                speed = random.uniform(speed_min, speed_max)

                car_obj = self._make_car_mesh(
                    name=f"Car_{road['edge_index']}_{i}",
                    collection=cars_coll,
                    car_asset_coll=car_asset_coll,
                    front_wheels_coll=front_wheels_coll,
                    back_wheels_coll=back_wheels_coll,
                )

                car_obj["cg.is_car"] = True
                car_obj["cg.car_speed"] = speed
                car_obj["cg.car_direction"] = direction
                car_obj["cg.car_offset"] = offset
                car_obj["cg.car_curve_length"] = length
                car_obj["cg.car_stopped"] = False
                car_obj["cg.car_edge_id"] = road["edge_index"]

                # place at initial offset
                CarManager.place_on_curve(car_obj, curve, offset, direction)

                self.cars.append({
                    "obj": car_obj,
                    "curve": curve,       # direct object reference — no name lookup
                    "speed": speed,
                    "offset": offset,
                    "direction": direction,
                })

        return self.cars

    # ------------------------------------------------------------------
    # Mesh
    # ------------------------------------------------------------------

    def _make_car_mesh(self, name, collection, car_asset_coll,
                       front_wheels_coll=None, back_wheels_coll=None):
        """Create a complete car: body + front wheels + back wheels.

        All parts are linked duplicates (shared mesh data) parented to a
        root Empty so moving the root moves the whole car.
        """
        if car_asset_coll:
            root = bpy.data.objects.new(name, None)
            root.empty_display_type = "CUBE"
            root.empty_display_size = 0.02
            collection.objects.link(root)

            # --- body ---
            body_proto = self._find_mesh_in_collection(car_asset_coll)
            if body_proto is not None:
                body = bpy.data.objects.new(name + "_body", body_proto.data)
                for mat in body_proto.data.materials:
                    if mat.name not in [m.name for m in body.data.materials]:
                        body.data.materials.append(mat)
                body.parent = root
                body.location = (0, 0, 0)
                collection.objects.link(body)

            # --- wheels ---
            for wc, suffix in [(front_wheels_coll, "front"), (back_wheels_coll, "back")]:
                if wc is None:
                    continue
                wheel_proto = self._find_mesh_in_collection(wc)
                if wheel_proto is None:
                    continue
                wheel = bpy.data.objects.new(
                    f"{name}_{suffix}_wheels", wheel_proto.data
                )
                for mat in wheel_proto.data.materials:
                    if mat.name not in [m.name for m in wheel.data.materials]:
                        wheel.data.materials.append(mat)
                wheel.parent = root
                loc = wheel_proto.location.copy()
                loc.z += 0.96  # raise so wheel bottom touches road (Z=0)
                wheel.location = loc
                collection.objects.link(wheel)

            return root
        else:
            mesh = bpy.data.meshes.new(name + "_mesh")
            obj = bpy.data.objects.new(name, mesh)
            verts = [
                (-0.7, -1.6, 0.0), (0.7, -1.6, 0.0), (0.7, 1.6, 0.0), (-0.7, 1.6, 0.0),
                (-0.6, -1.0, 0.55), (0.6, -1.0, 0.55), (0.6, 1.4, 0.55), (-0.6, 1.4, 0.55),
            ]
            faces = [
                (0, 1, 2, 3), (4, 5, 6, 7),
                (0, 4, 7, 3), (1, 5, 4, 0), (2, 6, 5, 1), (3, 7, 6, 2),
            ]
            mesh.from_pydata(verts, [], faces)
            mesh.update()
            mat = bpy.data.materials.new(name + "_mat")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (
                    random.uniform(0.2, 1.0),
                    random.uniform(0.2, 1.0),
                    random.uniform(0.2, 1.0),
                    1.0,
                )
            mesh.materials.append(mat)

        collection.objects.link(obj)
        return obj

    # ------------------------------------------------------------------
    # Curve evaluation
    # ------------------------------------------------------------------

    @staticmethod
    def eval_curve(curve, t):
        """Return (world_pos: Vector, world_tangent: Vector) at t in [0, 1]."""
        t = t % 1.0
        spline = curve.data.splines[0]
        bp = spline.bezier_points
        if len(bp) < 2:
            return Vector((0, 0, 0)), Vector((1, 0, 0))

        p0, h0 = bp[0].co, bp[0].handle_right
        h1, p3 = bp[1].handle_left, bp[1].co

        u = 1.0 - t
        u2, u3 = u * u, u * u * u
        t2, t3 = t * t, t * t * t

        pos = u3 * p0 + 3 * u2 * t * h0 + 3 * u * t2 * h1 + t3 * p3
        tangent = 3 * u2 * (h0 - p0) + 6 * u * t * (h1 - h0) + 3 * t2 * (p3 - h1)

        if tangent.length < 1e-6:
            tangent = p3 - p0
        tangent.normalize()

        mat = curve.matrix_world
        return mat @ pos, mat.to_3x3() @ tangent

    @staticmethod
    def place_on_curve(obj, curve, offset, direction=1):
        """Set obj.location / obj.rotation_euler to *offset* on *curve*.

        Object faces its motion direction.  When *direction* is -1 the curve
        parameter is ``1 - offset`` (travels end→start) and the tangent is
        reversed so the model faces the way it is actually moving.
        """
        t = offset if direction > 0 else (1.0 - offset)
        pos, tangent = CarManager.eval_curve(curve, t)
        if direction < 0:
            tangent = -tangent
        obj.location = pos
        yaw = math.atan2(tangent.y, tangent.x)
        obj.rotation_euler = (0.0, 0.0, yaw + math.pi / 2)

    @staticmethod
    def _find_mesh_in_collection(coll):
        """Return the first MESH object found in *coll* (recursive)."""
        for obj in coll.all_objects:
            if obj.type == "MESH":
                return obj
        return None

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

    def cleanup_cars(self):
        cars_coll = bpy.data.collections.get(DYNAMICS_CARS_COLLECTION)
        if cars_coll:
            for obj in list(cars_coll.objects):
                data = obj.data
                bpy.data.objects.remove(obj)
                if data and hasattr(data, "users") and data.users == 0:
                    if isinstance(data, bpy.types.Mesh):
                        bpy.data.meshes.remove(data)
            bpy.data.collections.remove(cars_coll)
        self.cars.clear()
