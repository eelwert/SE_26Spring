import { FormEvent, useMemo, useState } from 'react';
import { BrainCircuit, CloudRain, Mountain, Play, Route, Send, ShipWheel, TrafficCone } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, Field, MetricCard, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';
import type { SimulationJob } from '../types/domain';

const naturalPrompts = [
  '将天色变暗，切换为雨天模式，并生成湖泊与河流。',
  '启动交通灯控制下的车辆和行人仿真，规则版本 traffic-r3.2。',
  '生成一个山丘地形，高度200米，再添加湖中动态船只。',
];

export function AnalystPortalPage() {
  const {
    selectedProjectId,
    selectedSceneId,
    selectedScene,
    commands,
    simulations,
    tasks,
    submitCommand,
    dispatchPlan,
    startSimulation,
  } = useWorkspace();
  const [text, setText] = useState(naturalPrompts[0]);
  const [simType, setSimType] = useState<SimulationJob['type']>('combined');
  const [rulesVersion, setRulesVersion] = useState('traffic-r3.2');
  const [terrainHeight, setTerrainHeight] = useState(200);
  const [lakeSize, setLakeSize] = useState(120);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const activeCommand = commands[0];
  const activeSimulation = simulations[0];
  const relatedTasks = useMemo(
    () => tasks.filter((task) => !selectedSceneId || task.sceneId === selectedSceneId).slice(0, 4),
    [selectedSceneId, tasks],
  );

  const runAction = async (key: string, action: () => Promise<unknown>) => {
    setBusyKey(key);
    try {
      await action();
    } finally {
      setBusyKey(null);
    }
  };

  const handleCommand = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !selectedSceneId) return;
    await runAction('command', async () => {
      await submitCommand({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        text,
        modalities: ['text'],
        attachmentNames: [],
      });
    });
  };

  const handleDispatch = async () => {
    if (!activeCommand) return;
    await runAction('dispatch', async () => dispatchPlan(activeCommand.id));
  };

  const handleSimulation = async () => {
    if (!selectedProjectId || !selectedSceneId) return;
    await runAction('simulation', async () =>
      startSimulation({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        type: simType,
        rulesVersion,
        seed: 20260604,
        durationMinutes: 60,
      }),
    );
  };

  const handleLandscape = async () => {
    if (!selectedProjectId || !selectedSceneId) return;
    await runAction('landscape', async () => {
      await submitCommand({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        text: `生成自然景观：山丘高度${terrainHeight}米，湖泊尺寸${lakeSize}米，河流与船只路径同时生成。`,
        modalities: ['text'],
        attachmentNames: [],
      });
    });
  };

  return (
    <div className="page-stack role-portal">
      <section className="role-hero analyst-hero">
        <div>
          <span className="eyebrow">/analyst</span>
          <h1>行业分析师门户</h1>
          <p>{selectedScene ? `${selectedScene.name} 的多模态方案推演、交通仿真和自然景观分析。` : '等待选择分析场景。'}</p>
        </div>
        <div className="hero-mini-map">
          <span className="traffic-light red" />
          <span className="traffic-light green" />
          <span className="traffic-road road-main" />
          <span className="traffic-road road-cross" />
        </div>
      </section>

      <div className="metrics-grid">
        <MetricCard label="历史指令" value={commands.length} meta="自然语言解析" />
        <MetricCard label="仿真批次" value={simulations.length} meta="车辆 / 人群" />
        <MetricCard label="关联任务" value={relatedTasks.length} meta="函数计划" />
        <MetricCard label="当前置信度" value={activeCommand ? `${Math.round(activeCommand.confidence * 100)}%` : '-'} meta="结构化 JSON" tone="good" />
        <MetricCard label="交通灯" value="启用" meta="红灯停步 / 路口停车" tone="warn" />
      </div>

      <div className="two-column uneven">
        <Panel>
          <SectionHeader title="自然语言指令" description="调用大模型 API，将文本解析为函数计划并驱动场景参数变更。" />
          <form className="mmi-form" onSubmit={(event) => void handleCommand(event)}>
            <div className="preset-list">
              {naturalPrompts.map((prompt) => (
                <button key={prompt} type="button" onClick={() => setText(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
            <Field label="指令">
              <textarea rows={6} value={text} onChange={(event) => setText(event.target.value)} />
            </Field>
            <Button type="submit" isLoading={busyKey === 'command'} disabled={!selectedSceneId}>
              <Send size={16} />
              解析指令
            </Button>
          </form>
        </Panel>

        <Panel>
          <SectionHeader
            title="结构化 JSON"
            action={
              activeCommand ? (
                <Button size="sm" onClick={() => void handleDispatch()} isLoading={busyKey === 'dispatch'} disabled={activeCommand.needsClarification}>
                  <Play size={14} />
                  下发计划
                </Button>
              ) : null
            }
          />
          {activeCommand ? (
            <div className="json-preview">
              <pre>{JSON.stringify({ intentTag: activeCommand.intentTag, slots: activeCommand.slots, plan: activeCommand.plan }, null, 2)}</pre>
            </div>
          ) : (
            <EmptyState title="暂无 JSON" description="提交自然语言指令后会生成结构化 JSON。" />
          )}
        </Panel>
      </div>

      <div className="two-column">
        <Panel>
          <SectionHeader title="交通灯仿真" description="车辆沿道路曲线行驶，行人沿人行道移动，红灯停步并在路口停车。" />
          <div className="form-grid">
            <Field label="仿真类型">
              <select value={simType} onChange={(event) => setSimType(event.target.value as SimulationJob['type'])}>
                <option value="combined">车辆 + 人群</option>
                <option value="traffic">车辆</option>
                <option value="crowd">人群</option>
              </select>
            </Field>
            <Field label="规则版本">
              <input value={rulesVersion} onChange={(event) => setRulesVersion(event.target.value)} />
            </Field>
          </div>
          <Button onClick={() => void handleSimulation()} isLoading={busyKey === 'simulation'} disabled={!selectedSceneId}>
            <TrafficCone size={16} />
            启动交通灯仿真
          </Button>
          <div className="traffic-board">
            <span className="traffic-road road-main" />
            <span className="traffic-road road-cross" />
            <span className="vehicle-dot car-a" />
            <span className="vehicle-dot car-b" />
            <span className="person-dot walker-a" />
            <span className="person-dot walker-b" />
            <span className="traffic-light red" />
            <span className="traffic-light green" />
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="自然景观" description="生成山丘地形、湖泊水面、河流与动态船只路径。" />
          <div className="form-grid">
            <Field label="山丘高度">
              <input type="number" min={20} max={400} value={terrainHeight} onChange={(event) => setTerrainHeight(Number(event.target.value))} />
            </Field>
            <Field label="湖泊尺寸">
              <input type="number" min={20} max={260} value={lakeSize} onChange={(event) => setLakeSize(Number(event.target.value))} />
            </Field>
          </div>
          <div className="landscape-options">
            <span><Mountain size={16} /> 山丘地形</span>
            <span><CloudRain size={16} /> 湖泊波纹</span>
            <span><Route size={16} /> 河流路径</span>
            <span><ShipWheel size={16} /> 动态船只</span>
          </div>
          <Button onClick={() => void handleLandscape()} isLoading={busyKey === 'landscape'} disabled={!selectedSceneId}>
            <BrainCircuit size={16} />
            生成自然景观计划
          </Button>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="仿真与任务状态" />
        {activeSimulation ? (
          <div className="table-list">
            <div className="table-row task-row">
              <div>
                <strong>{activeSimulation.id}</strong>
                <span>{activeSimulation.rulesVersion}</span>
              </div>
              <StatusBadge status={activeSimulation.status} />
              <ProgressBar value={activeSimulation.progress} />
              <span>{activeSimulation.durationMinutes} min</span>
            </div>
            {relatedTasks.map((task) => (
              <div key={task.id} className="table-row task-row">
                <div>
                  <strong>{task.title}</strong>
                  <span>{task.functionName}</span>
                </div>
                <StatusBadge status={task.status} />
                <ProgressBar value={task.progress} />
                <span>{task.createdBy}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="暂无仿真" description="启动交通灯仿真或下发函数计划后会显示状态。" />
        )}
      </Panel>
    </div>
  );
}
