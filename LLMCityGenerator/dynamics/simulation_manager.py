"""Simulation manager — pedestrians + traffic lights via bpy.app.timers.

Car traffic is handled by the City Generator Geo Nodes simulation.
"""

import math
import bpy
from mathutils import Vector
from .pedestrian_system import PedestrianManager
from .traffic_light import TrafficLightManager
from .car_system import CarManager  # for eval_curve / place_on_curve utilities
from ..constants import DYNAMICS_COLLECTION_NAME


class SimulationManager:
    _instance = None

    def __init__(self):
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
              enable_pedestrians=True, enable_traffic_lights=True,
              pedestrian_collection=None):
        from .road_analyzer import RoadAnalyzer

        if scene is None:
            scene = bpy.context.scene

        self.mesh_obj = mesh_obj
        self.road_data = RoadAnalyzer.extract_roads(mesh_obj)
        if not self.road_data:
            return False

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
        self._drive_pedestrians(dt)
        bpy.context.view_layer.update()
        return 1.0 / 30.0

    # ------------------------------------------------------------------
    # Pedestrian movement
    # ------------------------------------------------------------------

    def _drive_pedestrians(self, dt):
        for vdata in self.pedestrian_manager.pedestrians:
            obj = vdata["obj"]
            curve = vdata["curve"]
            speed = vdata["speed"]
            offset = vdata["offset"]
            direction = vdata.get("direction", 1)

            curve_length = obj.get("cg.ped_curve_length", 1.0)
            if curve_length <= 0:
                continue

            # --- traffic light (only near end of path) ---
            edge_id = obj.get("cg.ped_edge_id")
            eff_speed = speed
            if edge_id is not None and edge_id >= 0 and offset > 0.7:
                state = self.traffic_light_manager.get_light_state_at_edge(edge_id)
                if state == "RED":
                    obj["cg.ped_stopped"] = True
                    _place_pedestrian(obj, curve, offset, direction)
                    continue
                elif state == "YELLOW":
                    obj["cg.ped_stopped"] = False
                    eff_speed *= 0.3
                else:
                    obj["cg.ped_stopped"] = False

            delta = (eff_speed * dt) / curve_length
            offset += delta
            offset %= 1.0
            vdata["offset"] = offset
            _place_pedestrian(obj, curve, offset, direction)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self):
        self.active = False
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


# ------------------------------------------------------------------
# Pedestrian-specific curve placement (+Y forward convention)
# ------------------------------------------------------------------

def _place_pedestrian(obj, curve, offset, direction=1):
    """Place a pedestrian on *curve* facing the direction of motion.

    Uses ``yaw - pi/2`` because pedestrian models face +Y (cars face -Y).
    """
    t = offset if direction > 0 else (1.0 - offset)
    pos, tangent = CarManager.eval_curve(curve, t)
    if direction < 0:
        tangent = -tangent
    obj.location = pos
    yaw = math.atan2(tangent.y, tangent.x)
    obj.rotation_euler = (0.0, 0.0, yaw - math.pi / 2)
