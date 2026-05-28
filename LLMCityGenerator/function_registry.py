from .constants import SCENE_TEMPLATES
from .template_engine import apply_scene_template_function


def _template_enum():
    return list(SCENE_TEMPLATES.keys())


LLM_FUNCTION_SPECS = {
    "apply_scene_template": {
        "name": "apply_scene_template",
        "description": (
            "Apply a predefined city scene detail template to the active Blender City Generator object. "
            "The template changes coordinated scene details such as road material, tree type, sidewalk assets, "
            "tree spacing, and street-side furniture settings."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "enum": _template_enum(),
                    "description": "Template id. Use 0 for Waterfront Block, 1 for Commercial Street, 2 for Transit Hub.",
                }
            },
            "required": ["template_id"],
        },
        "returns": {
            "type": "object",
            "description": "Execution result containing template_id, template_name, applied fields, and warnings.",
        },
    }
}


LLM_FUNCTION_HANDLERS = {
    "apply_scene_template": apply_scene_template_function,
}


def get_llm_function_specs():
    """Return function specs that can be sent to the LLM."""
    return list(LLM_FUNCTION_SPECS.values())


def call_llm_function(context, function_name, arguments):
    """Dispatch an LLM-selected function call to the matching Blender implementation."""
    handler = LLM_FUNCTION_HANDLERS.get(function_name)
    if handler is None:
        raise ValueError(f"Unknown LLM function: {function_name}")

    if arguments is None:
        arguments = {}

    return handler(context, **arguments)