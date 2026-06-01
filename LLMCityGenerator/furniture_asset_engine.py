# dA_5_add
import math
import os
import random
import time

import bpy
from mathutils import Vector

from .constants import ADDON_DIR, CITY_3D_ASSETS


# dA_5_add
GENERATED_COLLECTION_NAME = "CG_Added_3D_Assets"
SURFACE_MATERIAL_KEYWORDS = ("side walk", "sidewalk", "pavement")
ROAD_MATERIAL_KEYWORDS = ("street", "road", "lane", "curb")


# dA_5_add
def _asset_path(relative_path):
    return os.path.join(ADDON_DIR, relative_path)


# dA_5_add
def _get_city_object(context, object_name=None):
    obj = bpy.data.objects.get(object_name) if object_name else context.object
    if obj is None:
        raise ValueError("No active object selected.")

    if not obj.modifiers.get("City_Generator_2.0"):
        raise ValueError("Active object must have a City_Generator_2.0 modifier.")

    return obj


# dA_5_add
def _get_or_create_collection(name, parent_collection):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)

    if parent_collection and collection.name not in parent_collection.children:
        parent_collection.children.link(collection)

    return collection


# dA_5_add
def _ensure_source_collection(asset_id):
    asset = CITY_3D_ASSETS.get(str(asset_id))
    if asset is None:
        raise ValueError(f"3D asset '{asset_id}' does not exist.")

    collection = bpy.data.collections.get(asset["collection_name"])
    if collection is not None:
        return collection

    blend_path = _asset_path(asset["blend_path"])
    if not os.path.exists(blend_path):
        raise FileNotFoundError(f"3D asset blend file not found: {blend_path}")

    object_names = list(asset["object_names"])
    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        missing = [name for name in object_names if name not in data_from.objects]
        if missing:
            raise ValueError(f"Objects not found in {blend_path}: {', '.join(missing)}")
        data_to.objects = object_names

    collection = bpy.data.collections.new(asset["collection_name"])
    for obj in data_to.objects:
        if obj is not None and obj.name not in collection.objects:
            collection.objects.link(obj)

    return collection


# dA_5_add
def _get_or_create_generated_collection(context):
    scene_collection = context.scene.collection
    return _get_or_create_collection(GENERATED_COLLECTION_NAME, scene_collection)


# dA_5_add
def _clear_generated_instances(asset_id=None, group_id=None, city_object_name=None):
    for obj in list(bpy.data.objects):
        if not obj.get("cg_added_3d_asset_instance"):
            continue
        if asset_id is None or obj.get("cg_added_3d_asset_id") == asset_id:
            if group_id is not None and obj.get("cg_added_3d_group_id") != group_id:
                continue
            if city_object_name is not None and obj.get("cg_added_3d_city_object") != city_object_name:
                continue
            bpy.data.objects.remove(obj, do_unlink=True)


# dA_5_add
def _material_name(material_slots, material_index):
    if material_index < 0 or material_index >= len(material_slots):
        return ""
    material = material_slots[material_index].material
    return material.name.lower() if material else ""


# dA_5_add
def _is_sidewalk_material(name):
    return any(keyword in name for keyword in SURFACE_MATERIAL_KEYWORDS)


# dA_5_add
def _is_road_material(name):
    return any(keyword in name for keyword in ROAD_MATERIAL_KEYWORDS)


# dA_5_add
def _evaluated_ground_samples(context, obj):
    depsgraph = context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    sidewalk_samples = []
    road_samples = []

    try:
        material_slots = list(evaluated.material_slots)
        for poly in mesh.polygons:
            material_name = _material_name(material_slots, poly.material_index)
            world_center = evaluated.matrix_world @ poly.center
            if _is_sidewalk_material(material_name):
                sidewalk_samples.append(world_center)
            elif _is_road_material(material_name):
                road_samples.append(world_center)
    finally:
        evaluated.to_mesh_clear()

    return sidewalk_samples, road_samples


# dA_5_add
def _evaluated_street_edges(context, obj):
    depsgraph = context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    edge_map = {}
    poly_info = {}

    try:
        material_slots = list(evaluated.material_slots)
        for poly in mesh.polygons:
            material_name = _material_name(material_slots, poly.material_index)
            if _is_sidewalk_material(material_name):
                kind = "sidewalk"
            elif _is_road_material(material_name):
                kind = "road"
            else:
                continue

            poly_info[poly.index] = {
                "kind": kind,
                "center": evaluated.matrix_world @ poly.center,
            }
            for edge_key in poly.edge_keys:
                edge_map.setdefault(tuple(edge_key), []).append(poly.index)

        street_edges = []
        for edge_key, poly_indices in edge_map.items():
            if len(poly_indices) < 2:
                continue

            sidewalk_index = None
            road_index = None
            for poly_index in poly_indices:
                info = poly_info.get(poly_index)
                if info is None:
                    continue
                if info["kind"] == "sidewalk":
                    sidewalk_index = poly_index
                elif info["kind"] == "road":
                    road_index = poly_index

            if sidewalk_index is None or road_index is None:
                continue

            v1 = evaluated.matrix_world @ mesh.vertices[edge_key[0]].co
            v2 = evaluated.matrix_world @ mesh.vertices[edge_key[1]].co
            tangent = Vector((v2.x - v1.x, v2.y - v1.y, 0.0))
            if tangent.length < 0.001:
                continue
            edge_length = tangent.length
            tangent.normalize()

            sidewalk_center = poly_info[sidewalk_index]["center"]
            road_center = poly_info[road_index]["center"]
            inward = Vector((sidewalk_center.x - road_center.x, sidewalk_center.y - road_center.y, 0.0))
            if inward.length < 0.001:
                inward = Vector((-tangent.y, tangent.x, 0.0))
            inward.normalize()

            street_edges.append({
                "midpoint": (v1 + v2) * 0.5,
                "tangent": tangent,
                "inward": inward,
                "length": edge_length,
            })
    finally:
        evaluated.to_mesh_clear()

    return street_edges


# dA_5_add
def _evaluated_world_bounds(context, obj):
    depsgraph = context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    bound_points = [evaluated.matrix_world @ Vector(bound_point) for bound_point in evaluated.bound_box]

    min_x = min(point.x for point in bound_points)
    max_x = max(point.x for point in bound_points)
    min_y = min(point.y for point in bound_points)
    max_y = max(point.y for point in bound_points)
    min_z = min(point.z for point in bound_points)

    if math.isclose(min_x, max_x) or math.isclose(min_y, max_y):
        raise ValueError("City object bounds are too small to place 3D assets.")

    return min_x, max_x, min_y, max_y, min_z


# dA_5_add
def _source_collection_metrics(collection):
    min_z = None
    max_z = None
    min_x = None
    max_x = None
    min_y = None
    max_y = None
    max_x_radius = 0.0
    max_y_radius = 0.0

    for obj in collection.all_objects:
        for bound_point in obj.bound_box:
            world_point = obj.matrix_world @ Vector(bound_point)
            min_z = world_point.z if min_z is None else min(min_z, world_point.z)
            max_z = world_point.z if max_z is None else max(max_z, world_point.z)
            min_x = world_point.x if min_x is None else min(min_x, world_point.x)
            max_x = world_point.x if max_x is None else max(max_x, world_point.x)
            min_y = world_point.y if min_y is None else min(min_y, world_point.y)
            max_y = world_point.y if max_y is None else max(max_y, world_point.y)
            max_x_radius = max(max_x_radius, abs(world_point.x))
            max_y_radius = max(max_y_radius, abs(world_point.y))

    width = (max_x - min_x) if min_x is not None and max_x is not None else max_x_radius * 2.0
    depth = (max_y - min_y) if min_y is not None and max_y is not None else max_y_radius * 2.0
    height = (max_z - min_z) if min_z is not None and max_z is not None else 1.0
    radius = max(width, depth, 0.4) * 0.5
    return min_z or 0.0, radius, height


