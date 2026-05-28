"""Sketch processor — extract road topology from hand-drawn images.

Supports two back-ends:

* **cv2** (OpenCV) — Canny edge detection + Hough line transform
* **llm**  — multimodal LLM prompt (base-64 image → JSON points & lines)

When *method* is ``"auto"`` (the default) cv2 is tried first; if the
library is not installed the processor falls back to LLM.
"""

import base64
import json
import os
import bpy
from mathutils import Vector
from collections import defaultdict


class SketchProcessor:
    """Extract road topology from a sketch image."""

    @staticmethod
    def process(image_path, method="auto", threshold=0.5, min_line_length=30,
                mesh_name="RoadLayout"):
        """Run the extraction pipeline and create a road mesh.

        Args:
            image_path (str): absolute path to the sketch image.
            method (str): ``"cv2"``, ``"llm"``, or ``"auto"``.
            threshold (float): Canny edge threshold (cv2 mode only).
            min_line_length (int): minimum line length in pixels.
            mesh_name (str): name for the created mesh object.

        Returns:
            dict: ``{"success": bool, "data": {...}, "message": str}``
        """
        if not os.path.isfile(image_path):
            return {"success": False, "message": f"File not found: {image_path}"}

        if method == "auto":
            method = "cv2" if SketchProcessor._has_cv2() else "llm"

        if method == "cv2":
            return SketchProcessor._process_cv2(image_path, threshold,
                                                min_line_length, mesh_name)
        elif method == "llm":
            return SketchProcessor._process_llm(image_path, mesh_name)
        else:
            return {"success": False, "message": f"Unknown method: {method}"}

    # ------------------------------------------------------------------
    # cv2 back-end
    # ------------------------------------------------------------------

    @staticmethod
    def _has_cv2():
        try:
            import cv2  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _process_cv2(image_path, threshold, min_line_length, mesh_name):
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "message": f"Cannot read image: {image_path}"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        low = int(threshold * 100)
        high = int(threshold * 200)
        edges_img = cv2.Canny(blurred, max(low, 30), max(high, 60))

        lines = cv2.HoughLinesP(edges_img, 1, np.pi / 180,
                                threshold=30,
                                minLineLength=min_line_length,
                                maxLineGap=20)

        if lines is None or len(lines) == 0:
            return {"success": False, "message": "No lines detected in the image"}

        # Collect unique endpoints
        raw_points = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            raw_points.append(((x1, y1), (x2, y2)))

        return SketchProcessor._build_mesh_from_segments(
            raw_points, mesh_name, method="cv2")

    # ------------------------------------------------------------------
    # LLM back-end (stub — member B provides the actual API call)
    # ------------------------------------------------------------------

    @staticmethod
    def _process_llm(image_path, mesh_name):
        """Placeholder for multimodal LLM line extraction.

        In the final integration, Member B's ``llm_service.py`` would be
        called here.  For now we return an informative error so the
        developer knows where to wire in the API call.
        """
        # Encode image for reference
        with open(image_path, "rb") as fh:
            b64_data = base64.b64encode(fh.read()).decode()

        # TODO: replace with actual LLM call (member B)
        # prompt = (
        #     "Analyse this hand-drawn road sketch. Return ONLY valid JSON: "
        #     '{"points": [[x1,y1], ...], "lines": [[i,j], ...]}'
        # )
        # response = llm_service.chat(prompt, image_b64=b64_data)
        # data = json.loads(response)

        return {
            "success": False,
            "message": (
                "LLM sketch processing requires member B's llm_service module. "
                "Install cv2 (pip install opencv-python) into Blender's Python, "
                "or wire the LLM call in layout/sketch_processor.py:_process_llm(). "
                f"Image encoded as base64 ({len(b64_data)} bytes ready)."
            ),
        }

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_mesh_from_segments(segments, mesh_name, method):
        """Convert ``[(p0,p1), ...]`` into vertices + edges and create a mesh."""
        # Cluster nearby endpoints into shared vertices
        vert_map = {}   # frozen Vector → index
        verts = []
        edges = []

        def _add_vertex(pt):
            key = (round(pt[0], 1), round(pt[1], 1), 0.0)
            if key not in vert_map:
                vert_map[key] = len(verts)
                verts.append(Vector(key))
            return vert_map[key]

        for p0, p1 in segments:
            i0 = _add_vertex(p0)
            i1 = _add_vertex(p1)
            if i0 != i1:
                edges.append((i0, i1))

        if not edges:
            return {"success": False, "message": "No edges after clustering"}

        mesh_data = bpy.data.meshes.new(mesh_name)
        mesh_data.from_pydata(verts, edges, [])
        mesh_data.update()

        obj = bpy.data.objects.new(mesh_name, mesh_data)
        bpy.context.scene.collection.objects.link(obj)

        return {
            "success": True,
            "data": {
                "points": [tuple(v) for v in verts],
                "edges": edges,
                "mesh_name": obj.name,
                "vertex_count": len(verts),
                "edge_count": len(edges),
                "method": method,
            },
            "message": f"{len(verts)} vertices, {len(edges)} edges extracted via {method}",
        }
