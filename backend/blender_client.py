"""Blender CLI driver — dispatches tasks to the Blender plugin.

Uses blender --background --python to run plugin operations.
In production, this would connect to a running Blender instance via socket.
For now, tasks are logged and can be executed manually in Blender.
"""

import json
import subprocess
import uuid
from pathlib import Path

from .schemas import Task

BLENDER_EXE = None  # Set to blender executable path, e.g. r"D:\blender-4.1.0\blender.exe"
PLUGIN_DIR = Path(__file__).resolve().parent.parent / "LLMCityGenerator"


def dispatch_task(task: Task):
    """Execute a Blender plugin operation for the given task.

    In development mode, prints the task and saves a script that can be
    run manually in Blender's Python console.
    """
    script = _build_script(task)
    print(f"[blender_client] Task {task.id}: {task.functionName}")
    print(f"  Script: {script[:200]}...")

    if BLENDER_EXE and Path(BLENDER_EXE).exists():
        try:
            result = subprocess.run(
                [BLENDER_EXE, "--background", "--python-expr", script],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                print(f"  Success: {result.stdout[:200]}")
            else:
                print(f"  Error: {result.stderr[:200]}")
        except Exception as e:
            print(f"  Exception: {e}")
    else:
        # Save script for manual execution in Blender
        script_path = PLUGIN_DIR.parent / f"_task_{task.id}.py"
        script_path.write_text(script, encoding="utf-8")
        print(f"  Script saved to: {script_path}")


def _build_script(task: Task) -> str:
    """Build a Python script that executes the task in Blender."""
    function_name = task.functionName
    params = task.params

    return f'''
import bpy
import sys
sys.path.insert(0, r"{PLUGIN_DIR.parent}")

from LLMCityGenerator.function_registry import execute_function

# Ensure a context object exists
obj = bpy.context.object
if obj and obj.modifiers and "City_Generator_2.0" in obj.modifiers:
    pass
else:
    print("Warning: No active object with City_Generator_2.0 modifier")

result = execute_function("{function_name}", {json.dumps(params)}, bpy.context)
print("Task result:", result)
'''
