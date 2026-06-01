import bpy

from ..constants import PAVEMENT_TEXTURE_ASSETS, ROAD_TEXTURE_ASSETS


class CG_Texture_2D_Panel(bpy.types.Panel):
    bl_label = "Added 2D Texture"
    bl_idname = "CG_Texture_2D_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Setting_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Added road and pavement texture assets.")


class CG_Road_Texture_Panel(bpy.types.Panel):
    bl_label = "Road Texture"
    bl_idname = "CG_Road_Texture_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Texture_2D_Panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.prop(scene, "road_texture_id", text="Texture")

        texture = ROAD_TEXTURE_ASSETS.get(scene.road_texture_id)
        if texture:
            box.label(text=texture["label"])

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.apply_road_texture", text="Apply Road Texture", icon="TEXTURE")

        obj = context.object
        if not obj or not obj.modifiers.get("City_Generator_2.0"):
            box.label(text="Apply City Generator to an active mesh first.", icon="ERROR")


class CG_Pavement_Texture_Panel(bpy.types.Panel):
    bl_label = "Pavement Texture"
    bl_idname = "CG_Pavement_Texture_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "LLM City Generator"
    bl_parent_id = "CG_Texture_2D_Panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.prop(scene, "pavement_texture_id", text="Texture")

        texture = PAVEMENT_TEXTURE_ASSETS.get(scene.pavement_texture_id)
        if texture:
            box.label(text=texture["label"])

        row = box.row()
        row.scale_y = 1.5
        row.operator("cg.apply_pavement_texture", text="Apply Pavement Texture", icon="TEXTURE")

        obj = context.object
        if not obj or not obj.modifiers.get("City_Generator_2.0"):
            box.label(text="Apply City Generator to an active mesh first.", icon="ERROR")