# dA_5_add
def _existing_asset_obstacles(asset_id=None):
    obstacles = []
    for obj in bpy.data.objects:
        if not obj.get("cg_added_3d_asset_instance"):
            continue
        if asset_id is not None and obj.get("cg_added_3d_asset_id") == asset_id:
            continue
        radius = float(obj.get("cg_added_3d_asset_radius", 1.0))
        obstacles.append((Vector((obj.location.x, obj.location.y, 0.0)), radius))
    return obstacles


# dA_5_add
def _modifier_collection_object_names(mod, socket_id):
    collection = mod.get(socket_id)
    if collection is None or not hasattr(collection, "all_objects"):
        return set()
    return {obj.name for obj in collection.all_objects}


# dA_5_add
def _street_reference_instances(context, obj):
    mod = obj.modifiers.get("City_Generator_2.0")
    if mod is None:
        return []

    reference_names = set()
    for socket_id in ("Socket_166", "Socket_69", "Socket_70"):
        reference_names.update(_modifier_collection_object_names(mod, socket_id))

    depsgraph = context.evaluated_depsgraph_get()
    references = []
    for instance in depsgraph.object_instances:
        source = instance.object
        if source is None:
            continue

        source_name = source.name
        source_name_lower = source_name.lower()
        if source_name not in reference_names and not source_name_lower.startswith("tree"):
            continue

        parent = instance.parent
        if parent is not None and getattr(parent, "name", None) != obj.name:
            continue

        location = instance.matrix_world.translation.copy()
        references.append(location)

    return references


# dA_5_add
def _split_reference_points(references):
    if not references:
        return [], None

    min_x = min(point.x for point in references)
    max_x = max(point.x for point in references)
    min_y = min(point.y for point in references)
    max_y = max(point.y for point in references)
    width = max(max_x - min_x, 0.001)
    depth = max(max_y - min_y, 0.001)
    side_band = min(width, depth) * 0.16

    straight = []

    for point in references:
        near_left = abs(point.x - min_x) <= side_band
        near_right = abs(point.x - max_x) <= side_band
        near_bottom = abs(point.y - min_y) <= side_band
        near_top = abs(point.y - max_y) <= side_band
        near_x_side = near_left or near_right
        near_y_side = near_bottom or near_top

        if near_x_side != near_y_side:
            straight.append(point)

    bounds = (min_x, max_x, min_y, max_y)
    return straight, bounds


# dA_5_add
def _sort_reference_ring(points, bounds):
    min_x, max_x, min_y, max_y = bounds
    width = max(max_x - min_x, 0.001)
    depth = max(max_y - min_y, 0.001)

    def key(point):
        distances = (
            (abs(point.y - min_y), 0, point.x - min_x),
            (abs(point.x - max_x), 1, width + point.y - min_y),
            (abs(point.y - max_y), 2, width + depth + max_x - point.x),
            (abs(point.x - min_x), 3, 2.0 * width + depth + max_y - point.y),
        )
        return min(distances, key=lambda item: item[0])[2]

    return sorted(points, key=key)


# dA_5_add
def _sample_from_street_references(context, obj, count, spacing, min_distance):
    references = _street_reference_instances(context, obj)
    if not references:
        return []

    candidate_refs, bounds = _split_reference_points(references)
    if bounds is None:
        return []

    min_x, max_x, min_y, max_y = bounds
    center = Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, 0.0))

    if not candidate_refs:
        return []

    candidate_refs = _sort_reference_ring(candidate_refs, bounds)
    stride = max(1, int(max(float(spacing), 1.0) / 4.0))
    chosen = []
    obstacles = []
    obstacles.extend((Vector((point.x, point.y, 0.0)), min_distance * 0.65) for point in references)

    for source_index in range(len(candidate_refs) * 3):
        point = candidate_refs[(source_index * stride) % len(candidate_refs)]
        radial = Vector((point.x - center.x, point.y - center.y, 0.0))
        if radial.length < 0.001:
            radial = Vector((1.0, 0.0, 0.0))
        radial.normalize()

        tangent = Vector((-radial.y, radial.x, 0.0))
        angle = math.atan2(tangent.y, tangent.x)
        base_point = point + tangent * min_distance * (1.05 + 0.12 * (source_index % 3))
        base_point, angle = _naturalized_point(base_point, angle, source_index, spacing)
        moved = _resolve_overlap(base_point, angle, obstacles, min_distance)
        if moved is None:
            continue

        chosen.append((moved, angle))
        obstacles.append((Vector((moved.x, moved.y, 0.0)), min_distance))
        if len(chosen) >= max(1, int(count)):
            break

    return chosen


# dA_5_add
def _band_value(point, center, max_dx, max_dy):
    dx = abs(point.x - center.x) / max(max_dx, 0.001)
    dy = abs(point.y - center.y) / max(max_dy, 0.001)
    return max(dx, dy)


# dA_5_add
def _nearest_distance(point, samples):
    if not samples:
        return None
    point_2d = Vector((point.x, point.y, 0.0))
    return min((point_2d - Vector((sample.x, sample.y, 0.0))).length for sample in samples)


# dA_5_add
def _nearest_sample(point, samples):
    if not samples:
        return None

    point_2d = Vector((point.x, point.y, 0.0))
    return min(
        samples,
        key=lambda sample: (point_2d - Vector((sample.x, sample.y, 0.0))).length,
    )


# dA_5_add
def _surface_ring_key(point, min_x, max_x, min_y, max_y):
    width = max(max_x - min_x, 0.001)
    depth = max(max_y - min_y, 0.001)
    distances = (
        (abs(point.y - min_y), point.x - min_x),
        (abs(point.x - max_x), width + point.y - min_y),
        (abs(point.y - max_y), width + depth + max_x - point.x),
        (abs(point.x - min_x), 2.0 * width + depth + max_y - point.y),
    )
    return min(distances, key=lambda item: item[0])[1]


# dA_5_add
def _surface_side(point, min_x, max_x, min_y, max_y):
    distances = (
        (abs(point.y - min_y), "bottom"),
        (abs(point.x - max_x), "right"),
        (abs(point.y - max_y), "top"),
        (abs(point.x - min_x), "left"),
    )
    return min(distances, key=lambda item: item[0])[1]


# dA_5_add
def _side_angle(side):
    if side == "right":
        return math.pi / 2.0
    if side == "top":
        return math.pi
    if side == "left":
        return -math.pi / 2.0
    return 0.0


# dA_5_add
def _side_axis_value(point, side):
    return point.y if side in {"left", "right"} else point.x


# dA_5_add
def _side_normal_value(point, side):
    return point.x if side in {"left", "right"} else point.y


