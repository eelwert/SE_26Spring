import { FormEvent, useMemo, useState } from 'react';
import { Download, FileUp, Plus, Replace, Save, SlidersHorizontal } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import type { LayoutPoint } from '../types/domain';
import { Button, EmptyState, Field, IconButton, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';

const targetTypes = ['tree', 'road_material', 'seat', 'building_facade', 'vehicle'];

const defaultPoints: LayoutPoint[] = [
  { id: 'p1', x: 0, y: 0, label: '主入口', constraint: 'road-node' },
  { id: 'p2', x: 120, y: 32, label: '滨水转角', constraint: 'waterfront' },
  { id: 'p3', x: 240, y: 76, label: '商业节点', constraint: 'facility' },
  { id: 'p4', x: 320, y: 10, label: '边界控制点', constraint: 'boundary' },
];

export function ProjectsPage() {
  const { hasPermission } = useSession();
  const {
    projects,
    scenes,
    selectedProject,
    selectedScene,
    selectedProjectId,
    selectedSceneId,
    templates,
    assets,
    tasks,
    setSelectedProjectId,
    setSelectedSceneId,
    createProject,
    updateSceneTemplate,
    replaceAsset,
    solveLayout,
    extractSketch,
  } = useWorkspace();
  const [projectName, setProjectName] = useState('');
  const [projectScale, setProjectScale] = useState(1.0);
  const [projectTags, setProjectTags] = useState('样板, 滨水');
  const [templateId, setTemplateId] = useState(selectedScene?.templateId ?? 'tpl-waterfront');
  const [treeDensity, setTreeDensity] = useState(selectedScene?.treeDensity ?? 60);
  const [roadWidth, setRoadWidth] = useState(selectedScene?.roadWidth ?? 8);
  const [assetId, setAssetId] = useState(assets[0]?.id ?? '');
  const [targetType, setTargetType] = useState(targetTypes[0]);
  const [points, setPoints] = useState(defaultPoints);
  const [sketchFile, setSketchFile] = useState('river-layout-sketch.png');
  const [busyAction, setBusyAction] = useState<string | null>(null);

  const canWrite = hasPermission('project:write');
  const projectScenes = scenes.filter((scene) => scene.projectId === selectedProjectId);
  const sceneTasks = useMemo(
    () => tasks.filter((task) => task.sceneId === selectedSceneId).slice(0, 6),
    [selectedSceneId, tasks],
  );
  const selectedTemplate = templates.find((template) => template.id === templateId);

  const guardedAction = async (key: string, action: () => Promise<unknown>) => {
    setBusyAction(key);
    try {
      await action();
    } finally {
      setBusyAction(null);
    }
  };

  const handleCreateProject = async (event: FormEvent) => {
    event.preventDefault();
    await guardedAction('create-project', async () =>
      createProject({
        name: projectName || '未命名智能城市场景',
        cityScaleKm2: projectScale,
        coordinateSystem: 'CGCS2000 / Tianjin Local Grid',
        tags: projectTags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean),
      }),
    );
    setProjectName('');
  };

  const handleTemplateUpdate = async () => {
    if (!selectedSceneId) return;
    await guardedAction('template', async () =>
      updateSceneTemplate({
        sceneId: selectedSceneId,
        templateId,
        treeDensity,
        roadWidth,
      }),
    );
  };

  const handleReplaceAsset = async () => {
    if (!selectedProjectId || !selectedSceneId || !assetId) return;
    await guardedAction('asset', async () =>
      replaceAsset({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        assetId,
        targetType,
      }),
    );
  };

  const handleLayout = async () => {
    if (!selectedProjectId || !selectedSceneId) return;
    await guardedAction('layout', async () =>
      solveLayout({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        points,
      }),
    );
  };

  const handleSketch = async () => {
    if (!selectedSceneId) return;
    await guardedAction('sketch', async () => extractSketch(selectedSceneId, sketchFile || 'uploaded-sketch.png'));
  };

  return (
    <div className="page-stack">
      <SectionHeader title="项目与场景管理" description="项目隔离、场景上下文、资产替换、模板联动、点集与草图布局。" />

      <div className="project-layout">
        <Panel className="project-list-panel">
          <SectionHeader title="项目列表" />
          <div className="project-list">
            {projects.map((project) => (
              <button
                key={project.id}
                className={`project-item ${project.id === selectedProjectId ? 'active' : ''}`}
                type="button"
                onClick={() => setSelectedProjectId(project.id)}
              >
                <div>
                  <strong>{project.name}</strong>
                  <span>{project.coordinateSystem}</span>
                </div>
                <StatusBadge status={project.status} />
                <small>
                  {project.currentVersion} / {project.cityScaleKm2}km²
                </small>
              </button>
            ))}
          </div>
          <form className="compact-form" onSubmit={(event) => void handleCreateProject(event)}>
            <Field label="新项目名称">
              <input value={projectName} onChange={(event) => setProjectName(event.target.value)} disabled={!canWrite} />
            </Field>
            <Field label="规模 km²">
              <input type="number" min={0.1} step={0.1} value={projectScale} onChange={(event) => setProjectScale(Number(event.target.value))} disabled={!canWrite} />
            </Field>
            <Field label="标签">
              <input value={projectTags} onChange={(event) => setProjectTags(event.target.value)} disabled={!canWrite} />
            </Field>
            <Button type="submit" isLoading={busyAction === 'create-project'} disabled={!canWrite}>
              <Plus size={16} />
              新建项目
            </Button>
          </form>
        </Panel>

        <div className="project-main">
          <Panel>
            <SectionHeader title="场景上下文" />
            {selectedProject && selectedScene ? (
              <div className="scene-context-grid">
                <div>
                  <span>项目</span>
                  <strong>{selectedProject.name}</strong>
                </div>
                <div>
                  <span>当前版本</span>
                  <strong>{selectedProject.currentVersion}</strong>
                </div>
                <div>
                  <span>场景</span>
                  <select value={selectedSceneId ?? ''} onChange={(event) => setSelectedSceneId(event.target.value)}>
                    {projectScenes.map((scene) => (
                      <option key={scene.id} value={scene.id}>
                        {scene.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <span>对象数量</span>
                  <strong>{selectedScene.objectCount.toLocaleString()}</strong>
                </div>
                <div>
                  <span>道路</span>
                  <strong>{selectedScene.roadType}</strong>
                </div>
                <div>
                  <span>树木</span>
                  <strong>{selectedScene.treeType}</strong>
                </div>
              </div>
            ) : (
              <EmptyState title="无项目上下文" description="选择或创建项目后加载场景。" />
            )}
          </Panel>

          <div className="two-column">
            <Panel>
              <SectionHeader title="模板联动配置" action={<StatusBadge status={selectedScene?.status ?? 'ready'} />} />
              <div className="form-grid">
                <Field label="模板">
                  <select value={templateId} onChange={(event) => setTemplateId(event.target.value)} disabled={!canWrite}>
                    {templates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="树木密度">
                  <input type="range" min={20} max={90} value={treeDensity} onChange={(event) => setTreeDensity(Number(event.target.value))} disabled={!canWrite} />
                </Field>
                <Field label="道路宽度">
                  <input type="number" min={4} max={24} value={roadWidth} onChange={(event) => setRoadWidth(Number(event.target.value))} disabled={!canWrite} />
                </Field>
              </div>
              {selectedTemplate ? (
                <div className="template-hints">
                  <div>
                    <strong>{selectedTemplate.style}</strong>
                    <span>{selectedTemplate.rulesVersion}</span>
                  </div>
                  <span>{selectedTemplate.conflictHints[0]}</span>
                </div>
              ) : null}
              <Button onClick={() => void handleTemplateUpdate()} isLoading={busyAction === 'template'} disabled={!selectedSceneId || !canWrite}>
                <SlidersHorizontal size={16} />
                应用联动
              </Button>
            </Panel>

            <Panel>
              <SectionHeader title="2D / 3D 资产替换" />
              <div className="form-grid">
                <Field label="资产">
                  <select value={assetId} onChange={(event) => setAssetId(event.target.value)} disabled={!hasPermission('asset:replace')}>
                    {assets.map((asset) => (
                      <option key={asset.id} value={asset.id}>
                        {asset.name} / {asset.format}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="目标对象">
                  <select value={targetType} onChange={(event) => setTargetType(event.target.value)} disabled={!hasPermission('asset:replace')}>
                    {targetTypes.map((target) => (
                      <option key={target} value={target}>
                        {target}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              <div className="asset-status-list">
                {assets.slice(0, 4).map((asset) => (
                  <div key={asset.id}>
                    <span>{asset.name}</span>
                    <StatusBadge status={asset.status} />
                  </div>
                ))}
              </div>
              <Button onClick={() => void handleReplaceAsset()} isLoading={busyAction === 'asset'} disabled={!hasPermission('asset:replace')}>
                <Replace size={16} />
                下发替换
              </Button>
            </Panel>
          </div>

          <div className="two-column">
            <Panel>
              <SectionHeader title="点集精确布局" />
              <div className="point-editor">
                {points.map((point, index) => (
                  <div key={point.id} className="point-row">
                    <span>{point.label}</span>
                    <input
                      type="number"
                      value={point.x}
                      onChange={(event) =>
                        setPoints((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, x: Number(event.target.value) } : item)))
                      }
                    />
                    <input
                      type="number"
                      value={point.y}
                      onChange={(event) =>
                        setPoints((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, y: Number(event.target.value) } : item)))
                      }
                    />
                  </div>
                ))}
              </div>
              <Button onClick={() => void handleLayout()} isLoading={busyAction === 'layout'} disabled={!hasPermission('layout:edit')}>
                <Save size={16} />
                求解布局
              </Button>
            </Panel>

            <Panel>
              <SectionHeader title="草图点线提取" />
              <div className="sketch-dropzone">
                <FileUp size={26} />
                <input value={sketchFile} onChange={(event) => setSketchFile(event.target.value)} />
                <span>PNG/JPEG / 20MB 以内</span>
              </div>
              <Button onClick={() => void handleSketch()} isLoading={busyAction === 'sketch'} disabled={!hasPermission('layout:edit')}>
                <Download size={16} />
                提取拓扑
              </Button>
            </Panel>
          </div>

          <Panel>
            <SectionHeader title="场景任务记录" />
            {sceneTasks.length ? (
              <div className="table-list">
                {sceneTasks.map((task) => (
                  <div key={task.id} className="table-row task-row">
                    <div>
                      <strong>{task.title}</strong>
                      <span>{task.functionName}</span>
                    </div>
                    <StatusBadge status={task.status} />
                    <div className="progress-cell">
                      <ProgressBar value={task.progress} />
                      <small>{task.progress}%</small>
                    </div>
                    <IconButton label="查看任务参数">
                      <Download size={16} />
                    </IconButton>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="暂无任务" description="模板、资产、布局操作会在这里留下任务记录。" />
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
