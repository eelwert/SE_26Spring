import { useMemo, useState } from 'react';
import { Brush, ExternalLink, FileImage, Map, PackagePlus, SlidersHorizontal, SquarePen } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, Field, MetricCard, Panel, SectionHeader, StatusBadge } from '../components/ui';

const templateNumberMap: Record<string, string> = {
  'tpl-waterfront': '0',
  'tpl-commercial': '1',
  'tpl-transit': '2',
  'tpl-campus': '0',
};

const roadTextureOptions = [
  { id: 'road_4_clean', label: 'Road 4 clean', note: '干净沥青贴图，适合主干路' },
  { id: 'road_8_dirty', label: 'Road 8 dirty', note: '旧化路面，适合生活街区' },
  { id: 'spongebob_fun', label: 'SpongeBob road', note: '趣味展示纹理，可用于演示' },
];

const furnitureAssets = [
  { id: 'wooden_picnic_table', label: '木质野餐桌', count: 5, spacing: 8 },
  { id: 'metal_trash_can', label: '金属垃圾桶', count: 12, spacing: 14 },
  { id: 'small_lpg_tank', label: '小型设施罐', count: 3, spacing: 18 },
];

export function ModelerPortalPage() {
  const {
    selectedProjectId,
    selectedSceneId,
    selectedProject,
    selectedScene,
    templates,
    assets,
    tasks,
    updateSceneTemplate,
    dispatchTask,
    submitCommand,
  } = useWorkspace();
  const [templateId, setTemplateId] = useState(selectedScene?.templateId ?? 'tpl-waterfront');
  const [templateNumber, setTemplateNumber] = useState(templateNumberMap[selectedScene?.templateId ?? 'tpl-waterfront'] ?? '0');
  const [roadTexture, setRoadTexture] = useState(roadTextureOptions[0].id);
  const [assetId, setAssetId] = useState(furnitureAssets[0].id);
  const [assetCount, setAssetCount] = useState(furnitureAssets[0].count);
  const [assetSpacing, setAssetSpacing] = useState(furnitureAssets[0].spacing);
  const [pointsText, setPointsText] = useState('(0,0),(10,0),(10,10)');
  const [sketchName, setSketchName] = useState('road-sketch.png');
  const [sketchBase64, setSketchBase64] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [pluginNotice, setPluginNotice] = useState<string | null>(null);

  const sceneTasks = useMemo(
    () => tasks.filter((task) => !selectedSceneId || task.sceneId === selectedSceneId).slice(0, 5),
    [selectedSceneId, tasks],
  );
  const selectedTemplate = templates.find((item) => item.id === templateId);

  const runAction = async (key: string, action: () => Promise<unknown>) => {
    setBusyKey(key);
    try {
      await action();
    } finally {
      setBusyKey(null);
    }
  };

  const handleTemplateApply = async () => {
    if (!selectedSceneId) return;
    await runAction('template', async () => {
      await updateSceneTemplate({
        sceneId: selectedSceneId,
        templateId,
        treeDensity: selectedScene?.treeDensity ?? 60,
        roadWidth: selectedScene?.roadWidth ?? 8,
      });
    });
  };

  const handleDispatchFunction = async (functionName: string, title: string, params: Record<string, unknown>, key: string) => {
    if (!selectedProjectId || !selectedSceneId) return;
    await runAction(key, async () => {
      await dispatchTask({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        functionName,
        title,
        priority: 4,
        params,
        dependsOn: [],
      });
    });
  };

  const handleSketchSubmit = async () => {
    if (!selectedProjectId || !selectedSceneId || !sketchBase64) return;
    await runAction('sketch', async () => {
      await submitCommand({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        text: '根据手绘草图提取道路点线拓扑，并应用到当前城市场景。',
        modalities: ['sketch'],
        attachmentNames: [sketchName || 'road-sketch.png'],
        imageBase64: sketchBase64,
      });
    });
  };

  const handleSketchFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSketchName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      setSketchBase64(result.includes(',') ? result.split(',')[1] : result);
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="page-stack role-portal">
      <section className="role-hero modeler-hero">
        <div>
          <span className="eyebrow">/modeler</span>
          <h1>场景建模师门户</h1>
          <p>{selectedProject && selectedScene ? `${selectedProject.name} / ${selectedScene.name}` : '选择项目后配置 Blender 城市场景。'}</p>
        </div>
        <div className="hero-actions">
          <Button
            onClick={() => {
              setPluginNotice('已模拟从主系统跳转至 Blender 插件系统。演示时可同步打开插件面板或播放演示视频。');
              window.alert('进入 Blender 插件系统：请在 Blender 侧边栏打开 LLM City Generator 面板。');
            }}
          >
            <ExternalLink size={16} />
            进入 Blender 插件系统
          </Button>
        </div>
      </section>

      {pluginNotice ? (
        <Panel>
          <div className="notice-row">
            <ExternalLink size={18} />
            <span>{pluginNotice}</span>
          </div>
        </Panel>
      ) : null}

      <div className="metrics-grid">
        <MetricCard label="当前对象" value={selectedScene?.objectCount.toLocaleString() ?? 0} meta="Blender 场景对象" />
        <MetricCard label="道路宽度" value={`${selectedScene?.roadWidth ?? 0}m`} meta="Geometry Nodes 参数" />
        <MetricCard label="树木密度" value={`${selectedScene?.treeDensity ?? 0}%`} meta="模板联动" tone="good" />
        <MetricCard label="待处理任务" value={sceneTasks.filter((task) => task.status === 'queued').length} meta="插件队列" tone="warn" />
        <MetricCard label="可用资产" value={assets.filter((asset) => asset.status === 'available').length} meta="2D / 3D 资源" />
      </div>

      <div className="two-column">
        <Panel>
          <SectionHeader title="模板编号联动" description="输入模板编号后批量配置树木、道路纹理与路边座椅类型。" />
          <div className="form-grid">
            <Field label="模板">
              <select
                value={templateId}
                onChange={(event) => {
                  setTemplateId(event.target.value);
                  setTemplateNumber(templateNumberMap[event.target.value] ?? '0');
                }}
              >
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="模板编号">
              <input value={templateNumber} onChange={(event) => setTemplateNumber(event.target.value)} />
            </Field>
          </div>
          {selectedTemplate ? (
            <div className="template-hints">
              <div>
                <strong>{selectedTemplate.style}</strong>
                <span>{selectedTemplate.rulesVersion}</span>
              </div>
              <span>{selectedTemplate.recommendedRoad} / {selectedTemplate.recommendedTree} / {selectedTemplate.recommendedSeat}</span>
            </div>
          ) : null}
          <Button onClick={() => void handleTemplateApply()} isLoading={busyKey === 'template'} disabled={!selectedSceneId}>
            <SlidersHorizontal size={16} />
            应用模板联动
          </Button>
        </Panel>

        <Panel>
          <SectionHeader title="道路纹理贴图" description="通过插件函数更换城市场景中的道路材质。" />
          <Field label="纹理">
            <select value={roadTexture} onChange={(event) => setRoadTexture(event.target.value)}>
              {roadTextureOptions.map((texture) => (
                <option key={texture.id} value={texture.id}>
                  {texture.label}
                </option>
              ))}
            </select>
          </Field>
          <div className="asset-status-list">
            {roadTextureOptions.map((texture) => (
              <div key={texture.id}>
                <span>{texture.note}</span>
                <StatusBadge status={texture.id === roadTexture ? 'active' : 'ready'} />
              </div>
            ))}
          </div>
          <Button
            onClick={() =>
              void handleDispatchFunction('apply_road_texture', '更换道路纹理贴图', { texture_id: roadTexture }, 'texture')
            }
            isLoading={busyKey === 'texture'}
            disabled={!selectedSceneId}
          >
            <Brush size={16} />
            下发纹理更换
          </Button>
        </Panel>
      </div>

      <div className="two-column">
        <Panel>
          <SectionHeader title="3D 资产实例化" description="放置新增资产，支持数量和间距参数控制。" />
          <div className="form-grid">
            <Field label="资产">
              <select
                value={assetId}
                onChange={(event) => {
                  const next = furnitureAssets.find((asset) => asset.id === event.target.value);
                  setAssetId(event.target.value);
                  setAssetCount(next?.count ?? assetCount);
                  setAssetSpacing(next?.spacing ?? assetSpacing);
                }}
              >
                {furnitureAssets.map((asset) => (
                  <option key={asset.id} value={asset.id}>
                    {asset.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="数量">
              <input type="number" min={1} max={60} value={assetCount} onChange={(event) => setAssetCount(Number(event.target.value))} />
            </Field>
            <Field label="间距">
              <input type="number" min={2} max={40} value={assetSpacing} onChange={(event) => setAssetSpacing(Number(event.target.value))} />
            </Field>
          </div>
          <Button
            onClick={() =>
              void handleDispatchFunction(
                'place_furniture',
                '放置 3D 资产实例',
                { asset_id: assetId, min_count: assetCount, max_count: assetCount, spacing: assetSpacing, clear_previous: false },
                'asset',
              )
            }
            isLoading={busyKey === 'asset'}
            disabled={!selectedSceneId}
          >
            <PackagePlus size={16} />
            实例化资产
          </Button>
        </Panel>

        <Panel>
          <SectionHeader title="道路布局输入" description="支持手动坐标点集与手绘草图两种方式。" />
          <Field label="坐标点集">
            <textarea rows={4} value={pointsText} onChange={(event) => setPointsText(event.target.value)} />
          </Field>
          <Button
            onClick={() =>
              void handleDispatchFunction('apply_layout', '按坐标点集生成路网', { points: pointsText, source: 'manual' }, 'layout')
            }
            isLoading={busyKey === 'layout'}
            disabled={!selectedSceneId}
          >
            <Map size={16} />
            连线生成路网
          </Button>
          <div className="sketch-dropzone">
            <SquarePen size={26} />
            <strong>手绘草图上传</strong>
            <input type="file" accept="image/*" onChange={handleSketchFileChange} />
            <span>{sketchName} / 前端通过多模态接口提交草图，由后端识别点线拓扑。</span>
          </div>
          <Button onClick={() => void handleSketchSubmit()} isLoading={busyKey === 'sketch'} disabled={!selectedSceneId || !sketchBase64}>
            <FileImage size={16} />
            提交手绘草图
          </Button>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="插件任务回执" />
        {sceneTasks.length ? (
          <div className="table-list">
            {sceneTasks.map((task) => (
              <div key={task.id} className="table-row task-row">
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.functionName}</span>
                </div>
                <StatusBadge status={task.status} />
                <small>{task.progress}%</small>
                <span>{task.traceId}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="暂无插件任务" description="模板、道路纹理贴图、3D 资产实例化和布局操作会在这里留下记录。" />
        )}
      </Panel>
    </div>
  );
}
