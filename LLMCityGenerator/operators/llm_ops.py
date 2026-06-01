"""LLM-related operators for natural language control."""

import json
import socket
import threading
import uuid

import bpy

from ..function_registry import execute_functions
from ..llm_service import call_llm, parse_local

BACKEND_URL = "http://localhost:8000/api"


def _report_to_backend(func_name, params, success, results):
    """Send execution result to backend in background thread."""

    def _post(path, payload_str):
        host, port = "localhost", 8000
        body = payload_str.encode("utf-8")
        req = f"POST {path} HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n"
        req = req.encode("utf-8") + body
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.sendall(req)
            resp = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk: break
                    resp += chunk
                except socket.timeout: break
            sock.close()
            body_start = resp.find(b"\r\n\r\n")
            if body_start != -1:
                return json.loads(resp[body_start+4:].decode("utf-8"))
        except Exception:
            return None

    def _run():
        # Dispatch task and get the real ID from response
        task_payload = json.dumps({
            "projectId": "", "sceneId": "",
            "functionName": func_name, "title": f"Blender: {func_name}",
            "priority": 3, "params": params, "dependsOn": [],
        })
        resp = _post("/api/tasks/dispatch?actor=Blender", task_payload)
        task_id = None
        if resp and resp.get("data"):
            task_id = resp["data"].get("id", "")
        if not task_id:
            task_id = f"task-blender-{uuid.uuid4().hex[:8]}"

        # Report result
        _post(f"/api/tasks/{task_id}/result", json.dumps({
            "status": "success" if success else "failed",
            "results": results,
        }))

    threading.Thread(target=_run, daemon=True).start()


def _set_result_lines(scene, lines):
    """Populate the scrollable result lines collection from a string."""
    scene.llm_result_lines.clear()
    for line in lines.split("\n"):
        item = scene.llm_result_lines.add()
        item.name = line[:80]
        item.text = line


class CG_OT_ExecuteLLMCommand(bpy.types.Operator):
    """Execute natural language command via LLM (with local fallback)"""
    bl_idname = "cg.execute_llm_command"
    bl_label = "Execute LLM Command"
    bl_description = "Send natural language instruction to LLM and execute the resulting function calls"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        user_text = scene.llm_text_input.strip()

        if not user_text:
            self.report({'WARNING'}, "请输入自然语言指令")
            return {'CANCELLED'}

        api_key = scene.llm_api_key.strip()
        if not api_key:
            import os
            api_key = os.environ.get("DEEPSEEK_API_KEY", "")

        response = None

        if api_key:
            scene.llm_status = "calling"
            _set_result_lines(scene, "正在调用 LLM...")
            self.report({'INFO'}, f"正在发送指令到 LLM: {user_text[:50]}...")
            response = call_llm(user_text, api_key)

        if not response or not response["success"]:
            scene.llm_status = "executing"
            if api_key and response and not response["success"]:
                _set_result_lines(scene, f"LLM 调用失败，切换到本地解析...\n{response['explanation'][:100]}")
            else:
                _set_result_lines(scene, "使用本地关键词解析...")
            self.report({'INFO'}, "使用本地解析模式")
            response = parse_local(user_text)

        functions = response.get("functions", [])
        if not functions:
            scene.llm_status = "done"
            _set_result_lines(scene, f"解析结果:\n{response.get('explanation', '')}\n\n没有生成可执行的函数调用。")
            self.report({'WARNING'}, "没有生成函数调用")
            return {'FINISHED'}

        skipped = [f for f in functions if f.get("_skipped")]
        valid_funcs = [f for f in functions if not f.get("_skipped")]

        if not valid_funcs:
            scene.llm_status = "done"
            msg = f"LLM 返回了 {len(skipped)} 个函数，但均不在注册表中:\n"
            for f in skipped:
                msg += f"  - {f['name']}: {f.get('_reason', 'N/A')}\n"
            _set_result_lines(scene, msg)
            self.report({'ERROR'}, "没有可执行的函数")
            return {'CANCELLED'}

        scene.llm_status = "executing"
        results = execute_functions(valid_funcs, context)

        source = "LLM" if (api_key and response.get("raw_response") != "[local]") else "本地解析"
        lines = [f"[{source}] {response.get('explanation', '')}", "", f"执行了 {len(valid_funcs)} 个函数:"]
        all_success = True
        for r in results:
            status_icon = "[OK]" if r["success"] else "[FAIL]"
            lines.append(f"  {status_icon} {r['function']}")
            for detail in r.get("results", []):
                lines.append(f"      {detail}")
            if not r["success"]:
                all_success = False

        if skipped:
            lines.append(f"\n跳过了 {len(skipped)} 个未识别函数:")
            for f in skipped:
                lines.append(f"  - {f['name']}: {f.get('_reason', 'N/A')}")

        scene.llm_status = "done"
        _set_result_lines(scene, "\n".join(lines))

        # Report to backend for frontend sync
        for r in results:
            threading.Thread(
                target=_report_to_backend,
                args=(r["function"], {}, r["success"], r.get("results", [])),
                daemon=True,
            ).start()

        if all_success:
            self.report({'INFO'}, f"成功执行 {len(valid_funcs)} 个操作")
        else:
            self.report({'WARNING'}, f"部分操作失败，请查看详情")

        return {'FINISHED'}


class CG_OT_ClearLLMResult(bpy.types.Operator):
    """Clear LLM result and input"""
    bl_idname = "cg.clear_llm_result"
    bl_label = "Clear"
    bl_description = "Clear the LLM input and result"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        scene.llm_text_input = ""
        scene.llm_status = "idle"
        scene.llm_result_lines.clear()
        return {'FINISHED'}
