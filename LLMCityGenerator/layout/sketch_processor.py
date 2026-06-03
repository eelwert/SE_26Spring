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
    def analyze_only(image_path):
        """LLM analyse — returns Points/Connections/Faces as text strings.

        Returns:
            {"success": bool, "points_text": str, "connections_text": str,
             "faces_text": str, "message": str}
        """
        import os
        if not os.path.isfile(image_path):
            return {"success": False, "message": f"File not found: {image_path}"}

        with open(image_path, "rb") as fh:
            b64_data = base64.b64encode(fh.read()).decode()

        result = SketchProcessor._raw_socket_post(
            SketchProcessor.BACKEND_SKETCH_URL,
            {"image_base64": b64_data},
        )

        if result is None:
            return {"success": False, "message": "无法连接后端 (localhost:8000)，请确保后端已启动"}

        data = result.get("data", result)
        pts = data.get("points_text", "")
        conns = data.get("connections_text", "")
        faces = data.get("faces_text", "")
        message = data.get("message", "")

        if not pts:
            return {"success": False, "message": message or "LLM未能从草图中识别出道路结构"}

        return {
            "success": True,
            "points_text": pts,
            "connections_text": conns,
            "faces_text": faces,
            "message": message,
        }

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
    # LLM back-end — calls backend server, which uses GLM-4V multimodal model
    # ------------------------------------------------------------------

    BACKEND_SKETCH_URL = "http://localhost:8000/api/sketch/analyze"

    @staticmethod
    def _raw_socket_post(url, json_data):
        """Send JSON via raw socket HTTP POST (bypasses Blender firewall)."""
        import socket
        try:
            rest = url.split("://", 1)[1]
            host, rest = rest.split(":", 1)
            port_s, path = rest.split("/", 1)
            port = int(port_s)
            path = "/" + path
        except Exception:
            return None

        body_bytes = json.dumps(json_data).encode("utf-8")
        req = (
            f"POST {path} HTTP/1.0\r\n"
            f"Host: {host}\r\nConnection: close\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body_bytes)}\r\n\r\n"
        ).encode("utf-8") + body_bytes

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(60)
            sock.connect((host, port))
            sock.sendall(req)
            resp = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    resp += chunk
                except socket.timeout:
                    break
            sock.close()
            body_start = resp.find(b"\r\n\r\n")
            if body_start == -1:
                return None
            return json.loads(resp[body_start + 4:].decode("utf-8"))
        except Exception as e:
            print(f"[SketchProcessor] Socket error: {e}")
            return None

    @staticmethod
    def _process_llm(image_path, mesh_name):
        """Send sketch image to backend multimodal LLM for road topology extraction.

        The backend calls GLM-4V-Flash to analyse the hand-drawn sketch and
        returns points (0-1000 normalized coords) and edges (index pairs).
        """
        with open(image_path, "rb") as fh:
            b64_data = base64.b64encode(fh.read()).decode()

        result = SketchProcessor._raw_socket_post(
            SketchProcessor.BACKEND_SKETCH_URL,
            {"image_base64": b64_data},
        )

        if result is None:
            return {"success": False, "message": "无法连接到后端服务器 (localhost:8000)，请确保后端已启动"}

        data = result.get("data", result)
        message = data.get("message", "")
        points = data.get("points", [])
        edges = data.get("edges", [])

        if not points or not edges:
            return {"success": False, "message": message or "模型未能从草图中识别出道路结构"}

        # Convert normalized 0-1000 coords to Blender world coords (scale to ~200m)
        scale = 0.2  # 1000 → 200 Blender units
        bl_points = [(p[0] * scale, p[1] * scale) for p in points]
        segments = [(bl_points[i], bl_points[j]) for i, j in edges if i < len(bl_points) and j < len(bl_points)]

        if not segments:
            return {"success": False, "message": "无法将识别结果转换为道路线段"}

        return SketchProcessor._build_mesh_from_segments(
            segments, mesh_name, method=f"llm ({message})"
        )

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
