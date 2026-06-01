
import bpy
import sys
sys.path.insert(0, r"C:\Users\CHDN\Desktop\SE\SE_26Spring")

from LLMCityGenerator.function_registry import execute_function

# Ensure a context object exists
obj = bpy.context.object
if obj and obj.modifiers and "City_Generator_2.0" in obj.modifiers:
    pass
else:
    print("Warning: No active object with City_Generator_2.0 modifier")

result = execute_function("solve_point_layout", {"scope": "current_scene", "dry_run": false}, bpy.context)
print("Task result:", result)
