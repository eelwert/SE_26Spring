import os
import bpy
from .constants import ADDON_DIR, BLEND_FILE


# Mapping from blend-file datablock folder names to bpy.data.libraries.load attribute names
_DATA_TYPE_MAP = {
    "Object": "objects",
    "NodeTree": "node_groups",
    "Material": "materials",
    "Collection": "collections",
    "Action": "actions",
    "Image": "images",
    "Texture": "textures",
    "Mesh": "meshes",
    "Scene": "scenes",
    "World": "worlds",
}


def append_data(directory, filename):
    """Appends a datablock from the bundled .blend resource file.

    Uses bpy.data.libraries.load() to avoid context-restriction issues
    that bpy.ops.wm.append suffers from in newer Blender versions.

    Loaded Objects and Collections are also linked to the active scene.
    """
    blend_path = os.path.join(ADDON_DIR, BLEND_FILE)
    attr = _DATA_TYPE_MAP.get(directory)
    if attr is None:
        raise TypeError(f"Unsupported datablock type '{directory}'")

    with bpy.data.libraries.load(str(blend_path), link=False) as (data_from, data_to):
        setattr(data_to, attr, [filename])

    # Newly loaded datablock is now in bpy.data.<collection> — link to scene if needed
    scene = bpy.context.scene
    if attr == "objects":
        obj = bpy.data.objects.get(filename)
        if obj and obj.name not in scene.collection.objects:
            scene.collection.objects.link(obj)
    elif attr == "collections":
        coll = bpy.data.collections.get(filename)
        if coll and coll.name not in scene.collection.children:
            scene.collection.children.link(coll)


def get_or_create_attribute(mesh, name, attr_type, domain):
    """Gets or creates a custom attribute on the given mesh."""
    if name not in mesh.attributes:
        mesh.attributes.new(name=name, type=attr_type, domain=domain)
    return mesh.attributes[name]


def find_layer_collection(layer_collection, collection_name):
    """Recursively find a layer collection by name."""
    if layer_collection.name == collection_name:
        return layer_collection
    for child in layer_collection.children:
        result = find_layer_collection(child, collection_name)
        if result:
            return result
    return None
