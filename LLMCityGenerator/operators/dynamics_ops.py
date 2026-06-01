"""Operators for adding and removing dynamic simulation elements."""

import bpy
from ..dynamics.simulation_manager import SimulationManager
from ..dynamics.function_api import run_full_simulation, stop_simulation


class CG_OT_AddDynamicElements(bpy.types.Operator):
    """Generate road curves from the active mesh and spawn dynamic elements."""

    bl_idname = "cg.add_dynamic_elements"
    bl_label = "Add Dynamic Elements"
    bl_description = "Extract road curves, spawn cars, pedestrians, and traffic lights"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.mode == "OBJECT"
            and context.active_object
            and context.active_object.type == "MESH"
        )

    def execute(self, context):
        # Use the function API so model resolution happens automatically
        result = run_full_simulation(
            mesh_obj=context.active_object,
            params={
                "car_density": context.scene.cg_car_density,
                "speed_min": context.scene.cg_car_speed_min,
                "speed_max": context.scene.cg_car_speed_max,
                "pedestrian_density": context.scene.cg_pedestrian_density,
                "walking_speed": context.scene.cg_pedestrian_speed,
                "green_duration": context.scene.cg_traffic_light_green,
                "yellow_duration": context.scene.cg_traffic_light_yellow,
                "red_duration": context.scene.cg_traffic_light_red,
            },
        )
        if result["success"]:
            self.report({"INFO"}, result["message"])
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, result["message"])
            return {"CANCELLED"}


class CG_OT_RemoveDynamicElements(bpy.types.Operator):
    """Remove all dynamic simulation objects and stop the simulation."""

    bl_idname = "cg.remove_dynamic_elements"
    bl_label = "Remove Dynamic Elements"
    bl_description = "Remove all cars, pedestrians, traffic lights, and road curves"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        result = stop_simulation()
        if result["success"]:
            self.report({"INFO"}, result["message"])
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, result["message"])
            return {"CANCELLED"}
