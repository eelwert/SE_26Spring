"""In-memory data store with demo seed data matching frontend mockData.ts."""

import time
import uuid

from .schemas import (
    Asset, AuditLog, MultimodalCommand, PluginFunction, Project,
    RuntimeSetting, Scene, SceneTemplate, SimulationJob,
    SystemHealthItem, Task, User, VersionSnapshot, TaskStatus,
)

DEMO_PASSWORD = "demo1234"

demo_users: list[User] = [
    User(id="usr-modeler", name="林知远", email="modeler@nku.city", role="modeler",
         department="场景建模组", permissions=["dashboard:view","project:read","project:write","asset:replace","layout:edit","task:dispatch","multimodal:execute","audit:read"]),
    User(id="usr-analyst", name="沈迭青", email="analyst@nku.city", role="analyst",
         department="城市仿真分析组", permissions=["dashboard:view","project:read","task:dispatch","multimodal:execute","simulation:run","audit:read"]),
    User(id="usr-admin", name="陈明策", email="admin@nku.city", role="admin",
         department="平台治理与运维", permissions=["dashboard:view","project:read","project:write","asset:replace","layout:edit","task:dispatch","multimodal:execute","simulation:run","audit:read","version:rollback","settings:write"]),
]

projects: list[Project] = [
    Project(id="prj-riverside", name="津湾河岸复合街区", owner="林知远", status="active",
            cityScaleKm2=1.2, coordinateSystem="CGCS2000 / Tianjin Local Grid",
            currentVersion="v18", updatedAt="2026-05-24T15:20:00+08:00", sceneCount=4,
            tags=["滨水","商业","行人密集"]),
]

scenes: list[Scene] = [
    Scene(id="scn-river-main", projectId="prj-riverside", name="主河岸日间运营场景",
          status="editing", version="v18", templateId="tpl-waterfront",
          roadType="慢行优先断面", treeType="国槐 + 银杏混植", seatType="滨水木质长椅",
          treeDensity=72, roadWidth=8, weather="多云", timeOfDay="16:30",
          objectCount=4218, issueCount=2),
]

assets: list[Asset] = [
    Asset(id="asset-tree-ginkgo", name="银杏树组 LOD2", type="3d-model", format="glTF", status="available", license="CC-BY 4.0", sizeMb=24),
    Asset(id="asset-road-asphalt", name="透水沥青材质包", type="material", format="PBR", status="available", license="Internal", sizeMb=88),
    Asset(id="asset-seat-wood", name="滨水木质长椅", type="3d-model", format="FBX", status="available", license="Internal", sizeMb=17),
]

templates: list[SceneTemplate] = [
    SceneTemplate(id="tpl-waterfront", name="滨水活力街区", style="亲水慢行 + 商业外摆",
                  rulesVersion="tpl-r4.2", recommendedTree="国槐 + 银杏混植",
                  recommendedRoad="慢行优先断面", recommendedSeat="滨水木质长椅",
                  densityRange=(50, 85), conflictHints=["树木密度超过 82% 时需检查消防通道净宽"]),
    SceneTemplate(id="tpl-commercial", name="商业步行街", style="连续界面 + 夜间灯光",
                  rulesVersion="tpl-r3.9", recommendedTree="法桐阵列",
                  recommendedRoad="商业步行街断面", recommendedSeat="模块化金属座椅",
                  densityRange=(40, 70), conflictHints=[]),
    SceneTemplate(id="tpl-campus", name="校园安全疏散", style="低速混行 + 开放空间",
                  rulesVersion="tpl-r2.7", recommendedTree="白蜡 + 灌木带",
                  recommendedRoad="校园混行道路", recommendedSeat="校园石材座椅",
                  densityRange=(45, 75), conflictHints=[]),
]

