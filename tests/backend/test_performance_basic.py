from __future__ import annotations

import statistics
import time

import pytest

from backend import store


def _measure_samples(operation, *, repeats: int = 5, warmup: int = 1) -> list[float]:
    samples: list[float] = []
    for index in range(repeats + warmup):
        started = time.perf_counter()
        operation()
        elapsed = time.perf_counter() - started
        if index >= warmup:
            samples.append(elapsed)
    return samples


def _assert_median_under(samples: list[float], limit_seconds: float, label: str) -> None:
    median = statistics.median(samples)
    assert median < limit_seconds, (
        f"{label} median latency {median:.4f}s exceeded baseline {limit_seconds:.4f}s; "
        f"samples={[round(sample, 4) for sample in samples]}"
    )


@pytest.mark.performance
def test_core_api_endpoints_meet_basic_latency_baseline(client):
    login_samples = _measure_samples(
        lambda: client.post(
            "/api/auth/login",
            json={"email": "modeler@nku.city", "password": "demo1234"},
        )
    )
    workspace_samples = _measure_samples(lambda: client.get("/api/workspace/bundle"))
    summary_samples = _measure_samples(lambda: client.get("/api/dashboard/summary"))

    _assert_median_under(login_samples, 0.10, "POST /api/auth/login")
    _assert_median_under(workspace_samples, 0.10, "GET /api/workspace/bundle")
    _assert_median_under(summary_samples, 0.10, "GET /api/dashboard/summary")


@pytest.mark.performance
def test_fallback_command_parsing_meets_basic_latency_baseline(client, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    def submit_command() -> None:
        response = client.post(
            "/api/commands/submit?actor=沈迭青",
            json={
                "projectId": "prj-riverside",
                "sceneId": "scn-river-main",
                "text": "道路宽度调到10米，增加到4车道，傍晚小雨",
                "modalities": ["text"],
                "attachmentNames": [],
            },
        )
        assert response.status_code == 200
        store.commands.clear()

    samples = _measure_samples(submit_command)
    _assert_median_under(samples, 0.15, "POST /api/commands/submit (fallback LLM)")


@pytest.mark.performance
def test_task_result_websocket_update_meets_basic_latency_baseline(client):
    task = client.post(
        "/api/tasks/dispatch",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "set_street_width",
            "title": "道路宽度 10 米",
            "priority": 3,
            "params": {"width": 10},
            "dependsOn": [],
        },
    ).json()["data"]

    with client.websocket_connect("/ws/frontend") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "connected"

        started = time.perf_counter()
        response = client.post(
            f"/api/tasks/{task['id']}/result",
            json={"status": "success", "results": ["道路宽度已更新"]},
        )
        elapsed = time.perf_counter() - started

        assert response.status_code == 200
        event = websocket.receive_json()
        assert event["type"] == "task_update"
        assert event["taskId"] == task["id"]
        assert event["status"] == "success"
        assert "道路宽度已更新" in event["results"]
        assert elapsed < 0.15, f"WebSocket update dispatch took {elapsed:.4f}s, expected under 0.15s"
