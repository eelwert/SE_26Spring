def test_login_returns_session_and_marks_frontend_active(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "modeler@nku.city", "password": "demo1234"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["role"] == "modeler"
    assert data["token"].startswith("jwt-modeler-")

    health = client.get("/api/health").json()
    assert health["frontend"] == "connected"


def test_login_rejects_bad_password(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "modeler@nku.city", "password": "wrong"},
    )

    assert response.status_code == 401


def test_workspace_bundle_exposes_plugin_functions(client):
    response = client.get("/api/workspace/bundle")

    assert response.status_code == 200
    bundle = response.json()["data"]
    assert {
        "projects",
        "scenes",
        "assets",
        "templates",
        "tasks",
        "commands",
        "simulations",
        "auditLogs",
        "versions",
        "functions",
        "settings",
        "health",
    } <= set(bundle)
    functions = bundle["functions"]
    function_names = {item["name"] for item in functions}
    assert {"set_street_width", "run_traffic_simulation", "apply_layout"} <= function_names


def test_dashboard_summary_counts_current_store_state(client):
    client.post(
        "/api/tasks/dispatch",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "set_street_width",
            "title": "排队任务",
            "priority": 3,
            "params": {"width": 12},
            "dependsOn": [],
        },
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["projectTotal"] >= 1
    assert summary["runningTasks"] == 1
    assert summary["pluginHealthRate"] == 98


def test_create_project_also_creates_default_scene(client):
    response = client.post(
        "/api/projects?actor=测试建模师",
        json={
            "name": "自动化测试街区",
            "cityScaleKm2": 0.8,
            "coordinateSystem": "CGCS2000",
            "tags": ["测试", "回归"],
        },
    )

    assert response.status_code == 200
    project = response.json()["data"]
    assert project["name"] == "自动化测试街区"
    assert project["owner"] == "测试建模师"
    assert project["status"] == "draft"

    bundle = client.get("/api/workspace/bundle").json()["data"]
    created_scene = next(scene for scene in bundle["scenes"] if scene["projectId"] == project["id"])
    assert created_scene["name"] == "默认场景"
    assert created_scene["status"] == "editing"


def test_update_scene_template_changes_scene_and_records_task(client):
    response = client.post(
        "/api/scenes/template?actor=林知远",
        json={
            "sceneId": "scn-river-main",
            "templateId": "tpl-commercial",
            "treeDensity": 64,
            "roadWidth": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["scene"]["templateId"] == "tpl-commercial"
    assert data["scene"]["treeType"] == "法桐阵列"
    assert data["scene"]["roadWidth"] == 10
    assert data["task"]["functionName"] == "apply_template_linkage"
    assert data["task"]["status"] == "success"


def test_replace_asset_creates_task_for_available_asset(client):
    response = client.post(
        "/api/assets/replace?actor=林知远",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "assetId": "asset-seat-wood",
            "targetType": "seat",
        },
    )

    assert response.status_code == 200
    task = response.json()["data"]
    assert task["functionName"] == "replace_asset_batch"
    assert task["status"] == "success"
    assert task["params"] == {"asset_id": "asset-seat-wood", "target_type": "seat"}


def test_layout_solve_rejects_too_few_points(client):
    response = client.post(
        "/api/layout/solve",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "points": [
                {"id": "p1", "x": 0, "y": 0, "label": "A", "constraint": "road-node"},
                {"id": "p2", "x": 10, "y": 0, "label": "B", "constraint": "road-node"},
            ],
        },
    )

    assert response.status_code == 400
    assert "至少需要 3 个约束点" in response.json()["detail"]


def test_layout_solve_creates_success_task_for_valid_polygon(client):
    response = client.post(
        "/api/layout/solve?actor=林知远",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "points": [
                {"id": "p1", "x": 0, "y": 0, "label": "A", "constraint": "road-node"},
                {"id": "p2", "x": 10, "y": 0, "label": "B", "constraint": "road-node"},
                {"id": "p3", "x": 10, "y": 10, "label": "C", "constraint": "boundary"},
            ],
        },
    )

    assert response.status_code == 200
    task = response.json()["data"]
    assert task["functionName"] == "solve_point_layout"
    assert task["status"] == "success"
    assert len(task["params"]["point_set"]) == 3