# dA_5_add
def _point_from_side_values(axis_value, normal_value, z, side):
    if side in {"left", "right"}:
        return Vector((normal_value, axis_value, z))
    return Vector((axis_value, normal_value, z))


# dA_5_add
def _modifier_float(obj, socket_id, default):
    mod = obj.modifiers.get("City_Generator_2.0")
    if mod is None:
        return float(default)
    try:
        return float(mod.get(socket_id, default))
    except (TypeError, ValueError):
        return float(default)


# dA_5_add
def _clamp(value, low, high):
    return max(low, min(high, value))


# dA_5_add
def _point_in_polygon_2d(point, polygon):
    x = point.x
    y = point.y
    inside = False
    count = len(polygon)
    if count < 3:
        return False

    previous = polygon[-1]
    for current in polygon:
        intersects = ((current.y > y) != (previous.y > y))
        if intersects:
            denominator = previous.y - current.y
            if abs(denominator) < 0.000001:
                denominator = 0.000001
            cross_x = (previous.x - current.x) * (y - current.y) / denominator + current.x
            if x < cross_x:
                inside = not inside
        previous = current
    return inside


# dA_5_add
def _is_building_instance_name(name):
    lowered = name.lower()
    if any(word in lowered for word in ("floor", "building", "facade", "trimm", "curved building")):
        return not any(word in lowered for word in ("sign", "box", "duct", "antenna", "pipe", "scaffold"))
    return False


# dA_5_add
def _building_points_by_source_face(context, obj, face_polygons):
    if not face_polygons:
        return {}

    depsgraph = context.evaluated_depsgraph_get()
    points_by_face = {face_index: [] for face_index in face_polygons}
    for instance in depsgraph.object_instances:
        source = instance.object
        if source is None or not _is_building_instance_name(source.name):
            continue

        parent = instance.parent
        if parent is not None and getattr(parent, "name", None) != obj.name:
            continue

        location = instance.matrix_world.translation.copy()
        point = Vector((location.x, location.y, 0.0))
        for face_index, polygon in face_polygons.items():
            if _point_in_polygon_2d(point, polygon):
                points_by_face[face_index].append(point)
                break

    return points_by_face


# dA_5_add
def _ground_points_by_source_face(context, obj, face_polygons):
    sidewalk_samples, road_samples = _evaluated_ground_samples(context, obj)
    sidewalk_by_face = {face_index: [] for face_index in face_polygons}
    road_by_face = {face_index: [] for face_index in face_polygons}

    for sample in sidewalk_samples:
        point = Vector((sample.x, sample.y, 0.0))
        for face_index, polygon in face_polygons.items():
            if _point_in_polygon_2d(point, polygon):
                sidewalk_by_face[face_index].append(point)
                break

    for sample in road_samples:
        point = Vector((sample.x, sample.y, 0.0))
        for face_index, polygon in face_polygons.items():
            if _point_in_polygon_2d(point, polygon):
                road_by_face[face_index].append(point)
                break

    return sidewalk_by_face, road_by_face


# dA_5_add
def _edge_projected_distances(points, road_start, tangent, inward, length):
    distances = []
    road_start_2d = Vector((road_start.x, road_start.y, 0.0))
    for point in points:
        relative = point - road_start_2d
        axis_value = relative.dot(tangent)
        if axis_value < 0.0 or axis_value > length:
            continue
        normal_distance = relative.dot(inward)
        if normal_distance >= 0.0:
            distances.append(normal_distance)
    return distances


# dA_5_add
def _edge_projected_axis_range(points, road_start, tangent, inward, length, sidewalk_start, sidewalk_end):
    axis_values = []
    road_start_2d = Vector((road_start.x, road_start.y, 0.0))
    for point in points:
        relative = point - road_start_2d
        axis_value = relative.dot(tangent)
        if axis_value < 0.0 or axis_value > length:
            continue
        normal_distance = relative.dot(inward)
        if sidewalk_start <= normal_distance <= sidewalk_end:
            axis_values.append(axis_value)

    if len(axis_values) < 2:
        return 0.0, length
    return max(0.0, min(axis_values)), min(length, max(axis_values))


# dA_5_add
def _asset_kind(asset):
    object_names = {str(name).lower() for name in asset.get("object_names", ())}
    blend_path = str(asset.get("blend_path", "")).lower()
    collection_name = str(asset.get("collection_name", "")).lower()
    identity = " ".join([blend_path, collection_name, " ".join(sorted(object_names))])

    if "wooden_picnic_table" in identity:
        return "picnic_table"
    if "small_lpg_tank" in identity:
        return "lpg_tank"
    if "rubber_duck_toy" in identity:
        return "rubber_duck"
    return "generic"


# dA_5_add
def _test_sidewalk_position_ratio(asset, randomize):
    if randomize:
        return _clamp(float(asset.get("sidewalk_position", 0.52)), 0.15, 0.9)

    kind = _asset_kind(asset)
    if kind == "picnic_table":
        return 0.02
    if kind == "rubber_duck":
        return 0.98
    return _clamp(float(asset.get("sidewalk_position", 0.52)), 0.15, 0.9)


# dA_5_add
def _fallback_sidewalk_band_values(obj):
    road_width = max(0.1, _modifier_float(obj, "Socket_9", 8.0))
    sidewalk_scale = max(0.6, _modifier_float(obj, "Socket_16", 6.0))
    curb_width = max(0.0, _modifier_float(obj, "Socket_24", 0.1))
    road_edge_offset = road_width * 0.5
    sidewalk_start = road_edge_offset + curb_width + 0.12
    sidewalk_end = road_edge_offset + sidewalk_scale
    if sidewalk_end <= sidewalk_start + 0.45:
        sidewalk_end = sidewalk_start + 0.45
    return sidewalk_start, sidewalk_end


# dA_5_add
def _fallback_sidewalk_band_offsets(obj, asset, placement_offset=0.0, randomize=False):
    sidewalk_start, sidewalk_end = _fallback_sidewalk_band_values(obj)
    return _offset_from_band(asset, sidewalk_start, sidewalk_end, placement_offset, randomize)


# dA_5_add
def _offset_from_band(asset, sidewalk_start, sidewalk_end, placement_offset=0.0, randomize=False):
    if sidewalk_end <= sidewalk_start:
        sidewalk_end = sidewalk_start + 0.45

    ratio = _test_sidewalk_position_ratio(asset, randomize)
    sidewalk_width = max(0.45, sidewalk_end - sidewalk_start)
    base_offset = sidewalk_start + sidewalk_width * ratio + float(placement_offset)
    base_offset = _clamp(base_offset, sidewalk_start + 0.05, sidewalk_end - 0.05)
    return {
        "base": base_offset,
        "start": sidewalk_start,
        "end": sidewalk_end,
        "width": sidewalk_width,
    }


