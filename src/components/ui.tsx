import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Clock3, Loader2, XCircle } from 'lucide-react';
import type { AuditSeverity, HealthStatus, ProjectStatus, SceneStatus, SimulationStatus, TaskStatus } from '../types/domain';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className = '',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'icon';
  isLoading?: boolean;
}) {
  return (
    <button className={`button button-${variant} button-${size} ${className}`} disabled={props.disabled || isLoading} {...props}>
      {isLoading ? <Loader2 className="spin" size={16} /> : null}
      {children}
    </button>
  );
}

export function IconButton({
  label,
  children,
  variant = 'ghost',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  children: ReactNode;
}) {
  return (
    <button className={`icon-button button-${variant}`} title={label} aria-label={label} {...props}>
      {children}
    </button>
  );
}

export function Panel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

export function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="section-header">
      <div>
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="empty-state">
      <Clock3 size={24} />
      <strong>{title}</strong>
      <span>{description}</span>
      {action}
    </div>
  );
}

export function InlineError({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  return (
    <div className="inline-error" role="alert">
      <AlertTriangle size={18} />
      <span>{message}</span>
      {onDismiss ? (
        <button onClick={onDismiss} aria-label="关闭错误提示">
          关闭
        </button>
      ) : null}
    </div>
  );
}

export function LoadingBlock({ label = '正在加载数据' }: { label?: string }) {
  return (
    <div className="loading-block">
      <Loader2 className="spin" size={20} />
      <span>{label}</span>
    </div>
  );
}

export function StatusBadge({
  status,
}: {
  status: TaskStatus | SimulationStatus | ProjectStatus | SceneStatus | AuditSeverity | HealthStatus | string;
}) {
  const labelMap: Record<string, string> = {
    queued: '排队',
    validating: '校验中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    rollback: '回滚',
    archived: '归档',
    active: '活跃',
    draft: '草稿',
    review: '评审',
    ready: '就绪',
    editing: '编辑中',
    rendering: '渲染中',
    idle: '空闲',
    paused: '暂停',
    completed: '完成',
    info: '信息',
    warning: '告警',
    critical: '高危',
    healthy: '健康',
    degraded: '降级',
    offline: '离线',
    denied: '拒绝',
    pending: '等待',
  };
  const icon =
    status === 'success' || status === 'completed' || status === 'healthy' ? (
      <CheckCircle2 size={14} />
    ) : status === 'failed' || status === 'critical' || status === 'offline' ? (
      <XCircle size={14} />
    ) : (
      <Clock3 size={14} />
    );
  return (
    <span className={`status-badge status-${status}`}>
      {icon}
      {labelMap[String(status)] ?? String(status)}
    </span>
  );
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="progress" aria-label={`进度 ${value}%`}>
      <span style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export function MetricCard({
  label,
  value,
  meta,
  tone = 'default',
}: {
  label: string;
  value: string | number;
  meta?: string;
  tone?: 'default' | 'good' | 'warn' | 'bad';
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {meta ? <small>{meta}</small> : null}
    </div>
  );
}
