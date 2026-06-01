"""UI panel for the dynamic simulation system."""

import bpy
from ..dynamics.simulation_manager import SimulationManager


class CG_PT_Dynamics_Panel(bpy.types.Panel):
    bl_label = "Dynamic Simulation"
    bl_idname = "CG_PT_Dynamics_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Setting_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        sim = SimulationManager.get_instance()

        # Main action buttons
        box = layout.box()
        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.add_dynamic_elements", text="Add Dynamic Elements", icon="PLAY")
        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.remove_dynamic_elements", text="Remove Dynamic Elements", icon="X")

        if sim.active:
            box.label(
                text=f"Active: Geo cars + "
                f"{len(sim.pedestrian_manager.pedestrians)} peds, "
                f"{len(sim.traffic_light_manager.traffic_lights)} lights",
                icon="INFO",
            )

        # Car Settings
        box = layout.box()
        box.label(text="Car Settings", icon="AUTO")
        box.prop(scene, "cg_car_density")
        box.prop(scene, "cg_car_speed_min")
        box.prop(scene, "cg_car_speed_max")

        # Pedestrian Settings
        box = layout.box()
        box.label(text="Pedestrian Settings", icon="ARMATURE_DATA")
        box.prop(scene, "cg_pedestrian_density")
        box.prop(scene, "cg_pedestrian_speed")

        # Traffic Light Settings
        box = layout.box()
        box.label(text="Traffic Light Settings", icon="LIGHT")
        box.prop(scene, "cg_traffic_light_green")
        box.prop(scene, "cg_traffic_light_yellow")
        box.prop(scene, "cg_traffic_light_red")
