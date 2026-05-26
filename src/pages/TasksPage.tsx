import { FormEvent, useMemo, useState } from 'react';
import { GitBranch, Play, RefreshCw, ShieldAlert, Workflow } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, Field, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';

export function TasksPage() {
  const { hasPermission } = useSession();
  const {
    selectedProjectId,
    selectedSceneId,
    functions,
    tasks,
    dispatchTask,
    retryTask,
  } = useWorkspace();
  const [functionName, setFunctionName] = useState(functions[0]?.name ?? 'replace_asset_batch');
  const [title, setTitle] = useState('手动下发插件任务');
  const [priority, setPriority] = useState(3);
  const [params, setParams] = useState('{"scope":"current_scene","dry_run":false}');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const functionItem = functions.find((item) => item.name === functionName);
  const taskStats = useMemo(
    () => ({
      running: tasks.filter((task) => task.status === 'running').length,
      queued: tasks.filter((task) => task.status === 'queued').length,
      failed: tasks.filter((task) => task.status === 'failed').length,
      success: tasks.filter((task) => task.status === 'success').length,
    }),
    [tasks],
  );

  const handleDispatch = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !selectedSceneId) return;
    setIsSubmitting(true);
    setLocalError(null);
    try {
      const parsedParams = JSON.parse(params) as Record<string, unknown>;
      await dispatchTask({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        functionName,
        title,
        priority,
        params: parsedParams,
        dependsOn: [],
      });
    } catch (caught) {
      setLocalError(caught instanceof Error ? caught.message : '任务下发失败。');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-stack">
      <SectionHeader title="任务编排与插件调度" description="白名单函数、DAG 依赖、Blender 插件任务下发与回执状态机。" />

      <div className="metrics-grid">
        <MetricInline label="排队" value={taskStats.queued} />
        <MetricInline label="运行" value={taskStats.running} />
        <MetricInline label="成功" value={taskStats.success} />
        <MetricInline label="失败" value={taskStats.failed} />
      </div>

      <div className="two-column uneven">
        <Panel>
          <SectionHeader title="函数注册表" />
          <div className="function-list">
            {functions.map((item) => (
              <button key={item.name} className={`function-item ${item.name === functionName ? 'active' : ''}`} type="button" onClick={() => setFunctionName(item.name)}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.name}</span>
                </div>
                <StatusBadge status={item.enabled ? 'healthy' : 'offline'} />
                <small>
                  {item.risk} / {item.averageMs}ms
                </small>
              </button>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="任务下发" action={functionItem ? <StatusBadge status={functionItem.risk === 'high' ? 'critical' : 'info'} /> : null} />
          <form className="dispatch-form" onSubmit={(event) => void handleDispatch(event)}>
            {localError ? <div className="form-error">{localError}</div> : null}
            <Field label="任务标题">
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </Field>
            <div className="form-grid">
              <Field label="函数">
                <select value={functionName} onChange={(event) => setFunctionName(event.target.value)}>
                  {functions.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="优先级">
                <input type="number" min={1} max={5} value={priority} onChange={(event) => setPriority(Number(event.target.value))} />
              </Field>
            </div>
            <Field label="参数 JSON">
              <textarea rows={8} value={params} onChange={(event) => setParams(event.target.value)} spellCheck={false} />
            </Field>
            <div className="function-schema">
              <ShieldAlert size={16} />
              <span>{functionItem?.schemaSummary}</span>
            </div>
            <Button type="submit" isLoading={isSubmitting} disabled={!hasPermission('task:dispatch')}>
              <Play size={16} />
              生成任务
            </Button>
          </form>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="DAG 调度视图" />
        <div className="dag-view">
          <DagNode title="参数校验" status="success" />
          <DagEdge />
          <DagNode title="函数白名单" status="success" />
          <DagEdge />
          <DagNode title="队列调度" status={taskStats.queued > 0 ? 'queued' : 'success'} />
          <DagEdge />
          <DagNode title="Blender 执行" status={taskStats.running > 0 ? 'running' : 'queued'} />
          <DagEdge />
          <DagNode title="回执归档" status={taskStats.failed > 0 ? 'failed' : 'success'} />
        </div>
      </Panel>

      <Panel>
        <SectionHeader title="任务状态机" />
        {tasks.length ? (
          <div className="task-table">
            {tasks.map((task) => (
              <div key={task.id} className="task-card-row">
                <div>
                  <strong>{task.title}</strong>
                  <span>
                    {task.functionName} / {task.traceId}
                  </span>
                </div>
                <StatusBadge status={task.status} />
                <div className="progress-cell">
                  <ProgressBar value={task.progress} />
                  <small>{task.progress}%</small>
                </div>
                <div className="task-log">
                  {task.logs.slice(-2).map((log) => (
                    <span key={log}>{log}</span>
                  ))}
                </div>
                <Button variant="secondary" size="sm" disabled={!task.retryable} onClick={() => void retryTask(task.id)}>
                  <RefreshCw size={14} />
                  重试
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="暂无任务" description="函数计划和手动调度会进入任务状态机。" />
        )}
      </Panel>
    </div>
  );
}

function MetricInline({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric metric-default">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>任务</small>
    </div>
  );
}

function DagNode({ title, status }: { title: string; status: string }) {
  return (
    <div className={`dag-node dag-${status}`}>
      <Workflow size={18} />
      <strong>{title}</strong>
      <StatusBadge status={status} />
    </div>
  );
}

function DagEdge() {
  return (
    <div className="dag-edge">
      <GitBranch size={18} />
    </div>
  );
}
