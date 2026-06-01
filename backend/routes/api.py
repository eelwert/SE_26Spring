"""All 18 REST API routes matching the frontend mockApi.ts contract.

Response format: ApiEnvelope<T> = { traceId, data, message? }
"""

import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..schemas import (
    ApiEnvelope,
    CreateProjectRequest,
    FunctionPlanNode,
    CreateSnapshotRequest,
    DashboardSummary,
    DispatchTaskRequest,
    LayoutRequest,
    LoginRequest,
    MultimodalCommand,
    Project,
    ReplaceAssetRequest,
    Scene,
    Session,
    StartSimulationRequest,
    SubmitCommandRequest,
    Task,
    UpdateSceneTemplateRequest,
    WorkspaceBundle,
)
from .. import store
from .. import llm_service as llm_svc

router = APIRouter()


def _ok(data):
    return ApiEnvelope(traceId=_tid(), data=data)


def _tid():
    return f"trace-{uuid.uuid4().hex[:8]}"


def _now():
    from datetime import datetime
    return datetime.now().isoformat()


# ── Auth ──────────────────────────────────────────────────

@router.post("/auth/login")
def login(request: LoginRequest):
    import time
    store.frontend_active = time.time()
    user = next((u for u in store.demo_users if u.email == request.email or u.role == request.role), None)
    if not user or request.password != store.DEMO_PASSWORD:
        raise HTTPException(401, "账号或密码不正确")
    session = Session(
        token=f"jwt-{user.role}-{int(time.time())}",
        user=user,
        expiresAt=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + 28800)),
    )
    return _ok(session)


# ── Workspace ─────────────────────────────────────────────

@router.get("/workspace/bundle")
def get_workspace_bundle():
    return _ok(WorkspaceBundle(
        projects=store.projects,
        scenes=store.scenes,
        assets=store.assets,
        templates=store.templates,
        tasks=store.tasks,
        commands=store.commands,
        simulations=store.simulations,
        auditLogs=store.audit_logs,
        versions=store.versions,
        functions=store.functions,
        settings=store.settings,
        health=store.health,
    ))


@router.get("/dashboard/summary")
def get_dashboard_summary():
    running = sum(1 for t in store.tasks if t.status in ("running", "queued"))
    failed = sum(1 for t in store.tasks if t.status == "failed")
    audit_warn = sum(1 for a in store.audit_logs if a.severity != "info")
    sims = [s for s in store.simulations if s.status != "failed"]
    return _ok(DashboardSummary(
        projectTotal=len(store.projects),
        runningTasks=running,
        failedTasks=failed,
        auditWarnings=audit_warn,
        simulationSuccessRate=round((len(sims) / max(1, len(store.simulations))) * 100),
        pluginHealthRate=98,
    ))


# ── Projects ─────────────────────────────────────────────

@router.post("/projects")
def create_project(request: CreateProjectRequest, actor: str = Query("modeler")):
    prj = Project(
        id=f"prj-{uuid.uuid4().hex[:8]}",
        name=request.name,
        owner=actor,
        status="draft",
        cityScaleKm2=request.cityScaleKm2,
        coordinateSystem=request.coordinateSystem,
        currentVersion="v01",
        updatedAt=_now(),
        sceneCount=1,
        tags=request.tags,
    )
    scene = Scene(
        id=f"scn-{uuid.uuid4().hex[:8]}",
        projectId=prj.id,
        name="默认场景",
        status="editing",
        version="v01",
        templateId="tpl-waterfront",
        roadType="慢行优先断面",
        treeType="国槐 + 银杏混植",
        seatType="滨水木质长椅",
        treeDensity=60,
        roadWidth=8,
        weather="晴",
        timeOfDay="12:00",
        objectCount=0,
        issueCount=0,
    )
    store.projects = [prj] + store.projects
    store.scenes = [scene] + store.scenes
    return _ok(prj)


@router.post("/scenes/template")
def update_scene_template(request: UpdateSceneTemplateRequest, actor: str = Query("modeler")):
    scene = store._require(store.scenes, request.sceneId, "场景")
    template = store._require(store.templates, request.templateId, "模板")
    updated = scene.model_copy(update={
        "templateId": request.templateId,
        "treeType": template.recommendedTree,
        "roadType": template.recommendedRoad,
        "seatType": template.recommendedSeat,
        "treeDensity": request.treeDensity,
        "roadWidth": request.roadWidth,
        "status": "editing",
    })
    store.scenes = [updated if s.id == updated.id else s for s in store.scenes]
    task = store._make_task(
        projectId=updated.projectId, sceneId=updated.id,
        functionName="apply_template_linkage",
        title=f"应用模板：{template.name}",
        priority=3, createdBy=actor,
        params={"template_id": request.templateId, "tree_density": request.treeDensity, "road_width": request.roadWidth},
        status="success",
    )
    return _ok({"scene": updated, "task": task})


