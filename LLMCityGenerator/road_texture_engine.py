import os
import bpy

from .constants import (
    ADDON_DIR,
    PAVEMENT_MATERIAL_SOCKET,
    PAVEMENT_TEXTURE_ASSETS,
    PAVEMENT_UV_SCALE_SOCKET,
    ROAD_MATERIAL_SOCKET,
    ROAD_TEXTURE_ASSETS,
    ROAD_UV_SCALE_SOCKET,
)
from .template_engine import get_city_generator_modifier, set_modifier_socket


def _asset_path(relative_path):
    return os.path.join(ADDON_DIR, relative_path)


def _load_image(relative_path):
    if not relative_path:
        return None

    path = _asset_path(relative_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Texture file not found: {path}")

    image = bpy.data.images.get(os.path.basename(path))
    if image is None:
        image = bpy.data.images.load(path)

    return image


def _new_image_node(nodes, image, location):
    node = nodes.new(type="ShaderNodeTexImage")
    node.image = image
    node.location = location
    return node


def _create_texture_material(texture):
    mat = bpy.data.materials.get(texture["material_name"])
    if mat is None:
        mat = bpy.data.materials.new(texture["material_name"])

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (500, 0)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (250, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    base_image = _load_image(texture["base_color"])
    base_node = _new_image_node(nodes, base_image, (-550, 120))
    links.new(base_node.outputs["Color"], bsdf.inputs["Base Color"])

    roughness_image = _load_image(texture.get("roughness"))
    if roughness_image is not None:
        roughness_node = _new_image_node(nodes, roughness_image, (-550, -120))
        roughness_node.image.colorspace_settings.name = "Non-Color"
        links.new(roughness_node.outputs["Color"], bsdf.inputs["Roughness"])
    else:
        bsdf.inputs["Roughness"].default_value = 0.65

    normal_image = _load_image(texture.get("normal"))
    if normal_image is not None:
        normal_tex_node = _new_image_node(nodes, normal_image, (-750, -320))
        normal_tex_node.image.colorspace_settings.name = "Non-Color"

        normal_map_node = nodes.new(type="ShaderNodeNormalMap")
        normal_map_node.location = (-300, -300)
        normal_map_node.inputs["Strength"].default_value = 0.45

        links.new(normal_tex_node.outputs["Color"], normal_map_node.inputs["Color"])
        links.new(normal_map_node.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def create_road_texture_material(texture_id):
    texture = ROAD_TEXTURE_ASSETS.get(str(texture_id))
    if texture is None:
        raise ValueError(f"Road texture '{texture_id}' does not exist.")

    return _create_texture_material(texture)


def create_pavement_texture_material(texture_id):
    texture = PAVEMENT_TEXTURE_ASSETS.get(str(texture_id))
    if texture is None:
        raise ValueError(f"Pavement texture '{texture_id}' does not exist.")

    return _create_texture_material(texture)


def apply_road_texture(context, texture_id):
    texture_key = str(texture_id)
    texture = ROAD_TEXTURE_ASSETS.get(texture_key)
    if texture is None:
        raise ValueError(f"Road texture '{texture_key}' does not exist.")

    mod = get_city_generator_modifier(context)
    warnings = []
    applied = []

    material = create_road_texture_material(texture_key)
    set_modifier_socket(
        mod,
        ROAD_MATERIAL_SOCKET,
        material,
        "road_material",
        applied,
        warnings,
    )

    if ROAD_UV_SCALE_SOCKET in mod.keys():
        set_modifier_socket(
            mod,
            ROAD_UV_SCALE_SOCKET,
            texture["uv_scale"],
            "road_uv_scale",
            applied,
            warnings,
        )

    mod.show_viewport = False
    context.view_layer.update()
    mod.show_viewport = True
    context.view_layer.update()

    return {
        "texture_id": texture_key,
        "texture_name": texture["label"],
        "material_name": material.name,
        "applied": applied,
        "warnings": warnings,
    }


def apply_road_texture_function(context, texture_id):
    """Callable wrapper for LLM/backend/frontend bridge."""
    return apply_road_texture(context, str(texture_id))


def apply_pavement_texture(context, texture_id):
    texture_key = str(texture_id)
    texture = PAVEMENT_TEXTURE_ASSETS.get(texture_key)
    if texture is None:
        raise ValueError(f"Pavement texture '{texture_key}' does not exist.")

    mod = get_city_generator_modifier(context)
    warnings = []
    applied = []

    material = create_pavement_texture_material(texture_key)
    set_modifier_socket(
        mod,
        PAVEMENT_MATERIAL_SOCKET,
        material,
        "pavement_material",
        applied,
        warnings,
    )

    if PAVEMENT_UV_SCALE_SOCKET in mod.keys():
        set_modifier_socket(
            mod,
            PAVEMENT_UV_SCALE_SOCKET,
            texture["uv_scale"],
            "pavement_uv_scale",
            applied,
            warnings,
        )

    mod.show_viewport = False
    context.view_layer.update()
    mod.show_viewport = True
    context.view_layer.update()

    return {
        "texture_id": texture_key,
        "texture_name": texture["label"],
        "material_name": material.name,
        "applied": applied,
        "warnings": warnings,
    }


def apply_pavement_texture_function(context, texture_id):
    """Callable wrapper for LLM/backend/frontend bridge."""
    return apply_pavement_texture(context, str(texture_id))
