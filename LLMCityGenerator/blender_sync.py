"""Background sync — polls backend in a thread, executes on the main Blender thread."""

import json
import socket
import threading
import time

import bpy

from .function_registry import execute_function

BACKEND_URL = "http://localhost:8000/api"
POLL_INTERVAL = 3.0
_tasks_to_run = []  # only accessed from main thread via timer
_running = False


def _request(url, data=None, method="GET"):
    try:
        rest = url.split("://", 1)[1]
        host, rest = rest.split(":", 1)
        port_s, path = rest.split("/", 1)
        port = int(port_s)
        path = "/" + path
    except Exception:
        return None
    body_bytes = json.dumps(data).encode("utf-8") if data else b""
    req = (
        f"{method} {path} HTTP/1.0\r\n"
        f"Host: {host}\r\nConnection: close\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body_bytes)}\r\n\r\n"
    ).encode("utf-8") + body_bytes
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
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
        print(f"[sync] _request: {e}")
        return None


def _report_result(task_id, success, results):
    """Send result to backend (called from any thread)."""
    _request(f"{BACKEND_URL}/tasks/{task_id}/result", {
        "status": "success" if success else "failed",
        "results": results,
    }, "POST")


def _poll_thread():
    """Background thread: poll backend, push tasks to shared list."""
    global _running
    tick = 0
    while _running:
        try:
            if tick % 10 == 0:
                reg = _request(f"{BACKEND_URL}/blender/register",
                               {"version": "2.8.0", "blender": "5.1"}, "POST")
                print(f"[sync] Register: {'OK' if reg else 'FAIL'}")
            resp = _request(f"{BACKEND_URL}/tasks/pending")
            if resp and resp.get("data"):
                tasks = resp["data"].get("tasks", [])
                if tasks:
                    _tasks_to_run.extend(tasks)
                    print(f"[sync] Queued {len(tasks)} tasks (total pending: {len(_tasks_to_run)})")
        except Exception as e:
            print(f"[sync] Poll error: {e}")
        tick += 1
        time.sleep(POLL_INTERVAL)


def _process_one_task():
    """Main-thread timer: process one task per tick, runs every 0.5s."""
    if not _tasks_to_run:
        return 0.5

    task = _tasks_to_run.pop(0)
    tid = task.get("id", task.get("taskId", ""))
    fn = task.get("functionName", "")
    params = task.get("params", {})

    if not fn:
        return 0.1

    print(f"[sync] Exec: {fn} {params}")
    try:
        result = execute_function(fn, params, bpy.context)
        ok = result.get("success", False)
        results = result.get("results", [])
        print(f"[sync] Done: {'OK' if ok else 'FAIL'}")
    except Exception as e:
        ok = False
        results = [str(e)]
        print(f"[sync] Error: {e}")

    threading.Thread(target=_report_result, args=(tid, ok, results), daemon=True).start()
    return 0.1 if _tasks_to_run else 0.5  # fast batch when many tasks


def start_sync():
    global _running, _tasks_to_run
    if _running:
        return
    _running = True
    _tasks_to_run = []
    threading.Thread(target=_poll_thread, daemon=True).start()
    print("[sync] Poll thread started")
    if not bpy.app.timers.is_registered(_process_one_task):
        bpy.app.timers.register(_process_one_task, first_interval=0.5, persistent=True)
        print("[sync] Execute timer registered (0.5s)")


def stop_sync():
    global _running
    _running = False
    if bpy.app.timers.is_registered(_process_one_task):
        bpy.app.timers.unregister(_process_one_task)
