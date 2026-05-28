import bpy
from bpy.utils import register_class, unregister_class

from .operators import (
    CG_OT_Import_Node_Group,
    CG_OT_Apply_Node_Group,
    CG_OT_Duplicate_Object,
    MESH_OT_SetLowPolyAttribute,
    MESH_OT_AddParkAttribute,
    MESH_OT_Add_Intersection_Grid,
    MESH_OT_Delete_CrossWalk,
    MESH_OT_Add_Bus_Lane,
    MESH_OT_delete_Trees_Edge,
    MESH_OT_SetmodernBuildingAttribute,
    MESH_OT_DeleteBuildingAttribute,
    CG_OT_AddDynamicElements,
    CG_OT_RemoveDynamicElements,
    CG_OT_PreviewPointLayout,
    CG_OT_ApplyPointLayout,
    CG_OT_ApplySketchLayout,
)
from .panels import (
    CG_PT_Main_Panel,
    CG_Setting_Panel,
    CG_General_Setting_Panel,
    CG_Street_Setting_Panel,
    CG_Park_Setting_Panel,
    CG_Street_Adv_Setting_Panel,
    CG_Traffic_Sim_Panel,
    CG_Building_Panel,
    CG_Building_Advanced_Panel,
    CG_Building_Asset_distribution_Panel,
    CG_Building_Floor_Plan_Shape_Panel,
    CG_Building_Additional_Assets_Panel,
    CG_Building_Roof_Panel,
    CG_Night_Lighting_Panel,
    InteriorPanel,
    CG_PT_Dynamics_Panel,
    CG_PT_Layout_Panel,
)
from .properties import register_scene_properties, unregister_scene_properties
from .handlers import register_handlers, unregister_handlers


bl_info = {
    "name": "The City Generator vx:dalipig",
    "blender": (4, 3, 0),
    "category": "Object",
    "description": "An add-on to generate a City",
    "author": "Andreas Dürr",
    "version": (2, 8, 0),
    "location": "View3D > Sidebar > LLM City Generator",
}


classes = [
    CG_OT_Import_Node_Group,
    CG_OT_Apply_Node_Group,
    CG_PT_Main_Panel,
    CG_Setting_Panel,
    CG_General_Setting_Panel,
    CG_Street_Setting_Panel,
    CG_Park_Setting_Panel,
    CG_Street_Adv_Setting_Panel,
    CG_OT_Duplicate_Object,
    CG_Traffic_Sim_Panel,
    CG_Night_Lighting_Panel,
    CG_Building_Panel,
    CG_Building_Advanced_Panel,
    CG_Building_Asset_distribution_Panel,
    CG_Building_Floor_Plan_Shape_Panel,
    CG_Building_Additional_Assets_Panel,
    CG_Building_Roof_Panel,
    MESH_OT_SetLowPolyAttribute,
    MESH_OT_SetmodernBuildingAttribute,
    MESH_OT_DeleteBuildingAttribute,
    MESH_OT_AddParkAttribute,
    MESH_OT_Add_Intersection_Grid,
    MESH_OT_Delete_CrossWalk,
    MESH_OT_Add_Bus_Lane,
    MESH_OT_delete_Trees_Edge,
    InteriorPanel,
    CG_OT_AddDynamicElements,
    CG_OT_RemoveDynamicElements,
    CG_PT_Dynamics_Panel,
    CG_OT_PreviewPointLayout,
    CG_OT_ApplyPointLayout,
    CG_OT_ApplySketchLayout,
    CG_PT_Layout_Panel,
]


def register():
    for cls in classes:
        register_class(cls)

    register_scene_properties()
    register_handlers()


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)

    unregister_handlers()
    unregister_scene_properties()


if __name__ == "__main__":
    register()
