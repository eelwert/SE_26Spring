"""Traffic light system — intersection detection and signal cycle logic.

Identifies road intersections (vertices shared by 3+ road edges), places
traffic light objects, and implements configurable green/yellow/red cycles.
"""

import random
import bpy
from mathutils import Vector
from ..constants import (
    DYNAMICS_COLLECTION_NAME,
    DYNAMICS_TRAFFIC_LIGHTS_COLLECTION,
    DEFAULT_TRAFFIC_LIGHT_GREEN,
    DEFAULT_TRAFFIC_LIGHT_YELLOW,
    DEFAULT_TRAFFIC_LIGHT_RED,
)


class TrafficLightManager:
    """Manages traffic light placement and cycle logic at intersections."""

    def __init__(self):
        self.traffic_lights = []  # list of dicts with light data

    def place_lights(self, road_data, mesh_obj=None, green=None, yellow=None, red=None):
        """Place traffic lights at every intersection (vertex shared by 2+ edges).

        Args:
            road_data: list of dicts from RoadAnalyzer.extract_roads().
            mesh_obj: the base mesh (used to find intersection vertices).
            green: green duration in frames.
            yellow: yellow duration in frames.
            red: red duration in frames.
        """
        scene = bpy.context.scene

        if green is None:
            green = getattr(scene, "cg_traffic_light_green", DEFAULT_TRAFFIC_LIGHT_GREEN)
        if yellow is None:
            yellow = getattr(scene, "cg_traffic_light_yellow", DEFAULT_TRAFFIC_LIGHT_YELLOW)
        if red is None:
            red = getattr(scene, "cg_traffic_light_red", DEFAULT_TRAFFIC_LIGHT_RED)

        root_coll = self._get_or_create_collection(DYNAMICS_COLLECTION_NAME)
        lights_coll = self._get_or_create_collection(
            DYNAMICS_TRAFFIC_LIGHTS_COLLECTION, parent_name=DYNAMICS_COLLECTION_NAME
        )

        intersections = self._find_intersections(road_data)

        for idx, (position, connected_edges) in enumerate(intersections.items()):
            # Place one traffic light for each incoming edge at the intersection
            for edge_idx in connected_edges:
                light_name = f"TrafficLight_I{idx}_E{edge_idx}"
                light_obj = self._create_light_object(light_name, position, lights_coll)

                # Phase offset: alternating intersections get opposite starting phases
                phase_offset = 0 if idx % 2 == 0 else green + yellow

                light_obj["cg.is_traffic_light"] = True
                light_obj["cg.tl_intersection_id"] = idx
                light_obj["cg.tl_edge_id"] = edge_idx
                light_obj["cg.tl_green"] = green
                light_obj["cg.tl_yellow"] = yellow
                light_obj["cg.tl_red"] = red
                light_obj["cg.tl_phase_offset"] = phase_offset
                light_obj["cg.tl_state"] = "GREEN"
                light_obj["cg.tl_timer"] = phase_offset  # start at phase offset

                self.traffic_lights.append({
                    "obj": light_obj,
                    "position": position,
                    "intersection_id": idx,
                    "edge_id": edge_idx,
                })

        return self.traffic_lights

    def _find_intersections(self, road_data):
        """Find vertices shared by 2+ road edges (intersections).

        Returns:
            dict mapping (x, y, z) tuple -> list of edge indices connecting there.
        """
        from collections import defaultdict

        vertex_to_edges = defaultdict(list)

        for road in road_data:
            start = road["start"]
            end = road["end"]
            v0_key = (round(start.x, 3), round(start.y, 3), round(start.z, 3))
            v1_key = (round(end.x, 3), round(end.y, 3), round(end.z, 3))

            # Both endpoints of the edge are intersection candidates
            vertex_to_edges[v0_key].append(road["edge_index"])
            vertex_to_edges[v1_key].append(road["edge_index"])

        # Filter to vertices shared by 2+ distinct edges
        intersections = {}
        for vkey, edge_list in vertex_to_edges.items():
            unique_edges = list(set(edge_list))
            if len(unique_edges) >= 2:
                pos = Vector(vkey)
                pos.freeze()  # required for dict key in Blender 5.1+
                intersections[pos] = unique_edges

        return intersections

    def _create_light_object(self, name, position, collection):
        """Create a simple traffic light representation (colored sphere)."""
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.3, location=position + Vector((0, 0, 2.5))
        )
        light_obj = bpy.context.object
        light_obj.name = name

        # Move from default collection to the lights collection
        for coll in list(light_obj.users_collection):
            coll.objects.unlink(light_obj)
        collection.objects.link(light_obj)

        # Create a simple emission material for the traffic light
        mat = bpy.data.materials.new(name=f"{name}_mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        principled = nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = (0, 1, 0, 1)  # Green
            principled.inputs["Emission Strength"].default_value = 3.0
            principled.inputs["Emission Color"].default_value = (0, 1, 0, 1)

        light_obj.data.materials.append(mat)
        light_obj["cg.tl_material"] = mat.name

        return light_obj

    def update_cycle(self, scene):
        """Advance the traffic light cycle for all lights (called each frame)."""
        frame = scene.frame_current
        fps = scene.render.fps

        for light in self.traffic_lights:
            obj = light["obj"]
            green = obj["cg.tl_green"]
            yellow = obj["cg.tl_yellow"]
            red = obj["cg.tl_red"]
            phase = obj["cg.tl_phase_offset"]

            cycle_total = green + yellow + red
            if cycle_total <= 0:
                continue

            t = (frame + phase) % cycle_total

            if t < green:
                state = "GREEN"
            elif t < green + yellow:
                state = "YELLOW"
            else:
                state = "RED"

            obj["cg.tl_state"] = state
            self._update_light_color(obj, state)

    def _update_light_color(self, obj, state):
        """Update the traffic light object color based on its state."""
        mat_name = obj.get("cg.tl_material", "")
        mat = bpy.data.materials.get(mat_name)
        if not mat or not mat.use_nodes:
            return

        principled = mat.node_tree.nodes.get("Principled BSDF")
        if not principled:
            return

        colors = {
            "GREEN": (0, 1, 0, 1),
            "YELLOW": (1, 1, 0, 1),
            "RED": (1, 0, 0, 1),
        }
        color = colors.get(state, (0, 1, 0, 1))
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Emission Color"].default_value = color

    def get_light_state_at_edge(self, edge_id):
        """Get the most restrictive traffic light state for a given edge."""
        states = []
        for light in self.traffic_lights:
            if light["edge_id"] == edge_id:
                obj = light["obj"]
                states.append(obj.get("cg.tl_state", "GREEN"))

        # Return the most restrictive state
        if "RED" in states:
            return "RED"
        if "YELLOW" in states:
            return "YELLOW"
        if "GREEN" in states:
            return "GREEN"
        return "GREEN"  # default

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

    def cleanup_lights(self):
        """Remove all traffic light objects and materials."""
        lights_coll = bpy.data.collections.get(DYNAMICS_TRAFFIC_LIGHTS_COLLECTION)
        if lights_coll:
            for obj in list(lights_coll.objects):
                mat_name = obj.get("cg.tl_material", "")
                bpy.data.objects.remove(obj)
                mat = bpy.data.materials.get(mat_name)
                if mat:
                    bpy.data.materials.remove(mat)
            bpy.data.collections.remove(lights_coll)
        self.traffic_lights.clear()
