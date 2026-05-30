"""Pydantic schemas mirroring frontend types from src/types/domain.ts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# --- Envelope ---

class ApiEnvelope(BaseModel, Generic[T]):
    traceId: str = Field(default_factory=lambda: f"trace-{uuid.uuid4().hex[:8]}")
    data: T
    message: Optional[str] = None


# --- Enums ---

RoleCode = str  # "modeler" | "analyst" | "admin"
PermissionCode = str
ProjectStatus = str  # "active" | "draft" | "archived" | "review"
SceneStatus = str  # "ready" | "editing" | "rendering" | "failed"
AssetType = str  # "2d-texture" | "3d-model" | "material" | "terrain" | "vehicle" | "crowd"
TaskStatus = str  # "queued" | "validating" | "running" | "success" | "failed" | "rollback" | "archived"
SimulationStatus = str  # "idle" | "queued" | "running" | "paused" | "completed" | "failed"
AuditSeverity = str  # "info" | "warning" | "critical"
HealthStatus = str  # "healthy" | "degraded" | "offline"
Modality = str  # "text" | "sketch" | "screenshot"


# --- Domain Models ---

class User(BaseModel):
    id: str
    name: str
    email: str
    role: RoleCode
    department: str
    permissions: list[PermissionCode]


class Session(BaseModel):
    token: str
    user: User
    expiresAt: str


class LoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[RoleCode] = None


class Project(BaseModel):
    id: str
    name: str
    owner: str
    status: ProjectStatus
    cityScaleKm2: float
    coordinateSystem: str
    currentVersion: str
    updatedAt: str
    sceneCount: int
    tags: list[str]


class Scene(BaseModel):
    id: str
    projectId: str
    name: str
    status: SceneStatus
    version: str
    templateId: str
    roadType: str
    treeType: str
    seatType: str
    treeDensity: int
    roadWidth: int
    weather: str
    timeOfDay: str
    objectCount: int
    issueCount: int


class Asset(BaseModel):
    id: str
    name: str
    type: AssetType
    format: str
    status: str  # "available" | "missing" | "deprecated"
    license: str
    sizeMb: float
    replacementFor: Optional[str] = None


class SceneTemplate(BaseModel):
    id: str
    name: str
    style: str
    rulesVersion: str
    recommendedTree: str
    recommendedRoad: str
    recommendedSeat: str
    densityRange: tuple[float, float]
    conflictHints: list[str]


class LayoutPoint(BaseModel):
    id: str
    x: float
    y: float
    label: str
    constraint: str  # "road-node" | "facility" | "boundary" | "waterfront"


class PluginFunction(BaseModel):
    name: str
    title: str
    category: str  # "asset" | "layout" | "environment" | "simulation" | "render" | "governance"
    description: str
    enabled: bool
    risk: str  # "low" | "medium" | "high"
    schemaSummary: str
    averageMs: int


class Task(BaseModel):
    id: str
    traceId: str = ""
    projectId: str
    sceneId: str
    title: str
    functionName: str
    status: TaskStatus
    priority: int
    progress: int
    createdBy: str
    createdAt: str
    elapsedMs: int = 0
    dependsOn: list[str] = []
    retryable: bool = False
    params: dict[str, Any] = {}
    resultObjects: list[str] = []
    logs: list[str] = []
    errorCode: Optional[str] = None


class FunctionPlanNode(BaseModel):
    id: str
    funcName: str
    title: str
    status: str = "approved"
    dependsOn: list[str] = []
    params: dict[str, Any] = {}


class MultimodalCommand(BaseModel):
    id: str
    projectId: str
    sceneId: str
    modality: list[str]
    rawInput: str
    intentTag: str
    confidence: float
    slots: dict[str, Any] = {}
    plan: list[FunctionPlanNode] = []
    explanation: str
    createdAt: str
    needsClarification: bool


class SimulationMetric(BaseModel):
    name: str
    value: float
    unit: str
    delta: float
    severity: str  # "good" | "normal" | "bad"


class SimulationJob(BaseModel):
    id: str
    projectId: str
    sceneId: str
    type: str  # "traffic" | "crowd" | "combined"
    status: SimulationStatus
    rulesVersion: str
    seed: int
    progress: int
    playbackTime: float
    durationMinutes: int
    startedAt: str
    metrics: list[SimulationMetric] = []


class AuditLog(BaseModel):
    id: str
    traceId: str = ""
    actor: str
    role: RoleCode
    eventType: str
    target: str
    severity: AuditSeverity
    result: str  # "success" | "denied" | "failed" | "pending"
    evidenceHash: str
    createdAt: str


class VersionSnapshot(BaseModel):
    id: str
    projectId: str
    sceneId: str
    version: str
    parentVersion: Optional[str] = None
    author: str
    createdAt: str
    summary: str
    changeCount: int
    rollbackable: bool


class RuntimeSetting(BaseModel):
    id: str
    title: str
    description: str
    value: Any
    category: str  # "rbac" | "plugin" | "llm" | "simulation" | "audit"
    locked: bool


class SystemHealthItem(BaseModel):
    id: str
    name: str
    status: HealthStatus
    latencyMs: int
    successRate: float
    description: str


class WorkspaceBundle(BaseModel):
    projects: list[Project]
    scenes: list[Scene]
    assets: list[Asset]
    templates: list[SceneTemplate]
    tasks: list[Task]
    commands: list[MultimodalCommand]
    simulations: list[SimulationJob]
    auditLogs: list[AuditLog]
    versions: list[VersionSnapshot]
    functions: list[PluginFunction]
    settings: list[RuntimeSetting]
    health: list[SystemHealthItem]


class DashboardSummary(BaseModel):
    projectTotal: int
    runningTasks: int
    failedTasks: int
    auditWarnings: int
    simulationSuccessRate: int
    pluginHealthRate: int


# --- Request Schemas ---

class CreateProjectRequest(BaseModel):
    name: str
    cityScaleKm2: float
    coordinateSystem: str
    tags: list[str] = []


class UpdateSceneTemplateRequest(BaseModel):
    sceneId: str
    templateId: str
    treeDensity: int
    roadWidth: int


class ReplaceAssetRequest(BaseModel):
    projectId: str
    sceneId: str
    assetId: str
    targetType: str


class LayoutRequest(BaseModel):
    projectId: str
    sceneId: str
    points: list[LayoutPoint]


class DispatchTaskRequest(BaseModel):
    projectId: str
    sceneId: str
    functionName: str
    title: str
    priority: int
    params: dict[str, Any] = {}
    dependsOn: list[str] = []


class SubmitCommandRequest(BaseModel):
    projectId: str
    sceneId: str
    text: str
    modalities: list[str] = ["text"]
    attachmentNames: list[str] = []


class StartSimulationRequest(BaseModel):
    projectId: str
    sceneId: str
    type: str  # "traffic" | "crowd" | "combined"
    rulesVersion: str
    seed: int
    durationMinutes: int


class CreateSnapshotRequest(BaseModel):
    projectId: str
    sceneId: str
    summary: str
