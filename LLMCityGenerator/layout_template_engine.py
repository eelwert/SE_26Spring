import bpy
import random

from .constants import SCENE_TEMPLATES, TEMPLATE_SOCKET_MAP
from .layout_template_constants import LAYOUT_TEMPLATE_ASSETS
from .template_engine import ensure_material, set_collection_socket, set_modifier_socket
from .utils import append_data, find_layer_collection


LAYOUT_GENERATED_FLAG = "cg_layout_template_object"
CITY_NODE_GROUP_NAME = "City_Generator_2.0"
ASSETS_COLLECTION_NAME = "City_Gen_2.0_Assets"
DEFAULT_CITY_OBJECT_NAME = "City_Generator_2.0_Object"


def _ensure_city_node_group():
    if CITY_NODE_GROUP_NAME not in bpy.data.node_groups:
        append_data("NodeTree", CITY_NODE_GROUP_NAME)

    node_group = bpy.data.node_groups.get(CITY_NODE_GROUP_NAME)
    if node_group is None:
        raise ValueError(f"Node group '{CITY_NODE_GROUP_NAME}' could not be loaded.")
    return node_group


def _hide_assets_collection(context):
    layer_collection = find_layer_collection(context.view_layer.layer_collection, ASSETS_COLLECTION_NAME)
    if layer_collection is not None:
        layer_collection.exclude = True


def _clear_previous_layout_objects():
    for obj in list(bpy.data.objects):
        if obj.get(LAYOUT_GENERATED_FLAG):
            bpy.data.objects.remove(obj, do_unlink=True)


def _remove_default_city_object():
    default_obj = bpy.data.objects.get(DEFAULT_CITY_OBJECT_NAME)
    if default_obj is None or default_obj.get(LAYOUT_GENERATED_FLAG):
        return

    if CITY_NODE_GROUP_NAME not in default_obj.modifiers:
        return

    bpy.data.objects.remove(default_obj, do_unlink=True)


def _unique_name(base_name, data_block):
    if base_name not in data_block:
        return base_name

    suffix = 1
    while f"{base_name}_{suffix:02d}" in data_block:
        suffix += 1
    return f"{base_name}_{suffix:02d}"


def _build_single_block_mesh(layout, index):
    width = float(layout["block_width"])
    depth = float(layout["block_depth"])
    min_x = -width * 0.5
    max_x = width * 0.5
    min_y = -depth * 0.5
    max_y = depth * 0.5

    vertices = (
        (min_x, min_y, 0.0),
        (max_x, min_y, 0.0),
        (min_x, max_y, 0.0),
        (max_x, max_y, 0.0),
    )
    faces = ((0, 1, 3, 2),)

    mesh_name = _unique_name(f"CG_Layout_Block_{index + 1:02d}_Mesh", bpy.data.meshes)
    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    _ensure_default_face_attributes(mesh)
    return mesh


def _ensure_default_face_attributes(mesh):
    defaults = {
        "assign Park": 0,
        "Delete Building": 0,
        "modern building": 0,
        "low poly": 0,
    }

    for name, value in defaults.items():
        if name not in mesh.attributes:
            mesh.attributes.new(name=name, type="INT", domain="FACE")
        for item in mesh.attributes[name].data:
            item.value = value


def _apply_random_block_style(modifier, index, count, rng):
    template_key = rng.choice(tuple(SCENE_TEMPLATES.keys()))
    template = SCENE_TEMPLATES[template_key]
    applied = []
    warnings = []

    numeric_keys = (
        "road_width",
        "lane_amount",
        "sidewalk_scale",
        "tree_distance",
        "tree_min_scale",
        "tree_max_scale",
        "sidewalk_asset_probability",
        "sidewalk_asset_distance",
    )
    for key in numeric_keys:
        value = template[key]
        if isinstance(value, (int, float)):
            value = value * rng.uniform(0.88, 1.12)
        if key == "lane_amount":
            value = max(1, int(round(value)))

        set_modifier_socket(
            modifier,
            TEMPLATE_SOCKET_MAP.get(key),
            value,
            key,
            applied,
            warnings,
        )

    road_material = ensure_material(template["road_material"], template["road_color"])
    set_modifier_socket(
        modifier,
        TEMPLATE_SOCKET_MAP.get("road_material"),
        road_material,
        "road_material",
        applied,
        warnings,
    )
    set_collection_socket(
        modifier,
        TEMPLATE_SOCKET_MAP.get("tree_collection"),
        template.get("tree_collection"),
        "tree_collection",
        applied,
        warnings,
        object_names=template.get("tree_objects"),
    )
    set_collection_socket(
        modifier,
        TEMPLATE_SOCKET_MAP.get("sidewalk_asset_collection"),
        template.get("sidewalk_asset_collection"),
        "sidewalk_asset_collection",
        applied,
        warnings,
    )

    demo_height_min = float(modifier.get("Socket_112", 28.0))
    demo_height_max = float(modifier.get("Socket_113", 60.0))
    height_cap = max(demo_height_max, demo_height_max * 1.5)
    random_min_height = rng.uniform(max(1.0, demo_height_min * 0.75), max(2.0, demo_height_min * 1.05))
    random_max_low = max(random_min_height + 8.0, demo_height_max * 0.75)
    random_max_high = min(height_cap, max(random_max_low, demo_height_max * 1.25))

    building_variants = {
        "Socket_112": random_min_height,
        "Socket_113": rng.uniform(random_max_low, random_max_high),
        "Socket_114": rng.randint(1, 9999),
        "Socket_116": rng.randint(1, 9999),
        "Socket_118": rng.randint(1, 9999),
        "Socket_122": True,
        "Socket_123": rng.uniform(0.25, 0.65),
        "Socket_124": rng.randint(1, 9999),
        "Socket_125": rng.randint(1, 3),
        "Socket_126": rng.uniform(0.12, 0.42),
    }
    for socket_id, value in building_variants.items():
        if socket_id in modifier.keys():
            current_value = modifier[socket_id]
            if isinstance(current_value, bool):
                modifier[socket_id] = bool(value)
            elif isinstance(current_value, int):
                modifier[socket_id] = int(round(value))
            elif isinstance(current_value, float):
                modifier[socket_id] = float(value)
            else:
                modifier[socket_id] = value

    modifier["cg_layout_random_style_template"] = template_key