# dA_5_add
def _sidewalk_band_offsets_from_samples(
    obj,
    asset,
    road_start,
    tangent,
    inward,
    length,
    sidewalk_points,
    road_points,
    building_points=None,
    placement_offset=0.0,
    randomize=False,
):
    sidewalk_distances = _edge_projected_distances(sidewalk_points, road_start, tangent, inward, length)
    if len(sidewalk_distances) < 2:
        return _fallback_sidewalk_band_offsets(obj, asset, placement_offset, randomize=randomize)

    sidewalk_min = min(sidewalk_distances)
    sidewalk_max = max(sidewalk_distances)
    road_distances = [
        distance
        for distance in _edge_projected_distances(road_points, road_start, tangent, inward, length)
        if distance <= sidewalk_min
    ]
    sidewalk_start = (max(road_distances) + sidewalk_min) * 0.5 if road_distances else sidewalk_min
    sidewalk_end = sidewalk_max
    fallback_start, fallback_end = _fallback_sidewalk_band_values(obj)
    fallback_width = max(0.45, fallback_end - fallback_start)
    sidewalk_end = min(sidewalk_end, sidewalk_start + fallback_width)

    if building_points:
        building_distances = _edge_projected_distances(building_points, road_start, tangent, inward, length)
        if building_distances:
            building_inner_limit = min(building_distances)
            if building_inner_limit > sidewalk_start + 0.45:
                sidewalk_end = min(sidewalk_end, building_inner_limit)

    if sidewalk_end <= sidewalk_start + 0.2:
        return _fallback_sidewalk_band_offsets(obj, asset, placement_offset, randomize=randomize)

    return _offset_from_band(asset, sidewalk_start, sidewalk_end, placement_offset, randomize)


# dA_5_add
def _source_mesh_street_segments(context, obj, asset, placement_offset=0.0, randomize=False):
    if obj.type != "MESH" or obj.data is None:
        return []

    mesh = obj.data
    if not mesh.polygons:
        return []

    matrix = obj.matrix_world
    face_polygons = {}
    for poly in mesh.polygons:
        if len(poly.vertices) >= 3:
            face_polygons[poly.index] = [
                Vector(((matrix @ mesh.vertices[index].co).x, (matrix @ mesh.vertices[index].co).y, 0.0))
                for index in poly.vertices
            ]
    sidewalk_points_by_face, road_points_by_face = _ground_points_by_source_face(context, obj, face_polygons)
    building_points_by_face = _building_points_by_source_face(context, obj, face_polygons)
    segments = []

    for poly in mesh.polygons:
        if len(poly.vertices) < 3:
            continue

        world_vertices = [matrix @ mesh.vertices[index].co for index in poly.vertices]
        center = sum((vertex for vertex in world_vertices), Vector()) / len(world_vertices)
        center_2d = Vector((center.x, center.y, 0.0))
        z = min(vertex.z for vertex in world_vertices)

        for local_index, start_vertex_index in enumerate(poly.vertices):
            end_vertex_index = poly.vertices[(local_index + 1) % len(poly.vertices)]
            v1 = matrix @ mesh.vertices[start_vertex_index].co
            v2 = matrix @ mesh.vertices[end_vertex_index].co
            tangent = Vector((v2.x - v1.x, v2.y - v1.y, 0.0))
            length = tangent.length
            if length < 0.5:
                continue
            tangent.normalize()

            midpoint = Vector(((v1.x + v2.x) * 0.5, (v1.y + v2.y) * 0.5, z))
            left_normal = Vector((-tangent.y, tangent.x, 0.0))
            right_normal = Vector((tangent.y, -tangent.x, 0.0))
            to_center = center_2d - Vector((midpoint.x, midpoint.y, 0.0))
            inward = left_normal if left_normal.dot(to_center) >= right_normal.dot(to_center) else right_normal
            if inward.length < 0.001:
                continue
            inward.normalize()

            road_start = Vector((v1.x, v1.y, z))
            road_end = Vector((v2.x, v2.y, z))
            sidewalk_offsets = _sidewalk_band_offsets_from_samples(
                obj,
                asset,
                road_start,
                tangent,
                inward,
                length,
                sidewalk_points_by_face.get(poly.index, []),
                road_points_by_face.get(poly.index, []),
                building_points_by_face.get(poly.index, []),
                placement_offset,
                randomize=randomize,
            )
            axis_start, axis_end = _edge_projected_axis_range(
                sidewalk_points_by_face.get(poly.index, []),
                road_start,
                tangent,
                inward,
                length,
                sidewalk_offsets["start"],
                sidewalk_offsets["end"],
            )
            if axis_end <= axis_start:
                continue
            base_start = road_start + inward * sidewalk_offsets["base"]
            base_end = road_end + inward * sidewalk_offsets["base"]

            segments.append({
                "axis": "generic",
                "start": axis_start,
                "end": axis_end,
                "normal": 0.0,
                "z": z,
                "tangent": tangent,
                "inward": inward,
                "length": max(0.0, axis_end - axis_start),
                "base_start": base_start,
                "base_end": base_end,
                "road_start": road_start,
                "road_end": road_end,
                "base_offset": sidewalk_offsets["base"],
                "sidewalk_start": sidewalk_offsets["start"],
                "sidewalk_end": sidewalk_offsets["end"],
                "source": "mesh",
                "face_index": poly.index,
            })

    return segments


# dA_5_add
def _merged_street_segments(context, obj, asset, placement_offset=0.0, randomize=False):
    source_segments = _source_mesh_street_segments(context, obj, asset, placement_offset, randomize=randomize)
    if source_segments:
        return source_segments

    street_edges = _evaluated_street_edges(context, obj)
    if not street_edges:
        return _street_segments_from_surface_samples(context, obj, asset, placement_offset)

    buckets = {}
    for edge in street_edges:
        tangent = edge["tangent"]
        if abs(tangent.x) >= abs(tangent.y):
            axis = "x"
            direction = Vector((1.0, 0.0, 0.0))
            normal_key = round(edge["midpoint"].y, 1)
            axis_value = edge["midpoint"].x
        else:
            axis = "y"
            direction = Vector((0.0, 1.0, 0.0))
            normal_key = round(edge["midpoint"].x, 1)
            axis_value = edge["midpoint"].y

        if edge["tangent"].dot(direction) < 0.0:
            direction = -direction

        key = (axis, normal_key, round(edge["inward"].x, 1), round(edge["inward"].y, 1))
        buckets.setdefault(key, []).append((axis_value, edge, direction))

    segments = []
    merge_gap = 1.2
    for (axis, _normal_key, _inward_x, _inward_y), items in buckets.items():
        items.sort(key=lambda item: item[0])
        current = []
        previous_axis = None

        for axis_value, edge, direction in items:
            if previous_axis is not None and axis_value - previous_axis > merge_gap:
                if current:
                    segments.append(_build_street_segment(axis, current, asset, placement_offset))
                current = []
            current.append((axis_value, edge, direction))
            previous_axis = axis_value

        if current:
            segments.append(_build_street_segment(axis, current, asset, placement_offset))

    return [segment for segment in segments if segment is not None and segment["length"] > 0.5]


