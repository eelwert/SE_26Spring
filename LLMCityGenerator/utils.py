import os
import bpy
from .constants import ADDON_DIR, BLEND_FILE


def append_data(directory, filename):
    """Appends data from a blend file."""
    path = os.path.join(ADDON_DIR, BLEND_FILE, directory)
    bpy.ops.wm.append(directory=path, filename=filename, autoselect=True)


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
