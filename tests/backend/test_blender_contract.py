from pathlib import Path

from backend import blender_client


ROOT = Path(__file__).resolve().parents[2]


def test_blender_manifest_declares_addon_and_supported_version():
    manifest = (ROOT / "LLMCityGenerator" / "blender_manifest.toml").read_text(encoding="utf-8")

    assert 'id = "LLMCityGenerator"' in manifest
    assert 'type = "add-on"' in manifest
    assert 'blender_version_min = "4.3.0"' in manifest


def test_generated_blender_script_calls_plugin_function_registry():
    task = type(
        "TaskStub",
        (),
        {
            "functionName": "set_street_width",
            "params": {"width": 10},
        },
    )()

    script = blender_client._build_script(task)

    assert "import bpy" in script
    assert "from LLMCityGenerator.function_registry import execute_function" in script
    assert 'execute_function("set_street_width", {"width": 10}, bpy.context)' in script


def test_plugin_register_starts_backend_sync():
    init_py = (ROOT / "LLMCityGenerator" / "__init__.py").read_text(encoding="utf-8")

    assert "from .blender_sync import start_sync, stop_sync" in init_py
    assert "start_sync()" in init_py
