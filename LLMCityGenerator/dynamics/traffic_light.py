"""Traffic light system — intersection detection and signal cycle logic.

Each traffic light is a linked-duplicate of the blend-file ``traffic lights``
collection model.  Per-light colour is achieved by storing a private material
copy whose emission colour / strength is toggled every frame.
"""

import math
import random
import bpy
from mathutils import Vector
from collections import defaultdict
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
        self.traffic_lights = []

    # ------------------------------------------------------------------
    # Placement
    # ------------------------------------------------------------------

    def place_lights(self, road_data, mesh_obj=None, green=None, yellow=None, red=None):
        scene = bpy.context.scene

        if green is None:
            green = getattr(scene, "cg_traffic_light_green", DEFAULT_TRAFFIC_LIGHT_GREEN)
        if yellow is None:
            yellow = getattr(scene, "cg_traffic_light_yellow", DEFAULT_TRAFFIC_LIGHT_YELLOW)
        if red is None:
            red = getattr(scene, "cg_traffic_light_red", DEFAULT_TRAFFIC_LIGHT_RED)

        lights_coll = TrafficLightManager._get_or_create_collection(
            DYNAMICS_TRAFFIC_LIGHTS_COLLECTION,
            parent_name=DYNAMICS_COLLECTION_NAME,
        )

        intersections = self._find_intersections(road_data)

        for idx, (position, connected_edges) in enumerate(intersections.items()):
            phase_offset = 0  # all intersections share the same cycle
            for edge_idx in connected_edges:
                light_name = f"TrafficLight_I{idx}_E{edge_idx}"
                root = self._create_light_object(light_name, position, lights_coll)

                root["cg.is_traffic_light"] = True
                root["cg.tl_intersection_id"] = idx
                root["cg.tl_edge_id"] = edge_idx
                root["cg.tl_green"] = green
                root["cg.tl_yellow"] = yellow
                root["cg.tl_red"] = red
                root["cg.tl_phase_offset"] = phase_offset
                root["cg.tl_state"] = "GREEN"
                root["cg.tl_timer"] = phase_offset

                self.traffic_lights.append({
                    "obj": root,
                    "position": position,
                    "intersection_id": idx,
                    "edge_id": edge_idx,
                })

        return self.traffic_lights

    # ------------------------------------------------------------------
    # Intersection detection
    # ------------------------------------------------------------------

    def _find_intersections_from_mesh(self, mesh_obj):
        """Find intersections directly from the mesh — vertex = intersection
        if it has ≥2 edges.  Uses world-space vertex positions."""
        mesh = mesh_obj.data
        matrix = mesh_obj.matrix_world
        vertex_to_edges = defaultdict(list)
        for edge_idx, edge in enumerate(mesh.edges):
            for vi in edge.vertices:
                vertex_to_edges[vi].append(edge_idx)

        intersections = {}
        for vi, edge_list in vertex_to_edges.items():
            unique_edges = list(set(edge_list))
            if len(unique_edges) >= 2:
                pos = matrix @ mesh.vertices[vi].co
                pos.freeze()
                intersections[pos] = unique_edges
        return intersections

    def _find_intersections(self, road_data):
        vertex_to_edges = defaultdict(list)

        for road in road_data:
            start = road["start"]
            end = road["end"]
            v0_key = (round(start.x, 3), round(start.y, 3), round(start.z, 3))
            v1_key = (round(end.x, 3), round(end.y, 3), round(end.z, 3))
            vertex_to_edges[v0_key].append(road["edge_index"])
            vertex_to_edges[v1_key].append(road["edge_index"])

        intersections = {}
        for vkey, edge_list in vertex_to_edges.items():
            unique_edges = list(set(edge_list))
            if len(unique_edges) >= 2:
                pos = Vector(vkey)
                pos.freeze()
                intersections[pos] = unique_edges

        return intersections

    # ------------------------------------------------------------------
    # Model creation — use blend-file "traffic lights" collection
    # ------------------------------------------------------------------

    def _create_light_object(self, name, position, collection):
        """Place a traffic-light model from the blend-file collection."""
        tl_coll = self._load_traffic_light_collection()
        root = bpy.data.objects.new(name, None)
        root.empty_display_type = "CUBE"
        root.empty_display_size = 0.02
        root.hide_viewport = True
        root.hide_render = True
        root.location = position
        collection.objects.link(root)

        if tl_coll:
            for proto in tl_coll.all_objects:
                if proto.type != "MESH":
                    continue
                child = bpy.data.objects.new(name + "_" + proto.name, proto.data)
                child.parent = root
                child.location = (0, 0, 0)
                child.rotation_euler = (0, 0, 0)
                collection.objects.link(child)

        return root

    @staticmethod
    def _load_traffic_light_collection():
        """Import the 'traffic lights' collection from the bundled blend file."""
        coll = bpy.data.collections.get("traffic lights")
        if coll is not None:
            return coll

        import os
        from ..constants import ADDON_DIR, BLEND_FILE

        blend_path = os.path.join(ADDON_DIR, BLEND_FILE)
        try:
            with bpy.data.libraries.load(str(blend_path), link=False) as (_df, dt):
                setattr(dt, "collections", ["traffic lights"])
        except Exception:
            return None

        coll = bpy.data.collections.get("traffic lights")
        if coll:
            coll.hide_viewport = True
        return coll

    def _create_fallback_light(self, name, position, collection):
        """Simple sphere when the traffic-light model is unavailable."""
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.6, location=position + Vector((0, 0, 3.0))
        )
        obj = bpy.context.object
        obj.name = name
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)

        mat = bpy.data.materials.new(name=f"{name}_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0, 1, 0, 1)
            bsdf.inputs["Emission Color"].default_value = (0, 1, 0, 1)
            bsdf.inputs["Emission Strength"].default_value = 3.0
        obj.data.materials.append(mat)
        return obj

    # ------------------------------------------------------------------
    # Per-frame cycle update
    # ------------------------------------------------------------------

    def update_cycle(self, scene):
        frame = scene.frame_current

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
        """(no-op — colour cycling disabled for now)"""
        pass

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_light_state_at_edge(self, edge_id):
        states = []
        for light in self.traffic_lights:
            if light["edge_id"] == edge_id:
                st = light["obj"].get("cg.tl_state", "GREEN")
                states.append(st)
        if "RED" in states:
            return "RED"
        if "YELLOW" in states:
            return "YELLOW"
        return "GREEN"

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

    def cleanup_lights(self):
        lights_coll = bpy.data.collections.get(DYNAMICS_TRAFFIC_LIGHTS_COLLECTION)
        if lights_coll:
            for obj in list(lights_coll.objects):
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(lights_coll)
        self.traffic_lights.clear()
