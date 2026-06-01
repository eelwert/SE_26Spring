import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import type {
  Asset,
  AuditLog,
  CreateProjectRequest,
  CreateSnapshotRequest,
  DashboardSummary,
  DispatchTaskRequest,
  LayoutRequest,
  MultimodalCommand,
  PluginFunction,
  Project,
  ReplaceAssetRequest,
  RuntimeSetting,
  Scene,
  SceneTemplate,
  SimulationJob,
  StartSimulationRequest,
  SubmitCommandRequest,
  SystemHealthItem,
  Task,
  UpdateSceneTemplateRequest,
  VersionSnapshot,
  WorkspaceBundle,
} from '../types/domain';
import { useSession } from './SessionContext';

interface WorkspaceContextValue {
  isLoading: boolean;
  error: string | null;
  selectedProjectId: string | null;
  selectedSceneId: string | null;
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
  summary: DashboardSummary | null;
  selectedProject?: Project;
  selectedScene?: Scene;
  setSelectedProjectId: (projectId: string) => void;
  setSelectedSceneId: (sceneId: string) => void;
  refreshWorkspace: () => Promise<void>;
  clearError: () => void;
  createProject: (request: CreateProjectRequest) => Promise<Project>;
  updateSceneTemplate: (request: UpdateSceneTemplateRequest) => Promise<void>;
  replaceAsset: (request: ReplaceAssetRequest) => Promise<Task>;
  solveLayout: (request: LayoutRequest) => Promise<Task>;
  extractSketch: (sceneId: string, fileName: string) => Promise<Task>;
  dispatchTask: (request: DispatchTaskRequest) => Promise<Task>;
  retryTask: (taskId: string) => Promise<void>;
  submitCommand: (request: SubmitCommandRequest) => Promise<MultimodalCommand>;
  dispatchPlan: (commandId: string) => Promise<Task[]>;
  startSimulation: (request: StartSimulationRequest) => Promise<SimulationJob>;
  updateSimulationStatus: (simulationId: string, status: SimulationJob['status']) => Promise<void>;
  createSnapshot: (request: CreateSnapshotRequest) => Promise<VersionSnapshot>;
  rollbackVersion: (snapshotId: string) => Promise<void>;
  updateSetting: (settingId: string, value: RuntimeSetting['value']) => Promise<void>;
  togglePluginFunction: (functionName: string, enabled: boolean) => Promise<void>;
}