# ── Assets ──────────────────────────────────────────────────

@router.post("/assets/replace")
def replace_asset(request: ReplaceAssetRequest, actor: str = Query("modeler")):
    asset = store._require(store.assets, request.assetId, "资产")
    status = "success" if asset.status == "available" else "failed"
    task = store._make_task(
        projectId=request.projectId, sceneId=request.sceneId,
        functionName="replace_asset_batch",
        title=f"替换{request.targetType}：{asset.name}",
        priority=4, createdBy=actor,
        params={"asset_id": request.assetId, "target_type": request.targetType},
        status=status,
    )
    return _ok(task)


# ── Layout ──────────────────────────────────────────────────

@router.post("/layout/solve")
def solve_layout(request: LayoutRequest, actor: str = Query("modeler")):
    if len(request.points) < 3:
        raise HTTPException(400, "点集至少需要 3 个约束点")
    task = store._make_task(
        projectId=request.projectId, sceneId=request.sceneId,
        functionName="solve_point_layout",
        title=f"点集布局求解（{len(request.points)} 点）",
        priority=4, createdBy=actor,
        params={"point_set": [p.model_dump() for p in request.points]},
        status="success",
    )
    return _ok(task)


@router.post("/layout/extract-sketch")
def extract_sketch(
    projectId: str = Query(...), sceneId: str = Query(...),
    fileName: str = Query(...), actor: str = Query("modeler"),
):
    task = store._make_task(
        projectId=projectId, sceneId=sceneId,
        functionName="extract_sketch_topology",
        title=f"草图点线提取：{fileName}",
        priority=4, createdBy=actor,
        params={"attachment_ref": f"upload://{fileName}", "scale": "1:1000"},
        status="success",
    )
    return _ok(task)


# ── Tasks ──────────────────────────────────────────────────

@router.post("/tasks/dispatch")
def dispatch_task(request: DispatchTaskRequest, actor: str = Query("modeler")):
    func = store._require(store.functions, request.functionName, "函数", key="name")
    if not func.enabled:
        raise HTTPException(400, "函数未注册或已停用")
    status = "running" if func.risk != "high" else "queued"
    task = store._make_task(
        projectId=request.projectId, sceneId=request.sceneId,
        functionName=request.functionName, title=request.title,
        priority=request.priority, createdBy=actor,
        params=request.params, depends=request.dependsOn,
        status=status,
    )
    # Dispatch to Blender if applicable
    if status == "running":
        from .. import blender_client
        blender_client.dispatch_task(task)
    return _ok(task)


@router.post("/tasks/{taskId}/retry")
def retry_task(taskId: str, actor: str = Query("modeler")):
    task = store._require(store.tasks, taskId, "任务")
    updated = task.model_copy(update={
        "status": "running", "progress": 34,
        "retryable": True, "errorCode": None,
    })
    store.tasks = [updated if t.id == taskId else t for t in store.tasks]
    return _ok(updated)


# ── Commands (Multi-modal / LLM) ──────────────────────────

@router.post("/commands/submit")
def submit_command(request: SubmitCommandRequest, actor: str = Query("analyst")):
    text = request.text.strip()
    if len(text) < 6 and len(request.modalities) == 1:
        raise HTTPException(400, "指令信息不足")

    # Use the real LLM service to parse the command
    result = llm_svc.parse_command(
        text, request.modalities, request.attachmentNames,
        image_base64=request.imageBase64,
    )
    plan_nodes = result.get("plan", [])

    needs = result.get("needsClarification", len(plan_nodes) == 0)
    cmd = MultimodalCommand(
        id=f"cmd-{uuid.uuid4().hex[:8]}",
        projectId=request.projectId,
        sceneId=request.sceneId,
        modality=request.modalities,
        rawInput=text or f"附件指令：{', '.join(request.attachmentNames)}",
        intentTag=result.get("intentTag", "general_scene_edit"),
        confidence=result.get("confidence", 0.65),
        slots=result.get("slots", {}),
        plan=[
            FunctionPlanNode(**n) for n in plan_nodes
        ],
        explanation=result.get("explanation", "已将指令转换为函数计划"),
        createdAt=_now(),
        needsClarification=needs,
    )
    store.commands = [cmd] + store.commands
    return _ok(cmd)


@router.post("/commands/{commandId}/dispatch")
def dispatch_plan(commandId: str, actor: str = Query("analyst")):
    cmd = store._require(store.commands, commandId, "命令计划")
    if cmd.needsClarification:
        raise HTTPException(400, "该计划需要澄清，不能自动执行")
    tasks = []
    for i, node in enumerate(cmd.plan):
        t = store._make_task(
            projectId=cmd.projectId, sceneId=cmd.sceneId,
            functionName=node.funcName, title=node.title,
            priority=3 + i, createdBy=actor,
            params=node.params, depends=node.dependsOn,
            status="queued",
        )
        tasks.append(t)
        # Dispatch to Blender
        from .. import blender_client
        blender_client.dispatch_task(t)
    return _ok(tasks)


