"""WebSocket connection manager for bidirectional frontend↔Blender sync."""

import json
import asyncio
from typing import Optional

from fastapi import WebSocket


class WSManager:
    """Central hub: frontend and Blender each connect via WebSocket."""

    def __init__(self):
        self.frontend: Optional[WebSocket] = None
        self.blender: Optional[WebSocket] = None
        self._pending: dict[str, asyncio.Future] = {}

    async def connect_frontend(self, ws: WebSocket):
        await ws.accept()
        self.frontend = ws
        await self._send(ws, {"type": "connected", "role": "frontend"})
        try:
            while True:
                data = await ws.receive_text()
                msg = json.loads(data)
                # Frontend → Blender relay
                if msg.get("type") == "dispatch" and self.blender:
                    await self._send(self.blender, msg)
        except Exception:
            pass
        finally:
            self.frontend = None

    async def connect_blender(self, ws: WebSocket):
        await ws.accept()
        self.blender = ws
        await self._send(ws, {"type": "connected", "role": "blender"})
        try:
            while True:
                data = await ws.receive_text()
                msg = json.loads(data)
                # Blender → Frontend relay
                if self.frontend:
                    await self._send(self.frontend, msg)
        except Exception:
            pass
        finally:
            self.blender = None

    async def dispatch_task(self, task: dict) -> Optional[dict]:
        """Send task to Blender and wait for result (sync mode)."""
        if not self.blender:
            return None
        task_id = task.get("taskId", task.get("id", ""))
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[task_id] = future
        await self._send(self.blender, {"type": "dispatch", "task": task})
        try:
            result = await asyncio.wait_for(future, timeout=30)
            return result
        except asyncio.TimeoutError:
            self._pending.pop(task_id, None)
            return {"status": "timeout", "error": "Task timed out"}

    def notify_frontend(self, event: dict):
        """Non-async helper to queue a send to frontend."""
        if self.frontend:
            asyncio.create_task(self._send(self.frontend, event))

    async def _send(self, ws: WebSocket, data: dict):
        try:
            await ws.send_text(json.dumps(data, ensure_ascii=False))
        except Exception:
            pass


manager = WSManager()
