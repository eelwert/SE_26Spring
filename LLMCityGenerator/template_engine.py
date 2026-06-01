import bpy

from .constants import SCENE_TEMPLATES, TEMPLATE_SOCKET_MAP


def get_city_generator_modifier(context):
    obj = context.object
    if not obj:
        raise ValueError("No active object selected.")

    mod = obj.modifiers.get("City_Generator_2.0")
    if not mod:
        raise ValueError("Active object does not have City_Generator_2.0 modifier.")

    return mod


def ensure_material(name, color):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = color
    return mat


def find_collection(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if collection is not None:
        return collection

    return next(
        (item for item in bpy.data.collections if item.name.strip() == collection_name.strip()),
        None,
    )


def ensure_collection_from_objects(collection_name, object_names, warnings):
    collection = find_collection(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)

    desired_names = set()
    for object_name in object_names:
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            warnings.append(f"{collection_name}: object '{object_name}' not found.")
            continue

        copy_name = f"{collection_name}_{object_name}"
        desired_names.add(copy_name)
        copy_obj = bpy.data.objects.get(copy_name)
        if copy_obj is None:
            copy_obj = obj.copy()
            copy_obj.data = obj.data
            copy_obj.animation_data_clear()
            copy_obj.name = copy_name

        copy_obj.location = (0.0, 0.0, 0.0)
        copy_obj.rotation_euler = (0.0, 0.0, 0.0)
        copy_obj.scale = (1.0, 1.0, 1.0)

        if copy_obj.name not in collection.objects.keys():
            collection.objects.link(copy_obj)

    for existing_obj in list(collection.objects):
        if existing_obj.name not in desired_names:
            collection.objects.unlink(existing_obj)

    return collection


def set_modifier_socket(mod, socket_id, value, label, applied, warnings):
    if not socket_id:
        warnings.append(f"{label}: socket is not configured.")
        return

    if socket_id not in mod.keys():
        warnings.append(f"{label}: {socket_id} not found on modifier.")
        return

    try:
        mod[socket_id] = value
        applied.append(label)
    except Exception as exc:
        warnings.append(f"{label}: failed to set {socket_id}: {exc}")


def set_collection_socket(mod, socket_id, collection_name, label, applied, warnings, object_names=None):
    if not collection_name:
        warnings.append(f"{label}: collection name is empty, skipped.")
        return

    if object_names:
        collection = ensure_collection_from_objects(collection_name, object_names, warnings)
    else:
        collection = find_collection(collection_name)

    if collection is None:
        warnings.append(f"{label}: collection '{collection_name}' not found.")
        return

    set_modifier_socket(mod, socket_id, collection, label, applied, warnings)


def apply_scene_template(context, template_id):
    template_key = str(template_id)
    template = SCENE_TEMPLATES.get(template_key)
    if template is None:
        raise ValueError(f"Scene template '{template_key}' does not exist.")

    mod = get_city_generator_modifier(context)
    applied = []
    warnings = []

    numeric_keys = [
        "road_width",
        "lane_amount",
        "sidewalk_scale",
        "tree_distance",
        "tree_min_scale",
        "tree_max_scale",
        "sidewalk_asset_probability",
        "sidewalk_asset_distance",
    ]

    for key in numeric_keys:
        set_modifier_socket(
            mod,
            TEMPLATE_SOCKET_MAP.get(key),
            template[key],
            key,
            applied,
            warnings,
        )

    road_material = ensure_material(template["road_material"], template["road_color"])
    set_modifier_socket(
        mod,
        TEMPLATE_SOCKET_MAP.get("road_material"),
        road_material,
        "road_material",
        applied,
        warnings,
    )

    set_collection_socket(
        mod,
        TEMPLATE_SOCKET_MAP.get("tree_collection"),
        template.get("tree_collection"),
        "tree_collection",
        applied,
        warnings,
        object_names=template.get("tree_objects"),
    )

    set_collection_socket(
        mod,
        TEMPLATE_SOCKET_MAP.get("sidewalk_asset_collection"),
        template.get("sidewalk_asset_collection"),
        "sidewalk_asset_collection",
        applied,
        warnings,
    )

    # context.view_layer.update()

    mod.show_viewport = False
    context.view_layer.update()
    mod.show_viewport = True
    context.view_layer.update()

    return {
        "template_id": template_key,
        "template_name": template["label"],
        "applied": applied,
        "warnings": warnings,
    }




# LLM可调用的函数入口
def apply_scene_template_function(context, template_id):
    """LLM-callable wrapper for applying a predefined scene template.

    Args:
        context: Blender context. The active object must have City_Generator_2.0 modifier.
        template_id: Template id defined in constants.SCENE_TEMPLATES, such as "0", "1", "2".

    Returns:
        dict: Structured execution result for UI, LLM, logging, or frontend callback.
    """
    return apply_scene_template(context, str(template_id))