# dA_5_add
def _street_segments_from_surface_samples(context, obj, asset, placement_offset=0.0):
    sidewalk_samples, road_samples = _evaluated_ground_samples(context, obj)
    if not sidewalk_samples or not road_samples:
        return []

    min_x = min(point.x for point in sidewalk_samples)
    max_x = max(point.x for point in sidewalk_samples)
    min_y = min(point.y for point in sidewalk_samples)
    max_y = max(point.y for point in sidewalk_samples)
    center = Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, 0.0))
    max_dx = (max_x - min_x) * 0.5
    max_dy = (max_y - min_y) * 0.5
    band_min, band_max = asset.get("street_band", (0.55, 1.02))
    buckets = {}

    for sample in sidewalk_samples:
        band = _band_value(sample, center, max_dx, max_dy)
        if not (band_min <= band <= band_max):
            continue

        nearest_road = _nearest_sample(sample, road_samples)
        if nearest_road is None:
            continue

        inward = Vector((sample.x - nearest_road.x, sample.y - nearest_road.y, 0.0))
        if inward.length < 0.001:
            continue
        inward.normalize()

        if abs(inward.x) >= abs(inward.y):
            axis = "y"
            normal_value = sample.x
            axis_value = sample.y
            tangent = Vector((0.0, 1.0, 0.0))
        else:
            axis = "x"
            normal_value = sample.y
            axis_value = sample.x
            tangent = Vector((1.0, 0.0, 0.0))

        normal_key = round(normal_value / 4.0)
        key = (axis, normal_key, round(inward.x, 0), round(inward.y, 0))
        buckets.setdefault(key, []).append({
            "axis_value": axis_value,
            "midpoint": sample.copy(),
            "inward": inward,
            "tangent": tangent,
            "length": 1.0,
        })

    segments = []
    merge_gap = max(4.0, float(asset.get("street_inset", 2.2)) * 1.5)
    for (axis, _normal_key, _inward_x, _inward_y), items in buckets.items():
        items.sort(key=lambda item: item["axis_value"])
        current = []
        previous_axis = None
        for item in items:
            axis_value = item["axis_value"]
            if previous_axis is not None and axis_value - previous_axis > merge_gap:
                if current:
                    segments.append(_build_sample_street_segment(axis, current, asset, placement_offset))
                current = []
            current.append(item)
            previous_axis = axis_value
        if current:
            segments.append(_build_sample_street_segment(axis, current, asset, placement_offset))

    segments = [segment for segment in segments if segment is not None and segment["length"] > 0.5]
    if not segments or max(segment["length"] for segment in segments) < 8.0:
        return _perimeter_street_segments_from_samples(sidewalk_samples, asset)
    return segments


# dA_5_add
def _perimeter_street_segments_from_samples(samples, asset):
    if not samples:
        return []

    min_x = min(point.x for point in samples)
    max_x = max(point.x for point in samples)
    min_y = min(point.y for point in samples)
    max_y = max(point.y for point in samples)
    z = sum(point.z for point in samples) / len(samples)
    inset = float(asset.get("street_inset", 2.2))
    margin = min(max_x - min_x, max_y - min_y) * 0.12

    raw_segments = (
        ("x", min_x + margin, max_x - margin, min_y + inset, Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))),
        ("y", min_y + margin, max_y - margin, max_x - inset, Vector((0.0, 1.0, 0.0)), Vector((-1.0, 0.0, 0.0))),
        ("x", min_x + margin, max_x - margin, max_y - inset, Vector((1.0, 0.0, 0.0)), Vector((0.0, -1.0, 0.0))),
        ("y", min_y + margin, max_y - margin, min_x + inset, Vector((0.0, 1.0, 0.0)), Vector((1.0, 0.0, 0.0))),
    )

    segments = []
    for axis, start_axis, end_axis, normal_value, tangent, inward in raw_segments:
        length = max(0.0, end_axis - start_axis)
        if length <= 0.5:
            continue
        segments.append({
            "axis": axis,
            "start": start_axis,
            "end": end_axis,
            "normal": normal_value,
            "z": z,
            "tangent": tangent,
            "inward": inward,
            "length": length,
        })
    return segments


# dA_5_add
def _build_sample_street_segment(axis, items, asset, placement_offset=0.0):
    if not items:
        return None

    values = [item["axis_value"] for item in items]
    start_axis = min(values)
    end_axis = max(values)
    length = max(0.0, end_axis - start_axis)
    if length <= 0.0:
        return None

    midpoint = sum((item["midpoint"] for item in items), Vector()) / len(items)
    inward = sum((item["inward"] for item in items), Vector())
    if inward.length < 0.001:
        inward = Vector((0.0, 1.0, 0.0)) if axis == "x" else Vector((1.0, 0.0, 0.0))
    inward.normalize()

    tangent = Vector((1.0, 0.0, 0.0)) if axis == "x" else Vector((0.0, 1.0, 0.0))
    z = sum(item["midpoint"].z for item in items) / len(items)
    street_inset = max(0.1, float(asset.get("street_inset", 2.2)) + float(placement_offset))
    base_midpoint = midpoint + inward * street_inset
    normal_value = base_midpoint.y if axis == "x" else base_midpoint.x
    end_margin = min(1.0, length * 0.15)

    return {
        "axis": axis,
        "start": start_axis + end_margin,
        "end": end_axis - end_margin,
        "normal": normal_value,
        "z": z,
        "tangent": tangent,
        "inward": inward,
        "length": max(0.0, length - end_margin * 2.0),
    }


# dA_5_add
def _build_street_segment(axis, items, asset, placement_offset=0.0):
    first_axis = min(item[0] for item in items)
    last_axis = max(item[0] for item in items)
    edge_half = sum(item[1]["length"] for item in items) / max(len(items), 1) * 0.5
    start_axis = first_axis - edge_half
    end_axis = last_axis + edge_half
    length = max(0.0, end_axis - start_axis)
    if length <= 0.0:
        return None

    midpoint = sum((item[1]["midpoint"] for item in items), Vector()) / len(items)
    inward = sum((item[1]["inward"] for item in items), Vector())
    if inward.length < 0.001:
        inward = Vector((0.0, 1.0, 0.0)) if axis == "x" else Vector((1.0, 0.0, 0.0))
    inward.normalize()

    tangent = Vector((1.0, 0.0, 0.0)) if axis == "x" else Vector((0.0, 1.0, 0.0))
    z = sum(item[1]["midpoint"].z for item in items) / len(items)
    street_inset = max(0.1, float(asset.get("street_inset", 2.2)) + float(placement_offset))
    base_midpoint = midpoint + inward * street_inset
    normal_value = base_midpoint.y if axis == "x" else base_midpoint.x

    return {
        "axis": axis,
        "start": start_axis,
        "end": end_axis,
        "normal": normal_value,
        "z": z,
        "tangent": tangent,
        "inward": inward,
        "length": length,
    }


# dA_5_add
def _segment_point(segment, axis_value, random_normal_offset=0.0, boundary_margin=0.0):
    if segment.get("axis") == "generic":
        offset = segment.get("base_offset", 0.0) + random_normal_offset
        if "sidewalk_start" in segment and "sidewalk_end" in segment:
            margin = max(0.05, float(boundary_margin))
            low = segment["sidewalk_start"] + margin
            high = segment["sidewalk_end"] - margin
            if high <= low:
                middle = (segment["sidewalk_start"] + segment["sidewalk_end"]) * 0.5
                low = high = middle
            offset = _clamp(offset, low, high)
        return segment["road_start"] + segment["tangent"] * axis_value + segment["inward"] * offset
    if segment["axis"] == "x":
        return Vector((axis_value, segment["normal"], segment["z"])) + segment["inward"] * random_normal_offset
    return Vector((segment["normal"], axis_value, segment["z"])) + segment["inward"] * random_normal_offset


# dA_5_add
def _segment_axis_limits(segment, boundary_margin):
    margin = max(0.05, float(boundary_margin) * 4.0)
    start_axis = segment["start"] + margin
    end_axis = segment["end"] - margin
    if end_axis < start_axis:
        return None
    return start_axis, end_axis


