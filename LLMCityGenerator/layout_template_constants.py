LAYOUT_TEMPLATE_ASSETS = {
    "linear_blocks": {
        "label": "Linear Blocks",
        "description": "Create independent default-sized city blocks side by side for layout experiments.",
        "block_width": 56.9820175,
        "block_depth": 56.9820175,
        "block_gap": 15.098793,
    },
}


LAYOUT_TEMPLATE_ENUM_ITEMS = tuple(
    (layout_id, layout["label"], layout["description"])
    for layout_id, layout in LAYOUT_TEMPLATE_ASSETS.items()
)
