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
import { backendConnectionMessage, backendFetchUrl } from './config';

const parseErrorMessage = (body: string, fallback: string) => {
  if (!body.trim()) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(body) as { detail?: unknown; message?: unknown };
    if (typeof parsed.detail === 'string') {
      return parsed.detail;
    }
    if (typeof parsed.message === 'string') {
      return parsed.message;
    }
  } catch {
    // Use the text body below.
  }
  return body;
};

const request = async <T>(path: string, options?: RequestInit): Promise<ApiEnvelope<T>> => {
  let res: Response;
  try {
    res = await fetch(backendFetchUrl(path), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
  } catch {
    throw new Error(backendConnectionMessage());
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(parseErrorMessage(body, `后端请求失败：HTTP ${res.status}`));
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
    return post<Project>(`/projects?actor=${encodeURIComponent(actor)}`, req);
  }

  async updateSceneTemplate(req: UpdateSceneTemplateRequest, actor: string): Promise<ApiEnvelope<{ scene: Scene; task: Task }>> {
    return post<{ scene: Scene; task: Task }>(`/scenes/template?actor=${encodeURIComponent(actor)}`, req);
  }

  // Assets
  async replaceAsset(req: ReplaceAssetRequest, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/assets/replace?actor=${encodeURIComponent(actor)}`, req);
  }

  // Layout
  async solveLayout(req: LayoutRequest, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/layout/solve?actor=${encodeURIComponent(actor)}`, req);
  }

  // Tasks
  async dispatchTask(req: DispatchTaskRequest, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/tasks/dispatch?actor=${encodeURIComponent(actor)}`, req);
  }

  async retryTask(taskId: string, actor: string): Promise<ApiEnvelope<Task>> {
    return post<Task>(`/tasks/${encodeURIComponent(taskId)}/retry?actor=${encodeURIComponent(actor)}`);
  }

  // Commands (LLM multimodal)
  async submitCommand(req: SubmitCommandRequest, actor: string): Promise<ApiEnvelope<MultimodalCommand>> {
    return post<MultimodalCommand>(`/commands/submit?actor=${encodeURIComponent(actor)}`, req);
  }

  async dispatchPlan(commandId: string, actor: string): Promise<ApiEnvelope<Task[]>> {
    return post<Task[]>(`/commands/${encodeURIComponent(commandId)}/dispatch?actor=${encodeURIComponent(actor)}`);
  }

  // Simulations
  async startSimulation(req: StartSimulationRequest, actor: string): Promise<ApiEnvelope<SimulationJob>> {
    return post<SimulationJob>(`/simulations/start?actor=${encodeURIComponent(actor)}`, req);
  }

  async updateSimulationStatus(simulationId: string, status: SimulationJob['status']): Promise<ApiEnvelope<SimulationJob>> {
    return patch<SimulationJob>(`/simulations/${encodeURIComponent(simulationId)}?status=${encodeURIComponent(status)}`);
  }

  // Versions
  async createSnapshot(req: CreateSnapshotRequest, actor: string): Promise<ApiEnvelope<VersionSnapshot>> {
    return post<VersionSnapshot>(`/versions/snapshot?actor=${encodeURIComponent(actor)}`, req);
  }

  async rollbackVersion(snapshotId: string, actor: string): Promise<ApiEnvelope<VersionSnapshot>> {
    return post<VersionSnapshot>(`/versions/${encodeURIComponent(snapshotId)}/rollback?actor=${encodeURIComponent(actor)}`);
  }

  // Settings
  async updateSetting(settingId: string, value: RuntimeSetting['value'], actor: string): Promise<ApiEnvelope<RuntimeSetting>> {
    return patch<RuntimeSetting>(`/settings/${encodeURIComponent(settingId)}?value=${encodeURIComponent(String(value))}&actor=${encodeURIComponent(actor)}`);
  }

  async togglePluginFunction(functionName: string, enabled: boolean, actor: string): Promise<ApiEnvelope<PluginFunction>> {
    return patch<PluginFunction>(
      `/functions/${encodeURIComponent(functionName)}/toggle?enabled=${encodeURIComponent(String(enabled))}&actor=${encodeURIComponent(actor)}`,
    );
  }
}

export const realApi = new RealSmartCityApi();