# dA_5_add
def _segment_normal_offset_limits(segment, boundary_margin):
    if "sidewalk_start" not in segment or "sidewalk_end" not in segment:
        return 0.0, 0.0

    margin = max(0.05, float(boundary_margin))
    low = segment["sidewalk_start"] + margin - segment.get("base_offset", 0.0)
    high = segment["sidewalk_end"] - margin - segment.get("base_offset", 0.0)
    if high < low:
        return None
    return low, high


# dA_5_add
def _segment_random_normal_offset_limits(segment, normal_limits, spacing, boundary_margin):
    return normal_limits


# dA_5_add
def _deterministic_street_edge_normal_offset(asset, segment, boundary_margin):
    if "sidewalk_start" not in segment or "sidewalk_end" not in segment:
        return 0.0

    sidewalk_start = float(segment["sidewalk_start"])
    sidewalk_end = float(segment["sidewalk_end"])
    base_offset = float(segment.get("base_offset", sidewalk_start))
    if sidewalk_end <= sidewalk_start:
        return 0.0

    asset_box_side = max(0.1, float(boundary_margin) * 2.0)
    kind = _asset_kind(asset)
    if kind == "picnic_table":
        target_offset = sidewalk_start + asset_box_side
    elif kind == "lpg_tank":
        target_offset = sidewalk_end - asset_box_side * 0.4
    elif kind == "rubber_duck":
        target_offset = (sidewalk_start + sidewalk_end) * 0.5 + asset_box_side * 0.2
    else:
        target_offset = base_offset

    safe_low = sidewalk_start + max(0.05, float(boundary_margin))
    safe_high = sidewalk_end - max(0.05, float(boundary_margin))
    if safe_high < safe_low:
        target_offset = (sidewalk_start + sidewalk_end) * 0.5
    else:
        target_offset = _clamp(target_offset, safe_low, safe_high)
    return target_offset - base_offset


# dA_5_add
def _count_for_unit(rng, min_count, max_count):
    low = max(0, int(min_count))
    high = max(low, int(max_count))
    return rng.randint(low, high)


# dA_5_add
def _placement_item(point, angle, unit_id=None):
    return (point, angle, unit_id)


# dA_5_add
def _unpack_placement_item(item, fallback_group_id=None):
    if len(item) >= 3:
        return item[0], item[1], item[2]
    return item[0], item[1], fallback_group_id


# dA_5_add
def _street_edge_points(context, obj, asset, min_count, max_count, spacing, min_distance, randomize=False, placement_offset=0.0, boundary_margin=0.0):
    segments = _merged_street_segments(context, obj, asset, placement_offset, randomize=randomize)
    if not segments:
        return []

    rng = random.Random()
    obstacles = []
    chosen = []
    strict_spacing = max(float(spacing), 0.1)
    random_spacing = max(float(spacing), min_distance)

    for segment_index, segment in enumerate(segments):
        unit_id = f"street_edge_segment_{segment_index:03d}"
        segment_rng = random.Random(f"{time.time_ns()}|{segment_index}|{unit_id}|{rng.random()}")
        target_count = _count_for_unit(segment_rng, min_count, max_count)
        axis_limits = _segment_axis_limits(segment, boundary_margin)
        normal_limits = _segment_normal_offset_limits(segment, boundary_margin)
        if axis_limits is None or normal_limits is None:
            continue
        start_limit, end_limit = axis_limits
        usable_length = max(0.0, end_limit - start_limit)
        step_spacing = random_spacing if randomize else strict_spacing
        capacity = int(usable_length // max(step_spacing, 0.1)) + 1 if usable_length > 0.0 else 0
        target_count = min(target_count, capacity)
        if target_count <= 0:
            continue

        angle = math.atan2(segment["tangent"].y, segment["tangent"].x)
        if randomize:
            placed_on_segment = []
            random_normal_limits = _segment_random_normal_offset_limits(
                segment,
                normal_limits,
                random_spacing,
                boundary_margin,
            )
            attempts = max(80, target_count * 36)
            for _attempt in range(attempts):
                axis_value = segment_rng.uniform(start_limit, end_limit)
                if random_normal_limits[0] == random_normal_limits[1]:
                    normal_offset = random_normal_limits[0]
                else:
                    normal_offset = segment_rng.uniform(random_normal_limits[0], random_normal_limits[1])
                point = _segment_point(segment, axis_value, normal_offset, boundary_margin)
                local_obstacles = obstacles + [
                    (Vector((p.x, p.y, 0.0)), random_spacing)
                    for p, _angle, _group_id in placed_on_segment
                ]
                if not _candidate_far_enough(point, local_obstacles, random_spacing):
                    continue
                jitter_angle = segment_rng.uniform(-0.3, 0.3)
                placed_on_segment.append(_placement_item(point, angle + jitter_angle, unit_id))
                if len(placed_on_segment) >= target_count:
                    break
            for point, point_angle, point_group_id in placed_on_segment:
                chosen.append(_placement_item(point, point_angle, point_group_id))
                obstacles.append((Vector((point.x, point.y, 0.0)), random_spacing))
        else:
            used_length = (target_count - 1) * strict_spacing
            start_axis = start_limit + (usable_length - used_length) * 0.5
            deterministic_normal_offset = _deterministic_street_edge_normal_offset(asset, segment, boundary_margin)
            for index in range(target_count):
                axis_value = start_axis + index * strict_spacing
                point = _segment_point(segment, axis_value, deterministic_normal_offset, boundary_margin)
                chosen.append(_placement_item(point, angle, unit_id))
                obstacles.append((Vector((point.x, point.y, 0.0)), min_distance))

    return chosen


# dA_5_add
def _surface_safe_point(point, candidate_samples, road_samples, obstacles, min_distance, min_road_distance):
    max_surface_distance = max(0.9, min_distance * 0.65)
    surface_distance = _nearest_distance(point, candidate_samples)
    road_distance = _nearest_distance(point, road_samples)

    if (
        surface_distance is not None
        and surface_distance <= max_surface_distance
        and (road_distance is None or road_distance >= min_road_distance)
        and _candidate_far_enough(point, obstacles, min_distance)
    ):
        return point

    nearest = sorted(
        candidate_samples,
        key=lambda sample: (Vector((point.x, point.y, 0.0)) - Vector((sample.x, sample.y, 0.0))).length,
    )
    for sample in nearest[:60]:
        road_distance = _nearest_distance(sample, road_samples)
        if road_distance is not None and road_distance < min_road_distance:
            continue
        if _candidate_far_enough(sample, obstacles, min_distance):
            return sample.copy()

    return None


# dA_5_add
def _surface_candidates(context, obj, asset):
    samples, road_samples = _evaluated_ground_samples(context, obj)
    if not samples:
        return []

    min_x = min(point.x for point in samples)
    max_x = max(point.x for point in samples)
    min_y = min(point.y for point in samples)
    max_y = max(point.y for point in samples)
    center = Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, 0.0))
    max_dx = (max_x - min_x) * 0.5
    max_dy = (max_y - min_y) * 0.5

    band_min, band_max = asset.get("street_band", (0.55, 0.95))

    candidates = []
    for sample in samples:
        band = _band_value(sample, center, max_dx, max_dy)
        road_distance = _nearest_distance(sample, road_samples)
        edge_end_score = min(
            abs(sample.x - min_x),
            abs(sample.x - max_x),
        ) + min(
            abs(sample.y - min_y),
            abs(sample.y - max_y),
        )

        if not (band_min <= band <= band_max):
            continue
        near_x_end = abs(sample.x - min_x) < max_dx * 0.22 or abs(sample.x - max_x) < max_dx * 0.22
        near_y_end = abs(sample.y - min_y) < max_dy * 0.22 or abs(sample.y - max_y) < max_dy * 0.22
        if near_x_end and near_y_end:
            continue

        if road_distance is not None:
            min_road_distance, max_road_distance = asset.get("road_distance", (1.0, 8.0))
            if not (min_road_distance <= road_distance <= max_road_distance):
                continue

        direction = Vector((sample.x - center.x, sample.y - center.y, 0.0))
        if direction.length < 0.001:
            direction = Vector((1.0, 0.0, 0.0))
        direction.normalize()

        tangent = Vector((-direction.y, direction.x, 0.0))
        angle = math.atan2(tangent.y, tangent.x)
        candidates.append((sample, angle, edge_end_score, band, road_distance or 9999.0))

    candidates.sort(key=lambda item: _surface_ring_key(item[0], min_x, max_x, min_y, max_y))

    return candidates