def _create_layout_objects(context, layout_id, layout, rows, columns):
    node_group = _ensure_city_node_group()
    _remove_default_city_object()
    bpy.ops.object.select_all(action="DESELECT")
    row_count = max(1, int(rows))
    column_count = max(1, int(columns))
    count = row_count * column_count
    pitch_x = float(layout["block_width"]) + float(layout["block_gap"])
    pitch_y = float(layout["block_depth"]) + float(layout["block_gap"])
    start_x = -((column_count - 1) * pitch_x) * 0.5
    start_y = -((row_count - 1) * pitch_y) * 0.5
    objects = []

    for index in range(count):
        mesh = _build_single_block_mesh(layout, index)
        row_index = index // column_count
        column_index = index % column_count
        object_name = _unique_name(f"CG_Layout_Block_R{row_index + 1:02d}_C{column_index + 1:02d}", bpy.data.objects)
        obj = bpy.data.objects.new(object_name, mesh)
        obj.location.x = start_x + column_index * pitch_x
        obj.location.y = start_y + row_index * pitch_y
        obj[LAYOUT_GENERATED_FLAG] = True
        obj["cg_layout_template_id"] = layout_id
        obj["cg_layout_block_count"] = count
        obj["cg_layout_rows"] = row_count
        obj["cg_layout_columns"] = column_count
        obj["cg_layout_block_index"] = index + 1
        obj["cg_layout_keeps_demo_style"] = index == 0

        context.scene.collection.objects.link(obj)
        modifier = obj.modifiers.new(type="NODES", name=CITY_NODE_GROUP_NAME)
        modifier.node_group = node_group
        if index > 0:
            _apply_random_block_style(modifier, index, count, random.Random(random.SystemRandom().randint(1, 2**31 - 1)))
        objects.append(obj)

    if objects:
        objects[0].select_set(True)
        context.view_layer.objects.active = objects[0]

    _hide_assets_collection(context)
    context.view_layer.update()
    return objects


def apply_layout_template(
    context,
    layout_id="linear_blocks",
    rows=1,
    columns=2,
    clear_previous=True,
    block_count=None,
):
    layout_key = str(layout_id)
    layout = LAYOUT_TEMPLATE_ASSETS.get(layout_key)
    if layout is None:
        raise ValueError(f"Layout template '{layout_key}' does not exist.")

    if block_count is not None:
        rows = 1
        columns = block_count

    rows = max(1, min(6, int(rows)))
    columns = max(1, min(6, int(columns)))
    block_count = rows * columns
    if clear_previous:
        _clear_previous_layout_objects()

    objects = _create_layout_objects(context, layout_key, layout, rows, columns)
    object_names = [obj.name for obj in objects]
    mesh_names = [obj.data.name for obj in objects]

    return {
        "layout_id": layout_key,
        "layout_name": layout["label"],
        "block_count": block_count,
        "rows": rows,
        "columns": columns,
        "object_name": object_names[0] if object_names else None,
        "mesh_name": mesh_names[0] if mesh_names else None,
        "object_names": object_names,
        "mesh_names": mesh_names,
        "active_object": object_names[0] if object_names else None,
        "clear_previous": bool(clear_previous),
    }


def apply_layout_template_function(
    context,
    layout_id="linear_blocks",
    rows=1,
    columns=2,
    clear_previous=True,
    block_count=None,
):
    """Callable wrapper for LLM/backend/frontend bridge."""
    return apply_layout_template(
        context,
        layout_id=str(layout_id),
        rows=rows,
        columns=columns,
        clear_previous=clear_previous,
        block_count=block_count,
    )
