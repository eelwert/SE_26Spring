"""FastAPI server — Smart City Generator Backend Control Plane.

Start:    python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
WebSocket: ws://localhost:8000/ws/frontend  (frontend)
           ws://localhost:8000/ws/blender   (Blender plugin)
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .routes.api import router
from .ws_manager import manager

app = FastAPI(title="Smart City Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/api/health")
def health_check():
    import time
    from . import store
    blender_connected = (manager.blender is not None) or store.blender_connected
    # Frontend is "connected" if it logged in within the last 5 minutes
    frontend_connected = (
        (manager.frontend is not None) or
        (store.frontend_active > 0 and (time.time() - store.frontend_active) < 300)
    )
    return {
        "status": "ok",
        "blender": "connected" if blender_connected else "disconnected",
        "frontend": "connected" if frontend_connected else "disconnected",
    }


@app.websocket("/ws/frontend")
async def ws_frontend(ws: WebSocket):
    await manager.connect_frontend(ws)


@app.websocket("/ws/blender")
async def ws_blender(ws: WebSocket):
    await manager.connect_blender(ws)