# dA_5_add
def _candidate_far_enough(point, obstacles, min_distance):
    point_2d = Vector((point.x, point.y, 0.0))
    for obstacle_point, obstacle_radius in obstacles:
        if (point_2d - obstacle_point).length < min_distance:
            return False
    return True


# dA_5_add
def _resolve_overlap(point, angle, obstacles, min_distance):
    if _candidate_far_enough(point, obstacles, min_distance):
        return point

    tangent = Vector((math.cos(angle), math.sin(angle), 0.0))
    normal = Vector((-tangent.y, tangent.x, 0.0))
    offsets = (
        tangent,
        -tangent,
        normal,
        -normal,
        tangent + normal,
        tangent - normal,
        -tangent + normal,
        -tangent - normal,
    )

    for multiplier in (0.7, 1.1, 1.6, 2.2):
        for offset in offsets:
            if offset.length < 0.001:
                continue
            moved = point + offset.normalized() * min_distance * multiplier
            if _candidate_far_enough(moved, obstacles, min_distance):
                return moved

    return None


# dA_5_add
def _naturalized_point(point, angle, index, spacing):
    rng = random.Random(index * 1009 + 9173)
    tangent = Vector((math.cos(angle), math.sin(angle), 0.0))
    normal = Vector((-tangent.y, tangent.x, 0.0))
    amount = max(0.12, min(float(spacing) * 0.12, 0.9))

    tangent_jitter = rng.uniform(-amount * 0.45, amount * 0.45)
    normal_jitter = rng.uniform(-amount * 0.25, amount * 0.25)
    angle_jitter = rng.uniform(-0.25, 0.25)

    moved = point + tangent * tangent_jitter + normal * normal_jitter
    return moved, angle + angle_jitter


# dA_5_add
def _unique_instance_name(asset_key, index):
    base_name = f"CG_{asset_key}_{index + 1:03d}"
    if base_name not in bpy.data.objects:
        return base_name

    suffix = 1
    while f"{base_name}_{suffix:02d}" in bpy.data.objects:
        suffix += 1
    return f"{base_name}_{suffix:02d}"


# dA_5_add
def _sample_from_surface(context, obj, asset, min_count, max_count, spacing, min_distance, randomize=False, placement_offset=0.0, boundary_margin=0.0):
    street_points = _street_edge_points(
        context,
        obj,
        asset,
        min_count,
        max_count,
        spacing,
        min_distance,
        randomize=randomize,
        placement_offset=placement_offset,
        boundary_margin=boundary_margin,
    )
    if street_points:
        return street_points

    candidates = _surface_candidates(context, obj, asset)
    if not candidates:
        return []

    _surface_samples, road_samples = _evaluated_ground_samples(context, obj)
    candidate_samples = [candidate[0] for candidate in candidates]
    min_road_distance, _max_road_distance = asset.get("road_distance", (1.0, 8.0))
    safe_road_distance = max(min_road_distance, min_distance * 0.55)

    if randomize:
        random.Random(271).shuffle(candidates)

    chosen = []
    obstacles = _existing_asset_obstacles(asset_id=None)
    step = max(1, int(max(1.0, float(spacing)) / 2.0)) if randomize else 1
    start_offset = 0
    previous_point = None

    fallback_count = max(1, int(max_count))
    while len(chosen) < fallback_count and start_offset < step:
        for index in range(start_offset, len(candidates), step):
            point, angle, _edge_end_score, _band, _road_distance = candidates[index]
            point = point.copy()
            if randomize:
                point, angle = _naturalized_point(point, angle, len(chosen), spacing)
            elif previous_point is not None and (Vector((point.x, point.y, 0.0)) - previous_point).length < float(spacing) * 0.92:
                continue

            moved = _resolve_overlap(point, angle, obstacles, min_distance)
            if moved is None:
                continue
            moved = _surface_safe_point(
                moved,
                candidate_samples,
                road_samples,
                obstacles,
                min_distance,
                safe_road_distance,
            )
            if moved is None:
                continue

            chosen.append((moved, angle))
            obstacles.append((Vector((moved.x, moved.y, 0.0)), min_distance))
            previous_point = Vector((moved.x, moved.y, 0.0))
            if len(chosen) >= fallback_count:
                break
        start_offset += 1

    return chosen


# dA_5_add
def _sample_rectangle_perimeter(min_x, max_x, min_y, max_y, z, count, spacing):
    width = max_x - min_x
    depth = max_y - min_y
    perimeter = 2.0 * (width + depth)
    step = max(0.1, float(spacing))
    points = []

    for index in range(max(1, int(count))):
        distance = (index * step) % perimeter
        if distance <= width:
            x = min_x + distance
            y = min_y
            angle = 0.0
        elif distance <= width + depth:
            x = max_x
            y = min_y + (distance - width)
            angle = math.pi / 2.0
        elif distance <= 2.0 * width + depth:
            x = max_x - (distance - width - depth)
            y = max_y
            angle = math.pi
        else:
            x = min_x
            y = max_y - (distance - 2.0 * width - depth)
            angle = -math.pi / 2.0

        points.append((Vector((x, y, z)), angle))

    return points


# dA_5_add
def _placement_points(context, obj, asset, min_count, max_count, spacing, min_distance, randomize=False, placement_offset=0.0, boundary_margin=0.0):
    surface_points = _sample_from_surface(
        context,
        obj,
        asset,
        min_count,
        max_count,
        spacing,
        min_distance,
        randomize=randomize,
        placement_offset=placement_offset,
        boundary_margin=boundary_margin,
    )
    if surface_points:
        return surface_points

    reference_points = _sample_from_street_references(
        context,
        obj,
        max_count,
        spacing,
        min_distance,
    )
    if reference_points:
        return reference_points

    min_x, max_x, min_y, max_y, min_z = _evaluated_world_bounds(context, obj)
    return _sample_rectangle_perimeter(min_x, max_x, min_y, max_y, min_z, max_count, spacing)