# ── Simulations ───────────────────────────────────────────

@router.post("/simulations/start")
def start_simulation(request: StartSimulationRequest, actor: str = Query("analyst")):
    from ..schemas import SimulationJob, SimulationMetric
    sim = SimulationJob(
        id=f"sim-{uuid.uuid4().hex[:8]}",
        projectId=request.projectId,
        sceneId=request.sceneId,
        type=request.type,
        status="running",
        rulesVersion=request.rulesVersion,
        seed=request.seed,
        progress=18,
        playbackTime=0,
        durationMinutes=request.durationMinutes,
        startedAt=_now(),
        metrics=[
            SimulationMetric(name="拥堵指数", value=0.42, unit="", delta=-0.03, severity="normal"),
        ],
    )
    store.simulations = [sim] + store.simulations
    return _ok(sim)


@router.patch("/simulations/{simulationId}")
def update_simulation_status(simulationId: str, status: str = Query(...)):
    sim = store._require(store.simulations, simulationId, "仿真")
    updated = sim.model_copy(update={
        "status": status,
        "progress": 100 if status == "completed" else sim.progress,
    })
    store.simulations = [updated if s.id == simulationId else s for s in store.simulations]
    return _ok(updated)


# ── Versions ──────────────────────────────────────────────

@router.post("/versions/snapshot")
def create_snapshot(request: CreateSnapshotRequest, actor: str = Query("modeler")):
    from ..schemas import VersionSnapshot
    current = [v for v in store.versions if v.sceneId == request.sceneId]
    next_num = len(current) + 1
    snap = VersionSnapshot(
        id=f"ver-{uuid.uuid4().hex[:8]}",
        projectId=request.projectId,
        sceneId=request.sceneId,
        version=f"v{next_num:02d}",
        parentVersion=current[0].version if current else None,
        author=actor,
        createdAt=_now(),
        summary=request.summary,
        changeCount=12,
        rollbackable=True,
    )
    store.versions = [snap] + store.versions
    return _ok(snap)


@router.post("/versions/{snapshotId}/rollback")
def rollback_version(snapshotId: str, actor: str = Query("admin")):
    snap = store._require(store.versions, snapshotId, "快照")
    store.scenes = [
        s.model_copy(update={"version": snap.version, "status": "editing"})
        if s.id == snap.sceneId else s
        for s in store.scenes
    ]
    return _ok(snap)


# ── Settings ──────────────────────────────────────────────

@router.patch("/settings/{settingId}")
def update_setting(settingId: str, value: str = Query(...), actor: str = Query("admin")):
    setting = store._require(store.settings, settingId, "设置")
    if setting.locked:
        raise HTTPException(400, "该设置已锁定")
    from ..schemas import RuntimeSetting
    updated = setting.model_copy(update={"value": value})
    store.settings = [updated if s.id == settingId else s for s in store.settings]
    return _ok(updated)


@router.patch("/functions/{functionName}/toggle")
def toggle_plugin_function(functionName: str, enabled: bool = Query(...), actor: str = Query("admin")):
    func = store._require(store.functions, functionName, "函数", key="name")
    updated = func.model_copy(update={"enabled": enabled})
    store.functions = [updated if f.name == functionName else f for f in store.functions]
    return _ok(updated)


# ── Blender sync (polling) ────────────────────────────────

@router.post("/blender/register")
def blender_register(body: dict):
    store.blender_connected = True
    store.blender_info = body
    # Send pending tasks to the just-connected Blender
    pending = [t for t in store.tasks if t.status == "queued"]
    return _ok({"tasks": [t.model_dump() for t in pending]})


@router.get("/tasks/pending")
def get_pending_tasks():
    pending = [t for t in store.tasks if t.status == "queued"][:10]
    # Mark as running
    for t in pending:
        idx = next(i for i, x in enumerate(store.tasks) if x.id == t.id)
        store.tasks[idx] = t.model_copy(update={"status": "running", "progress": 10})
    return _ok({"tasks": [t.model_dump() for t in pending]})


@router.post("/tasks/{task_id}/result")
def task_result(task_id: str, body: dict):
    task = store._require(store.tasks, task_id, "任务")
    status = body.get("status", "success")
    progress = 100 if status == "success" else 50
    updated = task.model_copy(update={
        "status": status,
        "progress": progress,
        "logs": task.logs + body.get("results", []),
    })
    store.tasks = [updated if t.id == task_id else t for t in store.tasks]

    # Notify frontend via WebSocket
    from ..ws_manager import manager
    manager.notify_frontend({
        "type": "task_update",
        "taskId": task_id,
        "status": status,
        "progress": progress,
        "results": body.get("results", []),
    })

    return _ok(updated)
