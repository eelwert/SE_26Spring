import type {
  ApiEnvelope,
  CreateProjectRequest,
  CreateSnapshotRequest,
  DashboardSummary,
  DispatchTaskRequest,
  LayoutRequest,
  LoginRequest,
  MultimodalCommand,
  PluginFunction,
  Project,
  ReplaceAssetRequest,
  RuntimeSetting,
  Scene,
  Session,
  SimulationJob,
  StartSimulationRequest,
  SubmitCommandRequest,
  Task,
  UpdateSceneTemplateRequest,
  VersionSnapshot,
  WorkspaceBundle,
} from '../../types/domain';

const BASE_URL = 'http://localhost:8000/api';

const request = async <T>(path: string, options?: RequestInit): Promise<ApiEnvelope<T>> => {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json() as Promise<ApiEnvelope<T>>;
};

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined });
const patch = <T>(path: string) => request<T>(path, { method: 'PATCH' });

class RealSmartCityApi {
  // Auth
  async login(req: LoginRequest): Promise<ApiEnvelope<Session>> {
    return post<Session>('/auth/login', req);
  }

  // Workspace
  async getWorkspaceBundle(): Promise<ApiEnvelope<WorkspaceBundle>> {
    return get<WorkspaceBundle>('/workspace/bundle');
  }

  async getDashboardSummary(): Promise<ApiEnvelope<DashboardSummary>> {
    return get<DashboardSummary>('/dashboard/summary');
  }

  // Projects
  async createProject(req: CreateProjectRequest, actor: string): Promise<ApiEnvelope<Project>> {
    return post<Project>(`/projects?actor=${actor}`, req);
  }

  async updateSceneTemplate(req: UpdateSceneTemplateRequest, actor: string): Promise<ApiEnvelope<{ scene: Scene; task: Task }>> {
    return post<{ scene: Scene; task: Task }>(`/scenes/template?actor=${actor}`, req);
  }

  // Assets
  async replaceAsset(req: ReplaceAssetRequest, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/assets/replace?actor=${actor}`, req);
  }

  // Layout
  async solveLayout(req: LayoutRequest, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/layout/solve?actor=${actor}`, req);
  }

  async extractSketch(projectId: string, sceneId: string, fileName: string, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/layout/extract-sketch?projectId=${projectId}&sceneId=${sceneId}&fileName=${encodeURIComponent(fileName)}&actor=${actor}`);
  }

  // Tasks
  async dispatchTask(req: DispatchTaskRequest, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/tasks/dispatch?actor=${actor}`, req);
  }

  async retryTask(taskId: string, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/tasks/${taskId}/retry?actor=${actor}`);
  }

  // Commands (LLM multimodal)
  async submitCommand(req: SubmitCommandRequest, actor: string): Promise<ApiEnvelope<MultimodalCommand>> {
    return post<MultimodalCommand>(`/commands/submit?actor=${actor}`, req);
  }

  async dispatchPlan(commandId: string, actor: string): Promise<ApiEnvelope<Task[]>> {
    return post<Task[]>(`/commands/${commandId}/dispatch?actor=${actor}`);
  }

  // Simulations
  async startSimulation(req: StartSimulationRequest, actor: string): Promise<ApiEnvelope<SimulationJob>> {
    return post<SimulationJob>(`/simulations/start?actor=${actor}`, req);
  }

  async updateSimulationStatus(simulationId: string, status: SimulationJob['status']): Promise<ApiEnvelope<SimulationJob>> {
    return patch<SimulationJob>(`/simulations/${simulationId}?status=${status}`);
  }

  // Versions
  async createSnapshot(req: CreateSnapshotRequest, actor: string): Promise<ApiEnvelope<VersionSnapshot>> {
    return post<VersionSnapshot>(`/versions/snapshot?actor=${actor}`, req);
  }

  async rollbackVersion(snapshotId: string, actor: string): Promise<ApiEnvelope<VersionSnapshot>> {
    return post<VersionSnapshot>(`/versions/${snapshotId}/rollback?actor=${actor}`);
  }

  // Settings
  async updateSetting(settingId: string, value: RuntimeSetting['value'], actor: string): Promise<ApiEnvelope<RuntimeSetting>> {
    return patch<RuntimeSetting>(`/settings/${settingId}?value=${encodeURIComponent(String(value))}&actor=${actor}`);
  }

  async togglePluginFunction(functionName: string, enabled: boolean, actor: string): Promise<ApiEnvelope<PluginFunction>> {
    return patch<PluginFunction>(`/functions/${functionName}/toggle?enabled=${enabled}&actor=${actor}`);
  }
}

export const realApi = new RealSmartCityApi();
