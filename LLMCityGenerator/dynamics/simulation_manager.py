"""Simulation manager — drives cars and pedestrians via bpy.app.timers.

Blender 5.x frame_change_pre handlers cannot reliably update object transforms
in a way the viewport will render.  Instead we use a persistent app timer that
runs at ~30 Hz, advances every vehicle along its curve, keyframes the new
location/rotation, and tags the 3D View for redraw.
"""

import bpy
from .car_system import CarManager
from .pedestrian_system import PedestrianManager
from .traffic_light import TrafficLightManager
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
        self._elapsed = 0.0          # accumulated simulation time
        self._last_tick = -1.0       # for frame-independent timing

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
    # Setup / teardown
    # ------------------------------------------------------------------

    def setup(self, mesh_obj, scene=None,
              enable_cars=True, enable_pedestrians=True,
              enable_traffic_lights=True,
              car_collection=None, front_wheels_coll=None,
              back_wheels_coll=None, pedestrian_collection=None):
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

        self._elapsed = 0.0
        self._last_tick = -1.0
        self.active = True
        scene.cg_dynamics_active = True

        bpy.app.timers.register(self._on_timer, first_interval=0.05)
        return True

    def cleanup(self):
        self.active = False  # timer will see this and return None → auto-unregister

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

    # ------------------------------------------------------------------
    # Timer callback — called ~30 × / second
    # ------------------------------------------------------------------

    def _on_timer(self):
        """App timer: drive simulation forward and keyframe positions."""
        if not self.active:
            return None  # stop timer

        scene = bpy.context.scene
        fps = max(scene.render.fps, 24)

        now = scene.frame_current / fps

        if self._last_tick < 0:
            self._last_tick = now
            return 1.0 / 30.0

        dt = now - self._last_tick
        self._last_tick = now

        # Clamp dt to avoid huge jumps after pause / frame scrub
        if dt <= 0 or dt > 0.5:
            return 1.0 / 30.0

        frame = scene.frame_current

        # --- traffic lights ---
        self.traffic_light_manager.update_cycle(scene)

        # --- cars ---
        self._drive_vehicles(
            vehicles=self.car_manager.cars,
            dt=dt,
            traffic_manager=self.traffic_light_manager,
            stopped_key="cg.car_stopped",
            edge_key="cg.car_edge_id",
            frame=frame,
        )

        # --- pedestrians ---
        self._drive_vehicles(
            vehicles=self.pedestrian_manager.pedestrians,
            dt=dt,
            traffic_manager=self.traffic_light_manager,
            stopped_key="cg.ped_stopped",
            edge_key="cg.ped_edge_id",
            frame=frame,
        )

        # Force depsgraph re-evaluation so viewport shows new positions
        bpy.context.view_layer.update()

        return 1.0 / 30.0

    # ------------------------------------------------------------------
    # Per-vehicle advance
    # ------------------------------------------------------------------

    def _drive_vehicles(self, vehicles, dt, traffic_manager, stopped_key, edge_key, frame):
        for vdata in vehicles:
            obj = vdata["obj"]
            curve = vdata["curve"]
            speed = vdata["speed"]
            direction = vdata.get("direction", 1)
            offset = vdata["offset"]

            curve_length = obj.get(
                "cg.car_curve_length",
                obj.get("cg.ped_curve_length", 1.0),
            )
            if curve_length <= 0:
                continue

            # --- traffic light ---
            edge_id = obj.get(edge_key)
            eff_speed = speed
            if edge_id is not None:
                state = traffic_manager.get_light_state_at_edge(edge_id)
                if state == "RED":
                    obj[stopped_key] = True
                    # keep current position but still keyframe (so it stays put)
                    CarManager.place_on_curve(obj, curve, offset, direction)
                    continue
                elif state == "YELLOW":
                    obj[stopped_key] = False
                    eff_speed *= 0.3
                else:
                    obj[stopped_key] = False

            # --- advance offset ---
            delta = (eff_speed * dt) / curve_length
            offset += direction * delta
            offset %= 1.0
            vdata["offset"] = offset

            # Place object at new position
            CarManager.place_on_curve(obj, curve, offset, direction)


