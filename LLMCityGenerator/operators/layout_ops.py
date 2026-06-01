"""Operators for road layout control."""

import bpy
from ..layout.point_solver import PointSolver
from ..layout.sketch_processor import SketchProcessor


class CG_OT_PreviewPointLayout(bpy.types.Operator):
    """Parse coordinate text and create a temporary preview mesh."""

    bl_idname = "cg.preview_point_layout"
    bl_label = "Preview Point Layout"
    bl_description = "Parse coordinates and show a preview mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        points, connections = self._parse_coords(scene.cg_layout_points_text)
        if not points:
            self.report({"WARNING"}, "Invalid coordinate format. Use: x,y;x,y;...")
            return {"CANCELLED"}

        if connections is None:
            connections = self._parse_connections(scene.cg_layout_connections_text)
        faces = self._parse_faces(scene.cg_layout_faces_text)
        auto = scene.cg_layout_auto_faces

        # Remove previous preview
        prev = bpy.data.objects.get("RoadLayout_preview")
        if prev:
            mesh = prev.data
            bpy.data.objects.remove(prev)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        obj = PointSolver.create_mesh(points, connections, "RoadLayout_preview",
                                      faces=faces, generate_faces=auto)
        self.report({"INFO"}, f"Preview: {len(obj.data.vertices)}v {len(obj.data.edges)}e {len(obj.data.polygons)}f")
        return {"FINISHED"}

    @staticmethod
    def _parse_coords(text):
        """Parse "x,y;x,y;..." or "x,y,z;x,y,z;..." into list of (x,y,z) tuples."""
        if not text:
            return None, None
        points = []
        for part in text.split(";"):
            part = part.strip()
            if not part:
                continue
            vals = [float(v.strip()) for v in part.split(",")]
            if len(vals) < 2:
                continue
            points.append(tuple(vals))
        if len(points) < 2:
            return None, None
        return points, None

    @staticmethod
    def _parse_connections(text):
        """Parse "i,j;k,l;..." into list of (i,j) edge tuples or None."""
        if not text or not text.strip():
            return None
        edges = []
        for part in text.split(";"):
            part = part.strip()
            if not part:
                continue
            vals = [int(v.strip()) for v in part.split(",")]
            if len(vals) >= 2:
                edges.append(tuple(vals[:2]))
        return edges if edges else None

    @staticmethod
    def _parse_faces(text):
        """Parse "a,b,c,d;e,f,g,h;..." into list of face tuples."""
        if not text or not text.strip():
            return None
        faces = []
        for part in text.split(";"):
            part = part.strip()
            if not part:
                continue
            vals = [int(v.strip()) for v in part.split(",")]
            if len(vals) >= 3:
                faces.append(tuple(vals))
        return faces if faces else None


class CG_OT_ApplyPointLayout(bpy.types.Operator):
    """Parse coordinates and create the final road-layout mesh."""

    bl_idname = "cg.apply_point_layout"
    bl_label = "Apply Point Layout"
    bl_description = "Parse coordinates and create the road-layout mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        points, connections = CG_OT_PreviewPointLayout._parse_coords(
            scene.cg_layout_points_text
        )
        if not points:
            self.report({"WARNING"}, "Invalid coordinate format")
            return {"CANCELLED"}

        if connections is None:
            connections = CG_OT_PreviewPointLayout._parse_connections(
                scene.cg_layout_connections_text
            )
        faces = CG_OT_PreviewPointLayout._parse_faces(scene.cg_layout_faces_text)
        auto = scene.cg_layout_auto_faces

        # Remove previous
        prev = bpy.data.objects.get("RoadLayout")
        if prev:
            mesh = prev.data
            bpy.data.objects.remove(prev)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)

        obj = PointSolver.create_mesh(points, connections, "RoadLayout",
                                      faces=faces, generate_faces=auto)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        self.report({"INFO"}, f"RoadLayout: {len(obj.data.vertices)}v {len(obj.data.edges)}e {len(obj.data.polygons)}f")
        return {"FINISHED"}


class CG_OT_ApplySketchLayout(bpy.types.Operator):
    """Load a sketch image and extract road topology."""

    bl_idname = "cg.apply_sketch_layout"
    bl_label = "Generate Layout from Sketch"
    bl_description = "Extract road topology from a sketch image"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        image_path = scene.cg_sketch_image_path
        threshold = scene.cg_sketch_threshold
        min_len = scene.cg_sketch_min_line_length

        if not image_path:
            self.report({"WARNING"}, "Select a sketch image file first")
            return {"CANCELLED"}

        result = SketchProcessor.process(
            image_path=image_path,
            method="auto",
            threshold=threshold,
            min_line_length=min_len,
            mesh_name="RoadLayout",
        )

        if result["success"]:
            obj = bpy.data.objects.get(result["data"]["mesh_name"])
            if obj:
                context.view_layer.objects.active = obj
                obj.select_set(True)
            self.report({"INFO"}, result["message"])
            return {"FINISHED"}
        else:
            self.report({"WARNING"}, result["message"])
            return {"CANCELLED"}