# dA_5_add
def _group_instances(group_id):
    return [
        obj
        for obj in bpy.data.objects
        if obj.get("cg_added_3d_asset_instance") and obj.get("cg_added_3d_group_id") == group_id
    ]


# dA_5_add
def selected_added_3d_group(context):
    active = context.object
    if active is None or not active.get("cg_added_3d_asset_instance"):
        return None

    group_id = active.get("cg_added_3d_group_id")
    if not group_id:
        return None

    instances = _group_instances(group_id)
    if not instances:
        return None

    return {
        "group_id": group_id,
        "asset_id": active.get("cg_added_3d_asset_id"),
        "asset_name": active.get("cg_added_3d_asset_name", active.get("cg_added_3d_asset_id")),
        "city_object_name": active.get("cg_added_3d_city_object"),
        "unit_id": active.get("cg_added_3d_group_unit_id", ""),
        "min_count": int(active.get("cg_added_3d_group_min_count", len(instances))),
        "max_count": int(active.get("cg_added_3d_group_max_count", len(instances))),
        "spacing": float(active.get("cg_added_3d_group_spacing", 5.0)),
        "scale": float(active.get("cg_added_3d_group_ui_scale", 1.0)),
        "placement_offset": float(active.get("cg_added_3d_group_placement_offset", 0.0)),
        "randomize": bool(active.get("cg_added_3d_group_randomize", False)),
        "instances": [obj.name for obj in instances],
    }


# dA_5_add
def apply_added_3d_asset(
    context,
    asset_id,
    min_count=3,
    max_count=6,
    spacing=10.0,
    scale=1.0,
    placement_offset=0.0,
    randomize=False,
    clear_previous=True,
    count=None,
    target_group_id=None,
    target_unit_id=None,
    city_object_name=None,
):
    asset_key = str(asset_id)
    asset = CITY_3D_ASSETS.get(asset_key)
    if asset is None:
        raise ValueError(f"3D asset '{asset_key}' does not exist.")

    obj = _get_city_object(context, object_name=city_object_name)
    source_collection = _ensure_source_collection(asset_key)
    generated_collection = _get_or_create_generated_collection(context)

    if clear_previous:
        _clear_generated_instances(asset_key, group_id=target_group_id, city_object_name=obj.name)

    source_bottom, source_radius, source_height = _source_collection_metrics(source_collection)
    instance_scale = max(0.01, float(scale)) * float(asset.get("default_scale", 1.0))
    placement_scale = float(asset.get("default_scale", 1.0))
    min_distance = max(float(spacing), 0.1)
    boundary_margin = max(0.05, source_radius * instance_scale)
    if count is not None:
        min_count = count
        max_count = count
    min_count = max(0, int(min_count))
    max_count = max(min_count, int(max_count))
    points = _placement_points(
        context,
        obj,
        asset,
        min_count,
        max_count,
        float(spacing),
        min_distance,
        randomize=bool(randomize),
        placement_offset=float(placement_offset),
        boundary_margin=boundary_margin,
    )
    created = []
    batch_id = (
        str(target_group_id).split("|batch|", 1)[1].split("|", 1)[0]
        if target_group_id is not None and "|batch|" in str(target_group_id)
        else f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    )

    for index, item in enumerate(points):
        location, angle, unit_id = _unpack_placement_item(item, target_unit_id)
        if unit_id is None:
            unit_id = f"street_edge|fallback|{index}"
        if target_unit_id is not None and unit_id != target_unit_id:
            continue
        group_id = target_group_id or f"{obj.name}|{asset_key}|batch|{batch_id}|{unit_id}"

        instance = bpy.data.objects.new(_unique_instance_name(asset_key, index), None)
        instance.empty_display_type = "CUBE"
        instance.empty_display_size = max(0.2, 1.0 / instance_scale)
        instance.instance_type = "COLLECTION"
        instance.instance_collection = source_collection
        z_lift = float(asset.get("z_lift", 0.05))
        instance.location = (location.x, location.y, location.z - source_bottom * instance_scale + z_lift)
        instance.rotation_euler = (0.0, 0.0, angle)
        instance.scale = (instance_scale, instance_scale, instance_scale)
        instance["cg_added_3d_asset_instance"] = True
        instance["cg_added_3d_asset_id"] = asset_key
        instance["cg_added_3d_asset_name"] = asset["label"]
        instance["cg_added_3d_city_object"] = obj.name
        instance["cg_added_3d_group_id"] = group_id
        instance["cg_added_3d_group_unit_id"] = unit_id
        instance["cg_added_3d_batch_id"] = batch_id
        instance["cg_added_3d_group_min_count"] = min_count
        instance["cg_added_3d_group_max_count"] = max_count
        instance["cg_added_3d_group_spacing"] = float(spacing)
        instance["cg_added_3d_group_ui_scale"] = max(0.01, float(scale))
        instance["cg_added_3d_group_placement_offset"] = float(placement_offset)
        instance["cg_added_3d_group_randomize"] = bool(randomize)
        instance["cg_added_3d_asset_radius"] = boundary_margin
        instance["cg_added_3d_asset_height"] = source_height * instance_scale
        generated_collection.objects.link(instance)
        created.append(instance.name)

    context.view_layer.update()
    if target_group_id is not None and created:
        bpy.ops.object.select_all(action="DESELECT")
        for name in created:
            created_obj = bpy.data.objects.get(name)
            if created_obj is not None:
                created_obj.select_set(True)
        active_created = bpy.data.objects.get(created[0])
        if active_created is not None:
            context.view_layer.objects.active = active_created

    return {
        "asset_id": asset_key,
        "asset_name": asset["label"],
        "count": len(created),
        "min_count": min_count,
        "max_count": max_count,
        "spacing": float(spacing),
        "scale": instance_scale,
        "placement_offset": float(placement_offset),
        "randomize": bool(randomize),
        "collection_name": source_collection.name,
        "instances": created,
    }


# dA_5_add
def apply_added_3d_asset_function(
    context,
    asset_id,
    min_count=3,
    max_count=6,
    spacing=10.0,
    scale=1.0,
    placement_offset=0.0,
    randomize=False,
    clear_previous=True,
    count=None,
):
    """Callable wrapper for LLM/backend/frontend bridge."""
    return apply_added_3d_asset(
        context,
        asset_id,
        min_count=min_count,
        max_count=max_count,
        spacing=spacing,
        scale=scale,
        placement_offset=placement_offset,
        randomize=randomize,
        clear_previous=clear_previous,
        count=count,
    )


# dA_5_add
def reapply_selected_added_3d_group(
    context,
    min_count=None,
    max_count=None,
    spacing=None,
    scale=None,
    placement_offset=None,
):
    group = selected_added_3d_group(context)
    if group is None:
        raise ValueError("Select one generated 3D asset instance first.")

    return apply_added_3d_asset(
        context,
        group["asset_id"],
        min_count=group["min_count"] if min_count is None else min_count,
        max_count=group["max_count"] if max_count is None else max_count,
        spacing=group["spacing"] if spacing is None else spacing,
        scale=group["scale"] if scale is None else scale,
        placement_offset=group["placement_offset"] if placement_offset is None else placement_offset,
        randomize=group["randomize"],
        clear_previous=True,
        target_group_id=group["group_id"],
        target_unit_id=group["unit_id"],
        city_object_name=group["city_object_name"],
    )
