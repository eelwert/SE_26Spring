import type {
  ApiEnvelope,
  AuditLog,
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
import {
  demoUsers,
  initialAssets,
  initialAuditLogs,
  initialCommands,
  initialFunctions,
  initialHealth,
  initialProjects,
  initialScenes,
  initialSettings,
  initialSimulations,
  initialTasks,
  initialTemplates,
  initialVersions,
} from './mockData';

const DEMO_PASSWORD = 'demo1234';

const makeTraceId = () => `trace-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
const makeId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
const nowIso = () => new Date().toISOString();
const clone = <T>(value: T): T => structuredClone(value);

const wait = async (ms = 420) => {
  await new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
};

const envelope = async <T>(data: T, ms?: number): Promise<ApiEnvelope<T>> => {
  await wait(ms);
  return {
    traceId: makeTraceId(),
    data: clone(data),
  };
};

class MockSmartCityApi {
  private projects = clone(initialProjects);
  private scenes = clone(initialScenes);
  private assets = clone(initialAssets);
  private templates = clone(initialTemplates);
  private tasks = clone(initialTasks);
  private commands = clone(initialCommands);
  private simulations = clone(initialSimulations);
  private auditLogs = clone(initialAuditLogs);
  private versions = clone(initialVersions);
  private functions = clone(initialFunctions);
  private settings = clone(initialSettings);
  private health = clone(initialHealth);

  async login(request: LoginRequest): Promise<ApiEnvelope<Session>> {
    await wait(520);
    const user = demoUsers.find((item) => item.email === request.email || item.role === request.role);

    if (!user || request.password !== DEMO_PASSWORD) {
      throw new Error('账号或密码不正确，请使用演示账号登录。');
    }

    this.appendAudit(user.name, user.role, 'AUTH_LOGIN', user.email, 'info', 'success');

    return envelope(
      {
        token: `mock-token-${user.role}-${Date.now()}`,
        user,
        expiresAt: new Date(Date.now() + 1000 * 60 * 60 * 8).toISOString(),
      },
      120,
    );
  }

  async getWorkspaceBundle(): Promise<ApiEnvelope<WorkspaceBundle>> {
    return envelope(
      {
        projects: this.projects,
        scenes: this.scenes,
        assets: this.assets,
        templates: this.templates,
        tasks: this.tasks,
        commands: this.commands,
        simulations: this.simulations,
        auditLogs: this.auditLogs,
        versions: this.versions,
        functions: this.functions,
        settings: this.settings,
        health: this.health,
      },
      620,
    );
  }

  async getDashboardSummary(): Promise<ApiEnvelope<DashboardSummary>> {
    const runningTasks = this.tasks.filter((task) => task.status === 'running' || task.status === 'queued').length;
    const failedTasks = this.tasks.filter((task) => task.status === 'failed').length;
    const auditWarnings = this.auditLogs.filter((log) => log.severity !== 'info').length;
    const pluginItems = this.health.filter((item) => item.id.includes('blender') || item.id.includes('api') || item.id.includes('llm'));
    const pluginHealthRate = Math.round(pluginItems.reduce((sum, item) => sum + item.successRate, 0) / pluginItems.length);
    const simItems = this.simulations.length || 1;
    const simulationSuccessRate = Math.round((this.simulations.filter((item) => item.status !== 'failed').length / simItems) * 100);

    return envelope({
      projectTotal: this.projects.length,
      runningTasks,
      failedTasks,
      auditWarnings,
      simulationSuccessRate,
      pluginHealthRate,
    });
  }

  async createProject(request: CreateProjectRequest, actor: string): Promise<ApiEnvelope<Project>> {
    const project: Project = {
      id: makeId('prj'),
      name: request.name,
      owner: actor,
      status: 'draft',
      cityScaleKm2: request.cityScaleKm2,
      coordinateSystem: request.coordinateSystem,
      currentVersion: 'v01',
      updatedAt: nowIso(),
      sceneCount: 1,
      tags: request.tags,
    };
    const scene: Scene = {
      id: makeId('scn'),
      projectId: project.id,
      name: '默认场景',
      status: 'editing',
      version: 'v01',
      templateId: 'tpl-waterfront',
      roadType: '慢行优先断面',
      treeType: '国槐 + 银杏混植',
      seatType: '滨水木质长椅',
      treeDensity: 60,
      roadWidth: 8,
      weather: '晴',
      timeOfDay: '14:00',
      objectCount: 120,
      issueCount: 0,
    };

    this.projects = [project, ...this.projects];
    this.scenes = [scene, ...this.scenes];
    this.appendAudit(actor, 'modeler', 'PROJECT_CREATED', project.name, 'info', 'success');

    return envelope(project);
  }

  async updateSceneTemplate(request: UpdateSceneTemplateRequest, actor: string): Promise<ApiEnvelope<{ scene: Scene; task: Task }>> {
    const scene = this.requireScene(request.sceneId);
    const template = this.templates.find((item) => item.id === request.templateId);
    if (!template) {
      throw new Error('模板不存在或已停用。');
    }

    const updatedScene: Scene = {
      ...scene,
      templateId: request.templateId,
      treeType: template.recommendedTree,
      roadType: template.recommendedRoad,
      seatType: template.recommendedSeat,
      treeDensity: request.treeDensity,
      roadWidth: request.roadWidth,
      status: 'editing',
      issueCount:
        request.treeDensity < template.densityRange[0] || request.treeDensity > template.densityRange[1]
          ? scene.issueCount + 1
          : Math.max(0, scene.issueCount - 1),
    };
    this.scenes = this.scenes.map((item) => (item.id === updatedScene.id ? updatedScene : item));

    const task = this.createTaskRecord({
      projectId: updatedScene.projectId,
      sceneId: updatedScene.id,
      functionName: 'apply_template_linkage',
      title: `应用模板：${template.name}`,
      priority: 3,
      params: {
        template_id: request.templateId,
        tree_density: request.treeDensity,
        road_width: request.roadWidth,
      },
      dependsOn: [],
    }, actor, 'success');

    return envelope({ scene: updatedScene, task }, 700);
  }

  async replaceAsset(request: ReplaceAssetRequest, actor: string): Promise<ApiEnvelope<Task>> {
    const asset = this.assets.find((item) => item.id === request.assetId);
    if (!asset) {
      throw new Error('资产不存在。');
    }

    const status = asset.status === 'available' ? 'success' : 'failed';
    const task = this.createTaskRecord(
      {
        projectId: request.projectId,
        sceneId: request.sceneId,
        functionName: 'replace_asset_batch',
        title: `替换${request.targetType}：${asset.name}`,
        priority: asset.status === 'missing' ? 5 : 4,
        params: {
          asset_id: request.assetId,
          target_type: request.targetType,
          fallback_asset: asset.replacementFor ?? null,
        },
        dependsOn: [],
      },
      actor,
      status,
    );
    task.logs =
      asset.status === 'available'
        ? ['schema 校验通过', `资产 ${asset.name} 可用`, '批量替换完成并写入对象映射']
        : ['schema 校验通过', `资产 ${asset.name} 不可用`, `替代建议：${asset.replacementFor ?? '暂无'}`];
    task.errorCode = asset.status === 'available' ? undefined : '2003';
    task.retryable = asset.status !== 'available';

    this.tasks = this.tasks.map((item) => (item.id === task.id ? task : item));
    return envelope(task, 840);
  }

  async solveLayout(request: LayoutRequest, actor: string): Promise<ApiEnvelope<Task>> {
    if (request.points.length < 3) {
      throw new Error('点集至少需要 3 个约束点。');
    }

    const task = this.createTaskRecord(
      {
        projectId: request.projectId,
        sceneId: request.sceneId,
        functionName: 'solve_point_layout',
        title: `点集布局求解（${request.points.length} 点）`,
        priority: 4,
        params: {
          point_set: request.points,
          coordinate_system: this.projects.find((item) => item.id === request.projectId)?.coordinateSystem,
        },
        dependsOn: [],
      },
      actor,
      'success',
    );
    task.logs = ['拓扑校验通过', '几何约束误差 0.31m', '道路与地块布局已更新'];
    this.tasks = this.tasks.map((item) => (item.id === task.id ? task : item));

    return envelope(task, 900);
  }

  async extractSketch(projectId: string, sceneId: string, fileName: string, actor: string): Promise<ApiEnvelope<Task>> {
    const task = this.createTaskRecord(
      {
        projectId,
        sceneId,
        functionName: 'extract_sketch_topology',
        title: `草图点线提取：${fileName}`,
        priority: 4,
        params: {
          attachment_ref: `mock-upload://${fileName}`,
          scale: '1:1000',
          output: 'editable_topology',
        },
        dependsOn: [],
      },
      actor,
      'success',
    );
    task.logs = ['边缘检测完成', '识别道路线段 18 条', '关键拓扑召回率 0.92'];
    task.resultObjects = ['topo-road-18', 'topo-boundary-05'];
    this.tasks = this.tasks.map((item) => (item.id === task.id ? task : item));

    return envelope(task, 980);
  }

  async dispatchTask(request: DispatchTaskRequest, actor: string): Promise<ApiEnvelope<Task>> {
    const func = this.functions.find((item) => item.name === request.functionName);
    if (!func || !func.enabled) {
      throw new Error('函数未注册或已停用，无法进入调度队列。');
    }

    const status = func.risk === 'high' ? 'queued' : 'running';
    const task = this.createTaskRecord(request, actor, status);
    task.logs = ['任务 JSON 已生成', '函数白名单校验通过', status === 'queued' ? '等待二次确认或执行器空闲' : '已下发至插件执行器'];
    task.progress = status === 'queued' ? 12 : 43;
    this.tasks = this.tasks.map((item) => (item.id === task.id ? task : item));

    return envelope(task, 560);
  }

  async retryTask(taskId: string, actor: string): Promise<ApiEnvelope<Task>> {
    const task = this.requireTask(taskId);
    const retried: Task = {
      ...task,
      status: 'running',
      retryable: true,
      progress: 34,
      logs: [...task.logs, '人工触发重试', '重新校验幂等键通过'],
      errorCode: undefined,
    };
    this.tasks = this.tasks.map((item) => (item.id === taskId ? retried : item));
    this.appendAudit(actor, 'modeler', 'TASK_RETRY', task.title, 'warning', 'pending');
    return envelope(retried);
  }

  async submitCommand(request: SubmitCommandRequest, actor: string): Promise<ApiEnvelope<MultimodalCommand>> {
    const text = request.text.trim();
    if (text.length < 6 && request.modalities.length === 1) {
      throw new Error('指令信息不足，请补充目标区域、对象或约束。');
    }

    const lowerText = text.toLowerCase();
    const wantsWeather = text.includes('天气') || text.includes('小雨') || text.includes('傍晚') || lowerText.includes('weather');
    const wantsTrees = text.includes('树') || text.includes('绿化') || text.includes('密度');
    const wantsSimulation = text.includes('仿真') || text.includes('车辆') || text.includes('人群');
    const wantsSketch = request.modalities.includes('sketch') || text.includes('草图') || text.includes('点线');

    const plan = [
      ...(wantsTrees
        ? [
            {
              id: makeId('node'),
              funcName: 'apply_template_linkage',
              title: '联动植被与道路模板',
              status: 'approved' as const,
              dependsOn: [],
              params: { tree_density: 78, rule: 'template_linkage' },
            },
          ]
        : []),
      ...(wantsWeather
        ? [
            {
              id: makeId('node'),
              funcName: 'set_weather_lighting',
              title: '标准化天气与天色参数',
              status: 'approved' as const,
              dependsOn: [],
              params: { weather: '小雨', time_of_day: '18:30', visibility: 0.68 },
            },
          ]
        : []),
      ...(wantsSketch
        ? [
            {
              id: makeId('node'),
              funcName: 'extract_sketch_topology',
              title: '提取草图点线拓扑',
              status: 'planned' as const,
              dependsOn: [],
              params: { attachment_count: request.attachmentNames.length, output: 'topology_graph' },
            },
          ]
        : []),
      ...(wantsSimulation
        ? [
            {
              id: makeId('node'),
              funcName: 'run_traffic_simulation',
              title: '调度车辆/人群仿真',
              status: 'planned' as const,
              dependsOn: [],
              params: { rules_version: 'traffic-r3.2', seed: 20260506 },
            },
          ]
        : []),
    ];

    const finalPlan =
      plan.length > 0
        ? plan
        : [
            {
              id: makeId('node'),
              funcName: 'dispatch_blender_job',
              title: '生成通用 Blender 插件任务',
              status: 'blocked' as const,
              dependsOn: [],
              params: { reason: '需要澄清目标对象' },
            },
          ];
    const confidence = Math.min(0.96, 0.58 + finalPlan.length * 0.12 + request.modalities.length * 0.04);

    const command: MultimodalCommand = {
      id: makeId('cmd'),
      projectId: request.projectId,
      sceneId: request.sceneId,
      modality: request.modalities,
      rawInput: text || `附件指令：${request.attachmentNames.join(', ')}`,
      intentTag: wantsSimulation
        ? 'simulation_orchestration'
        : wantsSketch
          ? 'sketch_to_topology'
          : wantsWeather && wantsTrees
            ? 'weather_and_green_space_adjustment'
            : 'general_scene_edit',
      confidence,
      slots: {
        area: '当前场景',
        weather: wantsWeather ? '小雨/傍晚' : '未指定',
        tree_density: wantsTrees ? 78 : '保持',
        simulation: wantsSimulation,
        attachments: request.attachmentNames.length,
      },
      plan: finalPlan,
      explanation:
        confidence >= 0.72
          ? '已将多模态输入转换为白名单函数计划，执行前可继续调整参数。'
          : '置信度偏低，建议补充目标范围或选择对象后再执行。',
      createdAt: nowIso(),
      needsClarification: confidence < 0.72,
    };

    this.commands = [command, ...this.commands];
    this.appendAudit(actor, 'analyst', 'MULTIMODAL_PLAN_CREATED', command.intentTag, confidence >= 0.72 ? 'info' : 'warning', 'success');
    return envelope(command, 980);
  }

  async dispatchPlan(commandId: string, actor: string): Promise<ApiEnvelope<Task[]>> {
    const command = this.commands.find((item) => item.id === commandId);
    if (!command) {
      throw new Error('函数计划不存在。');
    }
    if (command.needsClarification) {
      throw new Error('该计划需要澄清，不能自动执行。');
    }

    const tasks = command.plan.map((node, index) =>
      this.createTaskRecord(
        {
          projectId: command.projectId,
          sceneId: command.sceneId,
          functionName: node.funcName,
          title: node.title,
          priority: 3 + index,
          params: node.params,
          dependsOn: node.dependsOn,
        },
        actor,
        'queued',
      ),
    );
    this.commands = this.commands.map((item) =>
      item.id === command.id
        ? {
            ...item,
            plan: item.plan.map((node) => ({ ...node, status: 'dispatched' })),
          }
        : item,
    );
    this.appendAudit(actor, 'analyst', 'FUNCTION_PLAN_DISPATCHED', command.intentTag, 'info', 'pending');
    return envelope(tasks, 720);
  }

  async startSimulation(request: StartSimulationRequest, actor: string): Promise<ApiEnvelope<SimulationJob>> {
    const simulation: SimulationJob = {
      id: makeId('sim'),
      projectId: request.projectId,
      sceneId: request.sceneId,
      type: request.type,
      status: 'running',
      rulesVersion: request.rulesVersion,
      seed: request.seed,
      progress: 18,
      playbackTime: 0,
      durationMinutes: request.durationMinutes,
      startedAt: nowIso(),
      metrics: [
        { name: '拥堵指数', value: 0.42, unit: '', delta: -0.03, severity: 'normal' },
        { name: '平均速度', value: 31.5, unit: 'km/h', delta: 2.1, severity: 'good' },
        { name: '人车冲突', value: 7, unit: '处', delta: -2, severity: 'normal' },
      ],
    };
    this.simulations = [simulation, ...this.simulations];
    this.createTaskRecord(
      {
        projectId: request.projectId,
        sceneId: request.sceneId,
        functionName: request.type === 'crowd' ? 'run_crowd_simulation' : 'run_traffic_simulation',
        title: `启动${request.type === 'crowd' ? '人群' : request.type === 'traffic' ? '车辆' : '综合'}仿真`,
        priority: 5,
        params: {
          rules_version: request.rulesVersion,
          seed: request.seed,
          duration_minutes: request.durationMinutes,
        },
        dependsOn: [],
      },
      actor,
      'running',
    );
    return envelope(simulation, 760);
  }

  async updateSimulationStatus(simulationId: string, status: SimulationJob['status']): Promise<ApiEnvelope<SimulationJob>> {
    const simulation = this.simulations.find((item) => item.id === simulationId);
    if (!simulation) {
      throw new Error('仿真任务不存在。');
    }
    const updated: SimulationJob = {
      ...simulation,
      status,
      progress: status === 'completed' ? 100 : simulation.progress,
    };
    this.simulations = this.simulations.map((item) => (item.id === simulationId ? updated : item));
    return envelope(updated, 180);
  }

  async createSnapshot(request: CreateSnapshotRequest, actor: string): Promise<ApiEnvelope<VersionSnapshot>> {
    const currentVersions = this.versions.filter((item) => item.sceneId === request.sceneId);
    const newest = currentVersions[0];
    const nextNumber = currentVersions.length + 1;
    const version = `v${String(nextNumber).padStart(2, '0')}`;
    const snapshot: VersionSnapshot = {
      id: makeId('ver'),
      projectId: request.projectId,
      sceneId: request.sceneId,
      version,
      parentVersion: newest?.version,
      author: actor,
      createdAt: nowIso(),
      summary: request.summary,
      changeCount: Math.floor(12 + Math.random() * 44),
      rollbackable: true,
    };
    this.versions = [snapshot, ...this.versions];
    this.projects = this.projects.map((project) =>
      project.id === request.projectId ? { ...project, currentVersion: version, updatedAt: nowIso() } : project,
    );
    this.scenes = this.scenes.map((scene) => (scene.id === request.sceneId ? { ...scene, version } : scene));
    this.appendAudit(actor, 'modeler', 'VERSION_SNAPSHOT_CREATED', version, 'info', 'success');
    return envelope(snapshot, 520);
  }

  async rollbackVersion(snapshotId: string, actor: string): Promise<ApiEnvelope<VersionSnapshot>> {
    const snapshot = this.versions.find((item) => item.id === snapshotId);
    if (!snapshot) {
      throw new Error('快照不存在。');
    }
    this.scenes = this.scenes.map((scene) => (scene.id === snapshot.sceneId ? { ...scene, version: snapshot.version, status: 'editing' } : scene));
    this.projects = this.projects.map((project) =>
      project.id === snapshot.projectId ? { ...project, currentVersion: snapshot.version, updatedAt: nowIso() } : project,
    );
    this.appendAudit(actor, 'admin', 'VERSION_ROLLBACK', snapshot.version, 'critical', 'success');
    return envelope(snapshot, 680);
  }

  async updateSetting(settingId: string, value: RuntimeSetting['value'], actor: string): Promise<ApiEnvelope<RuntimeSetting>> {
    const setting = this.settings.find((item) => item.id === settingId);
    if (!setting) {
      throw new Error('设置不存在。');
    }
    if (setting.locked) {
      throw new Error('该设置已锁定，不能在前端修改。');
    }
    const updated = { ...setting, value };
    this.settings = this.settings.map((item) => (item.id === settingId ? updated : item));
    this.appendAudit(actor, 'admin', 'RUNTIME_SETTING_UPDATE', setting.title, 'warning', 'success');
    return envelope(updated, 360);
  }

  async togglePluginFunction(functionName: string, enabled: boolean, actor: string): Promise<ApiEnvelope<PluginFunction>> {
    const pluginFunction = this.functions.find((item) => item.name === functionName);
    if (!pluginFunction) {
      throw new Error('插件函数不存在。');
    }
    const updated = { ...pluginFunction, enabled };
    this.functions = this.functions.map((item) => (item.name === functionName ? updated : item));
    this.appendAudit(actor, 'admin', 'PLUGIN_WHITELIST_UPDATE', functionName, pluginFunction.risk === 'high' ? 'critical' : 'warning', 'success');
    return envelope(updated, 360);
  }

  private createTaskRecord(request: DispatchTaskRequest, actor: string, status: Task['status']): Task {
    const task: Task = {
      id: makeId('task'),
      traceId: makeTraceId(),
      projectId: request.projectId,
      sceneId: request.sceneId,
      title: request.title,
      functionName: request.functionName,
      status,
      priority: request.priority,
      progress: status === 'success' ? 100 : status === 'failed' ? 62 : status === 'queued' ? 8 : 35,
      createdBy: actor,
      createdAt: nowIso(),
      elapsedMs: status === 'success' ? 760 + Math.floor(Math.random() * 840) : status === 'failed' ? 2100 : 0,
      dependsOn: request.dependsOn,
      retryable: status === 'failed',
      params: request.params,
      resultObjects: status === 'success' ? [`obj-${Math.random().toString(16).slice(2, 7)}`] : [],
      logs:
        status === 'failed'
          ? ['任务已生成', '参数校验失败或外部节点异常']
          : ['任务已生成', '参数 schema 校验通过', status === 'success' ? '回执 success' : '等待执行回执'],
      errorCode: status === 'failed' ? '2004' : undefined,
    };
    this.tasks = [task, ...this.tasks];
    const auditResult: AuditLog['result'] =
      status === 'failed' ? 'failed' : status === 'queued' || status === 'running' || status === 'validating' ? 'pending' : 'success';
    this.appendAudit(actor, 'modeler', `TASK_${status.toUpperCase()}`, request.functionName, status === 'failed' ? 'warning' : 'info', auditResult);
    return task;
  }

  private requireScene(sceneId: string): Scene {
    const scene = this.scenes.find((item) => item.id === sceneId);
    if (!scene) {
      throw new Error('场景不存在或已归档。');
    }
    return scene;
  }

  private requireTask(taskId: string): Task {
    const task = this.tasks.find((item) => item.id === taskId);
    if (!task) {
      throw new Error('任务不存在。');
    }
    return task;
  }

  private appendAudit(
    actor: string,
    role: AuditLog['role'],
    eventType: string,
    target: string,
    severity: AuditLog['severity'],
    result: AuditLog['result'],
  ) {
    this.auditLogs = [
      {
        id: makeId('log'),
        traceId: makeTraceId(),
        actor,
        role,
        eventType,
        target,
        severity,
        result,
        evidenceHash: `sha256:${Math.random().toString(16).slice(2, 10)}`,
        createdAt: nowIso(),
      },
      ...this.auditLogs,
    ];
  }
}

export const mockApi = new MockSmartCityApi();