def test_extract_sketch_creates_topology_task(client):
    response = client.post(
        "/api/layout/extract-sketch?projectId=prj-riverside&sceneId=scn-river-main&fileName=road.png&actor=林知远",
    )

    assert response.status_code == 200
    task = response.json()["data"]
    assert task["functionName"] == "extract_sketch_topology"
    assert task["title"] == "草图点线提取：road.png"
    assert task["params"]["attachment_ref"] == "upload://road.png"


def test_dispatch_task_queues_work_for_blender_poller(client):
    response = client.post(
        "/api/tasks/dispatch?actor=林知远",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "set_street_width",
            "title": "道路宽度 10 米",
            "priority": 3,
            "params": {"width": 10},
            "dependsOn": [],
        },
    )

    assert response.status_code == 200
    task = response.json()["data"]
    assert task["status"] == "queued"
    assert task["functionName"] == "set_street_width"

    pending = client.get("/api/tasks/pending").json()["data"]["tasks"]
    assert [item["id"] for item in pending] == [task["id"]]


def test_dispatch_rejects_disabled_plugin_function(client):
    client.patch("/api/functions/set_street_width/toggle?enabled=false&actor=陈明策")

    response = client.post(
        "/api/tasks/dispatch?actor=林知远",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "set_street_width",
            "title": "道路宽度 10 米",
            "priority": 3,
            "params": {"width": 10},
            "dependsOn": [],
        },
    )

    assert response.status_code == 400
    assert "已停用" in response.json()["detail"]


def test_retry_task_marks_task_running(client):
    task = client.post(
        "/api/tasks/dispatch",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "set_lane_amount",
            "title": "设置 4 车道",
            "priority": 3,
            "params": {"lanes": 4},
            "dependsOn": [],
        },
    ).json()["data"]

    response = client.post(f"/api/tasks/{task['id']}/retry?actor=林知远")

    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["status"] == "running"
    assert updated["progress"] == 34
    assert updated["retryable"] is True


def test_submit_command_and_dispatch_plan_creates_queued_tasks(client, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    command_response = client.post(
        "/api/commands/submit?actor=沈迭青",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "text": "道路宽度调到10米，增加到4车道，傍晚小雨",
            "modalities": ["text"],
            "attachmentNames": [],
        },
    )

    assert command_response.status_code == 200
    command = command_response.json()["data"]
    assert command["needsClarification"] is False
    assert [node["funcName"] for node in command["plan"]] == [
        "set_weather_lighting",
        "set_street_width",
        "set_lane_amount",
    ]

    dispatch_response = client.post(f"/api/commands/{command['id']}/dispatch?actor=沈迭青")
    assert dispatch_response.status_code == 200
    tasks = dispatch_response.json()["data"]
    assert len(tasks) == 3
    assert {task["status"] for task in tasks} == {"queued"}
    assert tasks[0]["functionName"] == "set_weather_lighting"


def test_submit_short_text_command_returns_400(client):
    response = client.post(
        "/api/commands/submit",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "text": "改",
            "modalities": ["text"],
            "attachmentNames": [],
        },
    )

    assert response.status_code == 400
    assert "指令信息不足" in response.json()["detail"]


def test_command_that_needs_clarification_cannot_dispatch(client, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    command = client.post(
        "/api/commands/submit",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "text": "请做一个现在无法匹配函数的抽象调整",
            "modalities": ["text"],
            "attachmentNames": [],
        },
    ).json()["data"]

    response = client.post(f"/api/commands/{command['id']}/dispatch")

    assert response.status_code == 400
    assert "需要澄清" in response.json()["detail"]


def test_start_and_complete_simulation(client):
    started = client.post(
        "/api/simulations/start?actor=沈迭青",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "type": "combined",
            "rulesVersion": "traffic-r3.2",
            "seed": 20260604,
            "durationMinutes": 60,
        },
    )

    assert started.status_code == 200
    simulation = started.json()["data"]
    assert simulation["status"] == "running"
    assert simulation["progress"] == 18
    assert simulation["metrics"][0]["name"] == "拥堵指数"

    completed = client.patch(f"/api/simulations/{simulation['id']}?status=completed")
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "completed"
    assert completed.json()["data"]["progress"] == 100


