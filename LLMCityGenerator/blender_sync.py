"""Background sync — polls backend for tasks via a separate thread.

Uses threading so network timeouts never block Blender's UI.
Activated automatically when the addon is enabled.
"""

import json
import threading
import queue

import bpy

from .function_registry import execute_function

BACKEND_URL = "http://localhost:8000/api"
POLL_INTERVAL = 3.0

# Background thread state
_thread: threading.Thread | None = None
_running = False
_result_queue = queue.Queue()


def _request(url, data=None, method="GET"):
    """HTTP request via raw socket — bypasses urllib and curl, works in Blender."""
    import socket
    try:
        # Parse http://host:port/path
        rest = url.split("://", 1)[1]
        host, rest = rest.split(":", 1)
        port, path = rest.split("/", 1)
        port = int(port)
        path = "/" + path
    except Exception:
        return None

    body_bytes = json.dumps(data).encode("utf-8") if data else b""
    req = (
        f"{method} {path} HTTP/1.0\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"\r\n"
    )
    req = req.encode("utf-8") + body_bytes

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((host, port))
        sock.sendall(req)

        # Read all response data until connection closes
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

        # Extract JSON body
        body_start = resp.find(b"\r\n\r\n")
        if body_start == -1:
            return None
        return json.loads(resp[body_start+4:].decode("utf-8"))
    except Exception as e:
        print(f"[sync] _request failed for {url}: {e}")
        return None


def _sync_thread():
    """Background thread: poll backend, queue results for main thread."""
    global _running
    import time
    tick = 0

    print("[sync] Thread started, backend:", BACKEND_URL)
    while _running:
        try:
            if tick % 10 == 0:
                reg = _request(f"{BACKEND_URL}/blender/register",
                               {"version": "2.8.0", "blender": "4.1"}, "POST")
                print(f"[sync] Register attempt: {'OK' if reg else 'FAIL'}")

            result = _request(f"{BACKEND_URL}/tasks/pending")
            if result and result.get("data"):
                tasks = result["data"].get("tasks", [])
                if tasks:
                    print(f"[sync] Got {len(tasks)} tasks")
                    _result_queue.put(tasks)
        except Exception as e:
            print(f"[sync] Thread error: {e}")

        tick += 1
        time.sleep(POLL_INTERVAL)


def _process_results():
    """Called by bpy.app.timers on main thread — process queued tasks."""
    try:
        while True:
            tasks = _result_queue.get_nowait()
            for task in tasks:
                task_id = task.get("id", task.get("taskId", ""))
                func_name = task.get("functionName", "")
                params = task.get("params", {})
                if not func_name:
                    continue
                try:
                    exec_result = execute_function(func_name, params, bpy.context)
                except Exception as e:
                    exec_result = {"success": False, "results": [str(e)]}

                # Report result (also in background thread to avoid blocking)
                t = threading.Thread(
                    target=_request,
                    args=(f"{BACKEND_URL}/tasks/{task_id}/result", {
                        "status": "success" if exec_result.get("success") else "failed",
                        "results": exec_result.get("results", []),
                    }, "POST"),
                    daemon=True,
                )
                t.start()
    except queue.Empty:
        pass
    return POLL_INTERVAL


def start_sync():
    """Start the background polling thread + main-thread result processor."""
    global _running, _thread
    if _running:
        return
    _running = True
    _thread = threading.Thread(target=_sync_thread, daemon=True)
    _thread.start()
    print("[sync] Background thread started")
    if not bpy.app.timers.is_registered(_process_results):
        bpy.app.timers.register(_process_results, first_interval=2.0)
        print("[sync] Main-thread timer registered")


def stop_sync():
    """Stop background thread and clean up."""
    global _running, _thread
    _running = False
    if bpy.app.timers.is_registered(_process_results):
        bpy.app.timers.unregister(_process_results)
