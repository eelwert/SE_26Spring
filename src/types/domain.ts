export type RoleCode = 'modeler' | 'analyst' | 'admin';

export type PermissionCode =
  | 'dashboard:view'
  | 'project:read'
  | 'project:write'
  | 'asset:replace'
  | 'layout:edit'
  | 'task:dispatch'
  | 'multimodal:execute'
  | 'simulation:run'
  | 'audit:read'
  | 'version:rollback'
  | 'settings:write';

export const roleLabels: Record<RoleCode, string> = {
  modeler: '场景建模师',
  analyst: '行业分析师',
  admin: '系统管理员',
};

export const roleDescriptions: Record<RoleCode, string> = {
  modeler: '负责资产替换、模板联动、布局编辑与 Blender 插件任务下发。',
  analyst: '负责多模态方案推演、车辆/人群仿真、指标对比与结果回放。',
  admin: '负责 RBAC、插件白名单、审计版本、运行参数与安全治理。',
};

export interface User {
  id: string;
  name: string;
  email: string;
  role: RoleCode;
  department: string;
  permissions: PermissionCode[];
}

export interface Session {
  token: string;
  user: User;
  expiresAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  role?: RoleCode;
}

export interface ApiEnvelope<T> {
  traceId: string;
  data: T;
  message?: string;
}

export type ProjectStatus = 'active' | 'draft' | 'archived' | 'review';
export type SceneStatus = 'ready' | 'editing' | 'rendering' | 'failed';
export type AssetType = '2d-texture' | '3d-model' | 'material' | 'terrain' | 'vehicle' | 'crowd';
export type TaskStatus =
  | 'queued'
  | 'validating'
  | 'running'
  | 'success'
  | 'failed'
  | 'rollback'
  | 'archived';
export type SimulationStatus = 'idle' | 'queued' | 'running' | 'paused' | 'completed' | 'failed';
export type AuditSeverity = 'info' | 'warning' | 'critical';
export type HealthStatus = 'healthy' | 'degraded' | 'offline';
export type Modality = 'text' | 'sketch' | 'screenshot';

export interface Project {
  id: string;
  name: string;
  owner: string;
  status: ProjectStatus;
  cityScaleKm2: number;
  coordinateSystem: string;
  currentVersion: string;
  updatedAt: string;
  sceneCount: number;
  tags: string[];
}

export interface Scene {
  id: string;
  projectId: string;
  name: string;
  status: SceneStatus;
  version: string;
  templateId: string;
  roadType: string;
  treeType: string;
  seatType: string;
  treeDensity: number;
  roadWidth: number;
  weather: string;
  timeOfDay: string;
  objectCount: number;
  issueCount: number;
}

export interface Asset {
  id: string;
  name: string;
  type: AssetType;
  format: string;
  status: 'available' | 'missing' | 'deprecated';
  license: string;
  sizeMb: number;
  replacementFor?: string;
}

export interface SceneTemplate {
  id: string;
  name: string;
  style: string;
  rulesVersion: string;
  recommendedTree: string;
  recommendedRoad: string;
  recommendedSeat: string;
  densityRange: [number, number];
  conflictHints: string[];
}

export interface LayoutPoint {
  id: string;
  x: number;
  y: number;
  label: string;
  constraint: 'road-node' | 'facility' | 'boundary' | 'waterfront';
}

export interface TopologyLine {
  id: string;
  from: string;
  to: string;
  type: 'road' | 'river' | 'walkway' | 'boundary';
  confidence: number;
}

export interface PluginFunction {
  name: string;
  title: string;
  category: 'asset' | 'layout' | 'environment' | 'simulation' | 'render' | 'governance';
  description: string;
  enabled: boolean;
  risk: 'low' | 'medium' | 'high';
  schemaSummary: string;
  averageMs: number;
}

export interface Task {
  id: string;
  traceId: string;
  projectId: string;
  sceneId: string;
  title: string;
  functionName: string;
  status: TaskStatus;
  priority: number;
  progress: number;
  createdBy: string;
  createdAt: string;
  elapsedMs: number;
  dependsOn: string[];
  retryable: boolean;
  params: Record<string, unknown>;
  resultObjects: string[];
  logs: string[];
  errorCode?: string;
}