def test_snapshot_and_rollback_updates_scene_version(client):
    snapshot = client.post(
        "/api/versions/snapshot?actor=林知远",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "summary": "测试快照",
        },
    )

    assert snapshot.status_code == 200
    version = snapshot.json()["data"]
    assert version["version"] == "v01"
    assert version["author"] == "林知远"

    rollback = client.post(f"/api/versions/{version['id']}/rollback?actor=陈明策")
    assert rollback.status_code == 200

    scene = next(
        item
        for item in client.get("/api/workspace/bundle").json()["data"]["scenes"]
        if item["id"] == "scn-river-main"
    )
    assert scene["version"] == "v01"
    assert scene["status"] == "editing"


def test_blender_register_returns_existing_pending_tasks(client):
    created = client.post(
        "/api/tasks/dispatch",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "place_furniture",
            "title": "放置野餐桌",
            "priority": 4,
            "params": {"asset_id": "wooden_picnic_table", "min_count": 2},
            "dependsOn": [],
        },
    ).json()["data"]

    response = client.post("/api/blender/register", json={"version": "2.8.0", "blender": "4.3"})

    assert response.status_code == 200
    assert response.json()["data"]["tasks"][0]["id"] == created["id"]
    assert client.get("/api/health").json()["blender"] == "connected"


def test_task_result_marks_task_success(client):
    task = client.post(
        "/api/tasks/dispatch",
        json={
            "projectId": "prj-riverside",
            "sceneId": "scn-river-main",
            "functionName": "set_lane_amount",
            "title": "设置 4 车道",
            "priority": 3,
            "params": {"lanes": 4},
            "dependsOn": [],
        },
    ).json()["data"]

    response = client.post(
        f"/api/tasks/{task['id']}/result",
        json={"status": "success", "results": ["车道数量已设置为 4"]},
    )

    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["status"] == "success"
    assert updated["progress"] == 100
    assert "车道数量已设置为 4" in updated["logs"]


def test_sketch_analyze_requires_image_base64(client):
    response = client.post("/api/sketch/analyze", json={})

    assert response.status_code == 400
    assert "缺少 image_base64" in response.json()["detail"]


def test_sketch_analyze_without_api_key_returns_clarification_message(client, monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    response = client.post("/api/sketch/analyze", json={"image_base64": "abc123"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["points_text"] == ""
    assert data["message"] == "未设置 QWEN_API_KEY"


def test_locked_setting_update_returns_400(client, monkeypatch):
    from backend import store
    from backend.schemas import RuntimeSetting

    store.settings.insert(
        0,
        RuntimeSetting(
            id="set-locked-rbac",
            title="RBAC 根策略",
            description="测试锁定设置",
            value=True,
            category="rbac",
            locked=True,
        ),
    )

    response = client.patch("/api/settings/set-locked-rbac?value=false&actor=陈明策")

    assert response.status_code == 400
    assert "已锁定" in response.json()["detail"]


def test_unlocked_setting_update_changes_value(client):
    response = client.patch("/api/settings/set-plugin-timeout?value=9&actor=陈明策")

    assert response.status_code == 200
    assert response.json()["data"]["value"] == "9"

    bundle = client.get("/api/workspace/bundle").json()["data"]
    updated = next(item for item in bundle["settings"] if item["id"] == "set-plugin-timeout")
    assert updated["value"] == "9"


def test_toggle_plugin_function_updates_enabled_state(client):
    response = client.patch("/api/functions/set_street_width/toggle?enabled=false&actor=陈明策")

    assert response.status_code == 200
    assert response.json()["data"]["enabled"] is False

    bundle = client.get("/api/workspace/bundle").json()["data"]
    updated = next(item for item in bundle["functions"] if item["name"] == "set_street_width")
    assert updated["enabled"] is False