const emptyBundle: WorkspaceBundle = {
  projects: [],
  scenes: [],
  assets: [],
  templates: [],
  tasks: [],
  commands: [],
  simulations: [],
  auditLogs: [],
  versions: [],
  functions: [],
  settings: [],
  health: [],
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { session, isAuthenticated } = useSession();
  const [bundle, setBundle] = useState<WorkspaceBundle>(emptyBundle);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [selectedProjectId, setSelectedProjectIdState] = useState<string | null>(null);
  const [selectedSceneId, setSelectedSceneIdState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const actor = session?.user.name ?? '演示用户';

  const applyBundle = useCallback((nextBundle: WorkspaceBundle) => {
    setBundle(nextBundle);
    setSelectedProjectIdState((current) => current ?? nextBundle.projects[0]?.id ?? null);
    setSelectedSceneIdState((current) => {
      if (current && nextBundle.scenes.some((scene) => scene.id === current)) {
        return current;
      }
      const projectId = nextBundle.projects[0]?.id;
      return nextBundle.scenes.find((scene) => scene.projectId === projectId)?.id ?? nextBundle.scenes[0]?.id ?? null;
    });
  }, []);

  const refreshWorkspace = useCallback(async () => {
    if (!isAuthenticated) {
      setBundle(emptyBundle);
      setSummary(null);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [workspaceResponse, summaryResponse] = await Promise.all([api.getWorkspaceBundle(), api.getDashboardSummary()]);
      applyBundle(workspaceResponse.data);
      setSummary(summaryResponse.data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '工作区加载失败。');
    } finally {
      setIsLoading(false);
    }
  }, [applyBundle, isAuthenticated]);

  useEffect(() => {
    void refreshWorkspace();
  }, [refreshWorkspace]);

  // Poll backend every 3s for task updates (simpler than WebSocket)
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/workspace/bundle', { cache: 'no-store' });
        const envelope = await res.json() as { data: WorkspaceBundle };
        if (envelope?.data?.tasks) {
          setBundle((prev) => ({ ...prev, tasks: envelope.data.tasks }));
        }
      } catch { /* backend not reachable yet */ }
    };
    const timer = setInterval(poll, 3000);
    return () => clearInterval(timer);
  }, []);

  const selectedProject = useMemo(
    () => bundle.projects.find((project) => project.id === selectedProjectId),
    [bundle.projects, selectedProjectId],
  );
  const selectedScene = useMemo(
    () => bundle.scenes.find((scene) => scene.id === selectedSceneId),
    [bundle.scenes, selectedSceneId],
  );

  const setSelectedProjectId = useCallback(
    (projectId: string) => {
      setSelectedProjectIdState(projectId);
      const firstScene = bundle.scenes.find((scene) => scene.projectId === projectId);
      setSelectedSceneIdState(firstScene?.id ?? null);
    },
    [bundle.scenes],
  );

  const setSelectedSceneId = useCallback((sceneId: string) => {
    setSelectedSceneIdState(sceneId);
  }, []);

  const mutate = useCallback(async <T,>(operation: () => Promise<T>, after?: () => Promise<void>) => {
    setError(null);
    try {
      const result = await operation();
      await refreshWorkspace();
      if (after) {
        await after();
      }
      return result;
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : '操作失败。';
      setError(message);
      throw caught;
    }
  }, [refreshWorkspace]);

  const createProject = useCallback(
    async (request: CreateProjectRequest) =>
      mutate(async () => {
        const response = await api.createProject(request, actor);
        setSelectedProjectIdState(response.data.id);
        return response.data;
      }),
    [actor, mutate],
  );

  const updateSceneTemplate = useCallback(
    async (request: UpdateSceneTemplateRequest) => {
      await mutate(async () => {
        await api.updateSceneTemplate(request, actor);
      });
    },
    [actor, mutate],
  );

  const replaceAsset = useCallback(
    async (request: ReplaceAssetRequest) =>
      mutate(async () => {
        const response = await api.replaceAsset(request, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const solveLayout = useCallback(
    async (request: LayoutRequest) =>
      mutate(async () => {
        const response = await api.solveLayout(request, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const extractSketch = useCallback(
    async (sceneId: string, fileName: string) => {
      if (!selectedProjectId) {
        throw new Error('请先选择项目。');
      }
      return mutate(async () => {
        const response = await api.extractSketch(selectedProjectId, sceneId, fileName, actor);
        return response.data;
      });
    },
    [actor, mutate, selectedProjectId],
  );

  const dispatchTask = useCallback(
    async (request: DispatchTaskRequest) =>
      mutate(async () => {
        const response = await api.dispatchTask(request, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const retryTask = useCallback(
    async (taskId: string) => {
      await mutate(async () => {
        await api.retryTask(taskId, actor);
      });
    },
    [actor, mutate],
  );

  const submitCommand = useCallback(
    async (request: SubmitCommandRequest) =>
      mutate(async () => {
        const response = await api.submitCommand(request, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const dispatchPlan = useCallback(
    async (commandId: string) =>
      mutate(async () => {
        const response = await api.dispatchPlan(commandId, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const startSimulation = useCallback(
    async (request: StartSimulationRequest) =>
      mutate(async () => {
        const response = await api.startSimulation(request, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const updateSimulationStatus = useCallback(
    async (simulationId: string, status: SimulationJob['status']) => {
      await mutate(async () => {
        await api.updateSimulationStatus(simulationId, status);
      });
    },
    [mutate],
  );

  const createSnapshot = useCallback(
    async (request: CreateSnapshotRequest) =>
      mutate(async () => {
        const response = await api.createSnapshot(request, actor);
        return response.data;
      }),
    [actor, mutate],
  );

  const rollbackVersion = useCallback(
    async (snapshotId: string) => {
      await mutate(async () => {
        await api.rollbackVersion(snapshotId, actor);
      });
    },
    [actor, mutate],
  );

  const updateSetting = useCallback(
    async (settingId: string, value: RuntimeSetting['value']) => {
      await mutate(async () => {
        await api.updateSetting(settingId, value, actor);
      });
    },
    [actor, mutate],
  );

  const togglePluginFunction = useCallback(
    async (functionName: string, enabled: boolean) => {
      await mutate(async () => {
        await api.togglePluginFunction(functionName, enabled, actor);
      });
    },
    [actor, mutate],
  );

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      isLoading,
      error,
      selectedProjectId,
      selectedSceneId,
      projects: bundle.projects,
      scenes: bundle.scenes,
      assets: bundle.assets,
      templates: bundle.templates,
      tasks: bundle.tasks,
      commands: bundle.commands,
      simulations: bundle.simulations,
      auditLogs: bundle.auditLogs,
      versions: bundle.versions,
      functions: bundle.functions,
      settings: bundle.settings,
      health: bundle.health,
      summary,
      selectedProject,
      selectedScene,
      setSelectedProjectId,
      setSelectedSceneId,
      refreshWorkspace,
      clearError: () => setError(null),
      createProject,
      updateSceneTemplate,
      replaceAsset,
      solveLayout,
      extractSketch,
      dispatchTask,
      retryTask,
      submitCommand,
      dispatchPlan,
      startSimulation,
      updateSimulationStatus,
      createSnapshot,
      rollbackVersion,
      updateSetting,
      togglePluginFunction,
    }),
    [
      isLoading,
      error,
      selectedProjectId,
      selectedSceneId,
      bundle,
      summary,
      selectedProject,
      selectedScene,
      setSelectedProjectId,
      setSelectedSceneId,
      refreshWorkspace,
      createProject,
      updateSceneTemplate,
      replaceAsset,
      solveLayout,
      extractSketch,
      dispatchTask,
      retryTask,
      submitCommand,
      dispatchPlan,
      startSimulation,
      updateSimulationStatus,
      createSnapshot,
      rollbackVersion,
      updateSetting,
      togglePluginFunction,
    ],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used inside WorkspaceProvider');
  }
  return context;
}
