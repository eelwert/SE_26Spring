import { FormEvent, useMemo, useState } from 'react';
import { Download, Pause, Play, RotateCcw, TimerReset } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import type { SimulationJob } from '../types/domain';
import { Button, EmptyState, Field, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';

export function SimulationPage() {
  const {
    selectedProjectId,
    selectedSceneId,
    simulations,
    startSimulation,
    updateSimulationStatus,
  } = useWorkspace();
  const [type, setType] = useState<SimulationJob['type']>('combined');
  const [rulesVersion, setRulesVersion] = useState('traffic-r3.2 / crowd-r2.8');
  const [seed, setSeed] = useState(20260506);
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeSimulation = simulations[0];
  const allMetrics = useMemo(() => simulations.flatMap((simulation) => simulation.metrics), [simulations]);

  const handleStart = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !selectedSceneId) return;
    setIsSubmitting(true);
    try {
      await startSimulation({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        type,
        rulesVersion,
        seed,
        durationMinutes,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-stack">
      <SectionHeader title="仿真分析" description="车辆、人群、综合仿真任务，支持可复现随机种子、轨迹回放与指标分析。" />

      <div className="simulation-layout">
        <Panel>
          <SectionHeader title="启动仿真" />
          <form className="compact-form" onSubmit={(event) => void handleStart(event)}>
            <Field label="仿真类型">
              <select value={type} onChange={(event) => setType(event.target.value as SimulationJob['type'])}>
                <option value="combined">车辆 + 人群</option>
                <option value="traffic">车辆</option>
                <option value="crowd">人群</option>
              </select>
            </Field>
            <Field label="规则版本">
              <input value={rulesVersion} onChange={(event) => setRulesVersion(event.target.value)} />
            </Field>
            <Field label="随机种子">
              <input type="number" value={seed} onChange={(event) => setSeed(Number(event.target.value))} />
            </Field>
            <Field label="时长（分钟）">
              <input type="number" min={5} max={240} value={durationMinutes} onChange={(event) => setDurationMinutes(Number(event.target.value))} />
            </Field>
            <Button type="submit" isLoading={isSubmitting}>
              <Play size={16} />
              启动仿真
            </Button>
          </form>
        </Panel>

        <Panel className="wide-panel">
          <SectionHeader title="结果回放" />
          {activeSimulation ? (
            <div className="playback-panel">
              <div className="simulation-canvas">
                {Array.from({ length: 18 }, (_, index) => (
                  <span key={`road-${index}`} className={`sim-road sr-${index % 6}`} />
                ))}
                {Array.from({ length: 24 }, (_, index) => (
                  <span key={`vehicle-${index}`} className={`vehicle v-${index % 8}`} />
                ))}
                {Array.from({ length: 18 }, (_, index) => (
                  <span key={`person-${index}`} className={`person p-${index % 6}`} />
                ))}
                <div className="heat h1" />
                <div className="heat h2" />
              </div>
              <div className="playback-controls">
                <StatusBadge status={activeSimulation.status} />
                <ProgressBar value={activeSimulation.progress} />
                <span>
                  {activeSimulation.playbackTime} / {activeSimulation.durationMinutes} min
                </span>
                <Button size="sm" variant="secondary" onClick={() => void updateSimulationStatus(activeSimulation.id, activeSimulation.status === 'paused' ? 'running' : 'paused')}>
                  {activeSimulation.status === 'paused' ? <Play size={14} /> : <Pause size={14} />}
                  {activeSimulation.status === 'paused' ? '继续' : '暂停'}
                </Button>
                <Button size="sm" variant="secondary" onClick={() => void updateSimulationStatus(activeSimulation.id, 'completed')}>
                  <TimerReset size={14} />
                  完成
                </Button>
              </div>
            </div>
          ) : (
            <EmptyState title="暂无仿真" description="启动仿真后会显示回放画布。" />
          )}
        </Panel>
      </div>

      <div className="two-column">
        <Panel>
          <SectionHeader title="指标面板" />
          {allMetrics.length ? (
            <div className="metric-list">
              {allMetrics.slice(0, 8).map((metric, index) => (
                <div key={`${metric.name}-${index}`} className={`analysis-metric metric-${metric.severity}`}>
                  <span>{metric.name}</span>
                  <strong>
                    {metric.value}
                    {metric.unit}
                  </strong>
                  <small>{metric.delta > 0 ? '+' : ''}{metric.delta}</small>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="无指标" description="完成仿真后生成拥堵、冲突与效率指标。" />
          )}
        </Panel>

        <Panel>
          <SectionHeader title="仿真批次" />
          <div className="simulation-list">
            {simulations.map((simulation) => (
              <div key={simulation.id} className="simulation-item">
                <div>
                  <strong>{simulation.id}</strong>
                  <span>
                    {simulation.type} / seed {simulation.seed}
                  </span>
                </div>
                <StatusBadge status={simulation.status} />
                <ProgressBar value={simulation.progress} />
                <div className="row-actions">
                  <Button size="sm" variant="secondary">
                    <Download size={14} />
                    导出
                  </Button>
                  <Button size="sm" variant="ghost">
                    <RotateCcw size={14} />
                    复跑
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
