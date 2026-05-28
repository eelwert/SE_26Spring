"""Simulation manager — coordinates cars, pedestrians and traffic lights via bpy.app.timers.

All three systems are Python-driven.  No Geo Nodes dependency for animation.
"""

import bpy
from .pedestrian_system import PedestrianManager
from .traffic_light import TrafficLightManager
from .car_system import CarManager
from ..constants import DYNAMICS_COLLECTION_NAME


class SimulationManager:
    _instance = None

    def __init__(self):
        self.car_manager = CarManager()
        self.pedestrian_manager = PedestrianManager()
        self.traffic_light_manager = TrafficLightManager()
        self.road_data = []
        self.active = False
        self.mesh_obj = None
        self._last_tick = -1.0

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        if cls._instance is not None:
            cls._instance.cleanup()
            cls._instance = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self, mesh_obj, scene=None,
              enable_cars=True, enable_pedestrians=True, enable_traffic_lights=True,
              pedestrian_collection=None,
              car_collection=None, front_wheels_coll=None, back_wheels_coll=None):
        from .road_analyzer import RoadAnalyzer

        if scene is None:
            scene = bpy.context.scene

        self.mesh_obj = mesh_obj
        self.road_data = RoadAnalyzer.extract_roads(mesh_obj)
        if not self.road_data:
            return False

        if enable_cars:
            self.car_manager.spawn_cars(
                road_data=self.road_data,
                car_collection=car_collection,
                front_wheels_coll=front_wheels_coll,
                back_wheels_coll=back_wheels_coll,
                car_density=scene.cg_car_density,
                speed_min=scene.cg_car_speed_min,
                speed_max=scene.cg_car_speed_max,
            )
        if enable_pedestrians:
            self.pedestrian_manager.spawn_pedestrians(
                road_data=self.road_data,
                pedestrian_collection=pedestrian_collection,
                density=scene.cg_pedestrian_density,
                speed=scene.cg_pedestrian_speed,
            )
        if enable_traffic_lights:
            self.traffic_light_manager.place_lights(
                road_data=self.road_data,
                mesh_obj=mesh_obj,
                green=scene.cg_traffic_light_green,
                yellow=scene.cg_traffic_light_yellow,
                red=scene.cg_traffic_light_red,
            )

        self._last_tick = -1.0
        self.active = True
        scene.cg_dynamics_active = True
        bpy.app.timers.register(self._on_timer, first_interval=0.05)
        return True

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------

    def _on_timer(self):
        if not self.active:
            return None

        scene = bpy.context.scene
        fps = max(scene.render.fps, 24)
        now = scene.frame_current / fps

        if self._last_tick < 0:
            self._last_tick = now
            return 1.0 / 30.0

        dt = now - self._last_tick
        self._last_tick = now
        if dt <= 0 or dt > 0.5:
            return 1.0 / 30.0

        self.traffic_light_manager.update_cycle(scene)

        # Drive cars
        self._drive_vehicles(
            vehicles=self.car_manager.cars,
            dt=dt,
            traffic_manager=self.traffic_light_manager,
            stopped_key="cg.car_stopped",
            edge_key="cg.car_edge_id",
            curve_length_key="cg.car_curve_length",
        )

        # Drive pedestrians
        self._drive_vehicles(
            vehicles=self.pedestrian_manager.pedestrians,
            dt=dt,
            traffic_manager=self.traffic_light_manager,
            stopped_key="cg.ped_stopped",
            edge_key="cg.ped_edge_id",
            curve_length_key="cg.ped_curve_length",
        )

        bpy.context.view_layer.update()
        return 1.0 / 30.0

    # ------------------------------------------------------------------
    # Shared advance logic
    # ------------------------------------------------------------------

    def _drive_vehicles(self, vehicles, dt, traffic_manager, stopped_key, edge_key,
                        curve_length_key="cg.ped_curve_length"):
        is_pedestrian = (curve_length_key == "cg.ped_curve_length")
        for vdata in vehicles:
            obj = vdata["obj"]
            curve = vdata["curve"]
            speed = vdata["speed"]
            offset = vdata["offset"]
            direction = vdata.get("direction", 1)

            curve_length = obj.get(curve_length_key, 1.0)
            if curve_length <= 0:
                continue

            # --- traffic light (only near end of path) ---
            edge_id = obj.get(edge_key)
            eff_speed = speed
            if edge_id is not None and edge_id >= 0 and offset > 0.7:
                state = traffic_manager.get_light_state_at_edge(edge_id)
                if state == "RED":
                    obj[stopped_key] = True
                    if is_pedestrian:
                        _place_pedestrian(obj, curve, offset, direction)
                    else:
                        CarManager.place_on_curve(obj, curve, offset, direction)
                    continue
                elif state == "YELLOW":
                    obj[stopped_key] = False
                    eff_speed *= 0.3
                else:
                    obj[stopped_key] = False

            delta = (eff_speed * dt) / curve_length
            offset += delta
            offset %= 1.0
            vdata["offset"] = offset

            if is_pedestrian:
                _place_pedestrian(obj, curve, offset, direction)
            else:
                CarManager.place_on_curve(obj, curve, offset, direction)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

import math as _math
from mathutils import Vector as _Vector

def _place_pedestrian(obj, curve, offset, direction=1):
    """Place a pedestrian on *curve* — same logic as CarManager.place_on_curve
    but uses the opposite local-forward convention (+Y instead of -Y).
    """
    t = offset if direction > 0 else (1.0 - offset)
    pos, tangent = CarManager.eval_curve(curve, t)
    if direction < 0:
        tangent = -tangent
    obj.location = pos
    yaw = _math.atan2(tangent.y, tangent.x)
    # +Y faces motion direction (car convention is -Y)
    obj.rotation_euler = (0.0, 0.0, yaw - _math.pi / 2)

    def cleanup(self):
        self.active = False

        self.car_manager.cleanup_cars()
        self.pedestrian_manager.cleanup_pedestrians()
        self.traffic_light_manager.cleanup_lights()

        from .road_analyzer import RoadAnalyzer
        RoadAnalyzer.cleanup_road_curves()

        root_coll = bpy.data.collections.get(DYNAMICS_COLLECTION_NAME)
        if root_coll:
            bpy.data.collections.remove(root_coll)

        self.road_data = []
        self.mesh_obj = None

        scene = bpy.context.scene
        if hasattr(scene, "cg_dynamics_active"):
            scene.cg_dynamics_active = False