functions: list[PluginFunction] = [
    PluginFunction(name="replace_asset_batch", title="批量资产替换", category="asset",
                   description="替换树木、座椅、建筑立面等", enabled=True, risk="medium",
                   schemaSummary="asset_id, target_type", averageMs=1180),
    PluginFunction(name="apply_template_linkage", title="模板联动配置", category="layout",
                   description="根据模板联动道路树木座椅", enabled=True, risk="low",
                   schemaSummary="template_id, density, road_width", averageMs=620),
    PluginFunction(name="set_weather_lighting", title="天气与天色控制", category="environment",
                   description="标准化天气、时间与光照", enabled=True, risk="low",
                   schemaSummary="weather, time_of_day", averageMs=410),
    PluginFunction(name="dispatch_blender_job", title="Blender 插件下发", category="render",
                   description="封装函数计划为插件任务并等待回执", enabled=True, risk="high",
                   schemaSummary="function_plan, idempotency_key", averageMs=1920),
    PluginFunction(name="solve_point_layout", title="点集布局求解", category="layout",
                   description="根据点集重建道路和设施布局", enabled=True, risk="medium",
                   schemaSummary="point_set, topology_rules", averageMs=1360),
    PluginFunction(name="extract_sketch_topology", title="草图点线提取", category="layout",
                   description="从草图提取道路/边界拓扑", enabled=True, risk="medium",
                   schemaSummary="attachment_ref, scale", averageMs=1640),
    PluginFunction(name="run_traffic_simulation", title="车辆仿真调度", category="simulation",
                   description="调度交通仿真规则与需求", enabled=True, risk="medium",
                   schemaSummary="rules_version, seed", averageMs=2380),
    PluginFunction(name="run_crowd_simulation", title="人群仿真调度", category="simulation",
                   description="调度人群仿真规则与参数", enabled=True, risk="medium",
                   schemaSummary="rules_version, agent_count, seed", averageMs=2450),
    PluginFunction(name="rollback_scene_version", title="版本回滚", category="governance",
                   description="恢复到指定场景快照", enabled=True, risk="high",
                   schemaSummary="snapshot_id", averageMs=880),
    PluginFunction(name="set_street_width", title="道路宽度设置", category="layout",
                   description="调整城市道路宽度", enabled=True, risk="low",
                   schemaSummary="width", averageMs=310),
    PluginFunction(name="set_lane_amount", title="车道数量设置", category="layout",
                   description="调整车道数量", enabled=True, risk="low",
                   schemaSummary="lanes", averageMs=310),
    PluginFunction(name="set_tree_density", title="树木密度设置", category="environment",
                   description="调整街道树木密度", enabled=True, risk="low",
                   schemaSummary="density", averageMs=350),
    PluginFunction(name="set_street_lights", title="路灯开关", category="environment",
                   description="开启或关闭路灯", enabled=True, risk="low",
                   schemaSummary="enable", averageMs=280),
    PluginFunction(name="toggle_traffic", title="交通元素开关", category="simulation",
                   description="启用或禁用交通模拟元素", enabled=True, risk="medium",
                   schemaSummary="enable", averageMs=290),
]

tasks: list[Task] = [
    Task(id="task-1001", traceId="trace-1001", projectId="prj-riverside", sceneId="scn-river-main",
         title="主路两侧树木密度联动更新", functionName="apply_template_linkage",
         status="success", priority=3, progress=100, createdBy="林知远",
         createdAt="2026-05-24T15:11:00+08:00", elapsedMs=914,
         params={"template_id":"tpl-waterfront","tree_density":72,"road_width":8},
         resultObjects=["road-main-01"], logs=["schema 校验通过","回执 success"]),
]

commands: list[MultimodalCommand] = []
simulations: list[SimulationJob] = []
audit_logs: list[AuditLog] = []
versions: list[VersionSnapshot] = []

settings: list[RuntimeSetting] = [
    RuntimeSetting(id="set-llm-confidence", title="低置信度澄清阈值",
                   description="低于阈值时禁止自动执行", value=0.72, category="llm", locked=False),
    RuntimeSetting(id="set-plugin-timeout", title="轻量插件硬超时",
                   description="Blender 插件任务超时进入重试", value=5, category="plugin", locked=False),
]

health: list[SystemHealthItem] = [
    SystemHealthItem(id="health-api", name="控制平面 API", status="healthy", latencyMs=42,
                     successRate=99.8, description="认证、项目、任务编排入口"),
    SystemHealthItem(id="health-blender", name="Blender 插件执行器", status="healthy", latencyMs=312,
                     successRate=98.5, description="任务回执正常"),
    SystemHealthItem(id="health-llm", name="LLM 服务", status="healthy", latencyMs=860,
                     successRate=99.0, description="函数计划生成与澄清"),
]


def _require(collection: list, item_id: str, label: str, key: str = "id"):
    item = next((x for x in collection if getattr(x, key) == item_id), None)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(404, f"{label}不存在")
    return item


def _make_task(
    projectId, sceneId, functionName, title, priority, createdBy,
    params, status: TaskStatus = "queued", depends=None,
):
    from datetime import datetime
    t = Task(
        id=f"task-{uuid.uuid4().hex[:8]}",
        traceId=f"trace-{uuid.uuid4().hex[:8]}",
        projectId=projectId, sceneId=sceneId,
        title=title, functionName=functionName,
        status=status, priority=priority,
        progress=0, createdBy=createdBy,
        createdAt=datetime.now().isoformat(),
        dependsOn=depends or [],
        retryable=status == "failed",
        params=params,
        logs=["任务已生成", "参数 schema 校验通过"],
        errorCode="2004" if status == "failed" else None,
    )
    tasks.insert(0, t)
    return t
