import { FormEvent, useMemo, useState } from 'react';
import { BrainCircuit, Check, FileImage, MessageSquareText, Play, Send, SquarePen } from 'lucide-react';
import { useWorkspace } from '../context/WorkspaceContext';
import type { Modality } from '../types/domain';
import { Button, EmptyState, Field, Panel, ProgressBar, SectionHeader, StatusBadge } from '../components/ui';

const modalityOptions: Array<{ value: Modality; label: string; icon: React.ElementType }> = [
  { value: 'text', label: '文本', icon: MessageSquareText },
  { value: 'sketch', label: '草图', icon: SquarePen },
  { value: 'screenshot', label: '截图', icon: FileImage },
];

const promptPresets = [
  '把主路两侧树木密度调高，并让天气转为傍晚小雨。',
  '根据草图重建滨水步道点线拓扑，保留消防通道净宽。',
  '对当前场景启动车辆与人群综合仿真，规则版本使用 traffic-r3.2。',
];

export function MultimodalPage() {
  const {
    selectedProjectId,
    selectedSceneId,
    commands,
    tasks,
    submitCommand,
    dispatchPlan,
  } = useWorkspace();
  const [text, setText] = useState(promptPresets[0]);
  const [modalities, setModalities] = useState<Modality[]>(['text']);
  const [attachments, setAttachments] = useState('sketch-river-road.png');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDispatching, setIsDispatching] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const activeCommand = commands[0];
  const commandTasks = useMemo(
    () => tasks.filter((task) => activeCommand?.plan.some((node) => node.funcName === task.functionName)).slice(0, 6),
    [activeCommand, tasks],
  );

  const toggleModality = (value: Modality) => {
    setModalities((current) => {
      if (current.includes(value)) {
        const next = current.filter((item) => item !== value);
        return next.length ? next : ['text'];
      }
      return [...current, value];
    });
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedProjectId || !selectedSceneId) return;
    setIsSubmitting(true);
    setLocalError(null);
    try {
      await submitCommand({
        projectId: selectedProjectId,
        sceneId: selectedSceneId,
        text,
        modalities,
        attachmentNames: attachments
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      });
    } catch (caught) {
      setLocalError(caught instanceof Error ? caught.message : '多模态解析失败。');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDispatchPlan = async (commandId: string) => {
    setIsDispatching(commandId);
    setLocalError(null);
    try {
      await dispatchPlan(commandId);
    } catch (caught) {
      setLocalError(caught instanceof Error ? caught.message : '函数计划下发失败。');
    } finally {
      setIsDispatching(null);
    }
  };

  return (
    <div className="page-stack">
      <SectionHeader title="多模态智能交互" description="文本、草图、截图输入会先解析为意图与槽位，再生成可审计函数 DAG。" />

      <div className="multimodal-grid">
        <Panel>
          <SectionHeader title="指令输入" />
          <form className="mmi-form" onSubmit={(event) => void handleSubmit(event)}>
            {localError ? <div className="form-error">{localError}</div> : null}
            <div className="preset-list">
              {promptPresets.map((preset) => (
                <button key={preset} type="button" onClick={() => setText(preset)}>
                  {preset}
                </button>
              ))}
            </div>
            <Field label="多模态通道">
              <div className="segmented">
                {modalityOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <button key={option.value} className={modalities.includes(option.value) ? 'active' : ''} type="button" onClick={() => toggleModality(option.value)}>
                      <Icon size={16} />
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </Field>
            <Field label="自然语言指令">
              <textarea rows={7} value={text} onChange={(event) => setText(event.target.value)} />
            </Field>
            <Field label="附件引用">
              <input value={attachments} onChange={(event) => setAttachments(event.target.value)} />
            </Field>
            <Button type="submit" isLoading={isSubmitting}>
              <Send size={16} />
              解析指令
            </Button>
          </form>
        </Panel>

        <Panel>
          <SectionHeader title="意图与槽位" />
          {activeCommand ? (
            <div className="intent-panel">
              <div className="confidence-ring" style={{ '--confidence': `${Math.round(activeCommand.confidence * 100)}%` } as React.CSSProperties}>
                <strong>{Math.round(activeCommand.confidence * 100)}%</strong>
                <span>置信度</span>
              </div>
              <div className="intent-details">
                <StatusBadge status={activeCommand.needsClarification ? 'warning' : 'healthy'} />
                <h3>{activeCommand.intentTag}</h3>
                <p>{activeCommand.explanation}</p>
              </div>
              <div className="slot-grid">
                {Object.entries(activeCommand.slots).map(([key, value]) => (
                  <div key={key}>
                    <span>{key}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState title="等待指令" description="提交文本、草图或截图后会生成结构化意图。" />
          )}
        </Panel>
      </div>

      <Panel>
        <SectionHeader
          title="函数 DAG 计划"
          action={
            activeCommand ? (
              <Button
                size="sm"
                onClick={() => void handleDispatchPlan(activeCommand.id)}
                isLoading={isDispatching === activeCommand.id}
                disabled={activeCommand.needsClarification}
              >
                <Play size={14} />
                自动下发
              </Button>
            ) : null
          }
        />
        {activeCommand ? (
          <div className="plan-board">
            {activeCommand.plan.map((node, index) => (
              <div key={node.id} className="plan-node">
                <div className="plan-index">{index + 1}</div>
                <div>
                  <strong>{node.title}</strong>
                  <span>{node.funcName}</span>
                </div>
                <StatusBadge status={node.status} />
                <code>{JSON.stringify(node.params)}</code>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="暂无计划" description="系统会把输入转成白名单函数调用序列。" />
        )}
      </Panel>

      <div className="two-column">
        <Panel>
          <SectionHeader title="编排链路" />
          <div className="pipeline">
            {['多模态编码', '意图分类', '槽位填充', '函数检索', 'DAG 编排', '参数校验', '任务下发'].map((item, index) => (
              <div key={item} className="pipeline-step">
                <span>{index + 1}</span>
                <strong>{item}</strong>
                <Check size={16} />
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="关联任务" />
          {commandTasks.length ? (
            <div className="table-list">
              {commandTasks.map((task) => (
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
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="尚未下发" description="批准函数计划后会生成任务队列记录。" />
          )}
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="历史指令" />
        <div className="command-history">
          {commands.map((command) => (
            <div key={command.id} className="command-item">
              <BrainCircuit size={18} />
              <div>
                <strong>{command.rawInput}</strong>
                <span>
                  {command.intentTag} / {command.modality.join('+')}
                </span>
              </div>
              <StatusBadge status={command.needsClarification ? 'warning' : 'success'} />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