export interface FunctionPlanNode {
  id: string;
  funcName: string;
  title: string;
  status: 'planned' | 'approved' | 'dispatched' | 'blocked';
  dependsOn: string[];
  params: Record<string, unknown>;
}

export interface MultimodalCommand {
  id: string;
  projectId: string;
  sceneId: string;
  modality: Modality[];
  rawInput: string;
  intentTag: string;
  confidence: number;
  slots: Record<string, string | number | boolean>;
  plan: FunctionPlanNode[];
  explanation: string;
  createdAt: string;
  needsClarification: boolean;
}

export interface SimulationMetric {
  name: string;
  value: number;
  unit: string;
  delta: number;
  severity: 'good' | 'normal' | 'bad';
}

export interface SimulationJob {
  id: string;
  projectId: string;
  sceneId: string;
  type: 'traffic' | 'crowd' | 'combined';
  status: SimulationStatus;
  rulesVersion: string;
  seed: number;
  progress: number;
  playbackTime: number;
  durationMinutes: number;
  startedAt: string;
  metrics: SimulationMetric[];
}

export interface AuditLog {
  id: string;
  traceId: string;
  actor: string;
  role: RoleCode;
  eventType: string;
  target: string;
  severity: AuditSeverity;
  result: 'success' | 'denied' | 'failed' | 'pending';
  evidenceHash: string;
  createdAt: string;
}

export interface VersionSnapshot {
  id: string;
  projectId: string;
  sceneId: string;
  version: string;
  parentVersion?: string;
  author: string;
  createdAt: string;
  summary: string;
  changeCount: number;
  rollbackable: boolean;
}

export interface RuntimeSetting {
  id: string;
  title: string;
  description: string;
  value: string | number | boolean;
  category: 'rbac' | 'plugin' | 'llm' | 'simulation' | 'audit';
  locked: boolean;
}

export interface SystemHealthItem {
  id: string;
  name: string;
  status: HealthStatus;
  latencyMs: number;
  successRate: number;
  description: string;
}

export interface WorkspaceBundle {
  projects: Project[];
  scenes: Scene[];
  assets: Asset[];
  templates: SceneTemplate[];
  tasks: Task[];
  commands: MultimodalCommand[];
  simulations: SimulationJob[];
  auditLogs: AuditLog[];
  versions: VersionSnapshot[];
  functions: PluginFunction[];
  settings: RuntimeSetting[];
  health: SystemHealthItem[];
}

export interface DashboardSummary {
  projectTotal: number;
  runningTasks: number;
  failedTasks: number;
  auditWarnings: number;
  simulationSuccessRate: number;
  pluginHealthRate: number;
}

export interface CreateProjectRequest {
  name: string;
  cityScaleKm2: number;
  coordinateSystem: string;
  tags: string[];
}

export interface UpdateSceneTemplateRequest {
  sceneId: string;
  templateId: string;
  treeDensity: number;
  roadWidth: number;
}

export interface ReplaceAssetRequest {
  projectId: string;
  sceneId: string;
  assetId: string;
  targetType: string;
}

export interface LayoutRequest {
  projectId: string;
  sceneId: string;
  points: LayoutPoint[];
}

export interface DispatchTaskRequest {
  projectId: string;
  sceneId: string;
  functionName: string;
  title: string;
  priority: number;
  params: Record<string, unknown>;
  dependsOn: string[];
}

export interface SubmitCommandRequest {
  projectId: string;
  sceneId: string;
  text: string;
  modalities: Modality[];
  attachmentNames: string[];
}

export interface StartSimulationRequest {
  projectId: string;
  sceneId: string;
  type: SimulationJob['type'];
  rulesVersion: string;
  seed: number;
  durationMinutes: number;
}

export interface CreateSnapshotRequest {
  projectId: string;
  sceneId: string;
  summary: string;
}
