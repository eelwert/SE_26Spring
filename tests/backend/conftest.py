from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import store
from backend.server import app


BASELINE = {
    "projects": copy.deepcopy(store.projects),
    "scenes": copy.deepcopy(store.scenes),
    "assets": copy.deepcopy(store.assets),
    "templates": copy.deepcopy(store.templates),
    "tasks": copy.deepcopy(store.tasks),
    "commands": copy.deepcopy(store.commands),
    "simulations": copy.deepcopy(store.simulations),
    "audit_logs": copy.deepcopy(store.audit_logs),
    "versions": copy.deepcopy(store.versions),
    "functions": copy.deepcopy(store.functions),
    "settings": copy.deepcopy(store.settings),
    "health": copy.deepcopy(store.health),
    "blender_connected": store.blender_connected,
    "blender_info": copy.deepcopy(store.blender_info),
    "frontend_active": store.frontend_active,
}


def reset_store() -> None:
    for key, value in BASELINE.items():
        setattr(store, key, copy.deepcopy(value))


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


@pytest.fixture
def client():
    return TestClient(app)
