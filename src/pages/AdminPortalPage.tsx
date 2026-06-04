import { useMemo, useState } from 'react';
import { ClipboardCheck, Lock, PlugZap, Search, ShieldCheck, ToggleLeft, ToggleRight, Trash2, UserMinus } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, MetricCard, Panel, SectionHeader, StatusBadge } from '../components/ui';
import { roleLabels, type RoleCode } from '../types/domain';

const managedUsers: Array<{ id: string; name: string; role: RoleCode; email: string; state: 'active' | 'review' | 'archived' }> = [
  { id: 'usr-modeler', name: '林知远', role: 'modeler', email: 'modeler@nku.city', state: 'active' },
  { id: 'usr-analyst', name: '沈迭青', role: 'analyst', email: 'analyst@nku.city', state: 'review' },
  { id: 'usr-admin', name: '陈明策', role: 'admin', email: 'admin@nku.city', state: 'active' },
];

export function AdminPortalPage() {
  const { hasPermission } = useSession();
  const {
    functions,
    settings,
    auditLogs,
    versions,
    health,
    updateSetting,
    togglePluginFunction,
  } = useWorkspace();
  const [query, setQuery] = useState('');
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [reviewedPlugins, setReviewedPlugins] = useState<Record<string, boolean>>({});
  const [deletedUsers, setDeletedUsers] = useState<Record<string, boolean>>({});

  const filteredLogs = useMemo(
    () => auditLogs.filter((log) => `${log.actor} ${log.eventType} ${log.target}`.toLowerCase().includes(query.toLowerCase())).slice(0, 8),
    [auditLogs, query],
  );
  const riskyFunctions = functions.filter((func) => func.risk !== 'low');

  const runAction = async (key: string, action: () => Promise<unknown> | void) => {
    setBusyKey(key);
    try {
      await action();
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className="page-stack role-portal">
      <section className="role-hero admin-hero">
        <div>
          <span className="eyebrow">/admin</span>
          <h1>系统管理员门户</h1>
          <p>管理用户、审核插件、维护白名单与审计证据链。</p>
        </div>
        <div className="admin-lockup">
          <ShieldCheck size={34} />
          <span>RBAC 路由守卫已启用</span>
        </div>
      </section>

      <div className="metrics-grid">
        <MetricCard label="插件函数" value={functions.length} meta="白名单" />
        <MetricCard label="高风险函数" value={riskyFunctions.length} meta="需审核" tone="warn" />
        <MetricCard label="审计日志" value={auditLogs.length} meta="追加式记录" />
        <MetricCard label="版本快照" value={versions.length} meta="可回滚" />
        <MetricCard label="健康服务" value={health.filter((item) => item.status === 'healthy').length} meta="在线节点" tone="good" />
      </div>

      <div className="two-column">
        <Panel>
          <SectionHeader title="用户与角色" description="管理员专属操作：删除用户、冻结账号和检查角色权限。" />
          <div className="user-admin-list">
            {managedUsers.map((user) => (
              <div key={user.id} className={`user-admin-row ${deletedUsers[user.id] ? 'archived' : ''}`}>
                <div>
                  <strong>{user.name}</strong>
                  <span>{user.email} / {roleLabels[user.role]}</span>
                </div>
                <StatusBadge status={deletedUsers[user.id] ? 'archived' : user.state} />
                <Button
                  size="sm"
                  variant="danger"
                  disabled={!hasPermission('settings:write') || user.role === 'admin' || deletedUsers[user.id]}
                  onClick={() =>
                    void runAction(user.id, () => {
                      setDeletedUsers((current) => ({ ...current, [user.id]: true }));
                    })
                  }
                  isLoading={busyKey === user.id}
                >
                  <UserMinus size={14} />
                  删除用户
                </Button>
              </div>
            ))}
          </div>
        </Panel>

        <Panel>
          <SectionHeader title="运行参数" description="只允许管理员修改 RBAC、LLM、插件、仿真和审计策略。" />
          <div className="settings-list">
            {settings.slice(0, 4).map((setting) => (
              <div key={setting.id} className="compact-setting-row">
                <div>
                  <strong>{setting.title}</strong>
                  <span>{setting.description}</span>
                </div>
                {typeof setting.value === 'boolean' ? (
                  <Button
                    size="sm"
                    variant={setting.value ? 'secondary' : 'primary'}
                    disabled={setting.locked}
                    onClick={() => void runAction(setting.id, async () => updateSetting(setting.id, !setting.value))}
                    isLoading={busyKey === setting.id}
                  >
                    {setting.value ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                    {setting.value ? '开启' : '关闭'}
                  </Button>
                ) : (
                  <StatusBadge status={setting.locked ? 'offline' : 'healthy'} />
                )}
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel>
        <SectionHeader title="审核插件" description="管理员审核插件函数后，才能启用或停用白名单中的高风险能力。" />
        <div className="plugin-grid">
          {functions.map((func) => (
            <div key={func.name} className="plugin-card">
              <div className="plugin-card-head">
                <PlugZap size={18} />
                <div>
                  <strong>{func.title}</strong>
                  <span>{func.name}</span>
                </div>
                <StatusBadge status={reviewedPlugins[func.name] ? 'success' : func.risk === 'high' ? 'warning' : 'info'} />
              </div>
              <p>{func.description}</p>
              <div className="plugin-meta">
                <StatusBadge status={func.risk === 'high' ? 'critical' : func.risk === 'medium' ? 'warning' : 'info'} />
                <span>{func.schemaSummary}</span>
                <span>{func.averageMs}ms</span>
              </div>
              <div className="row-actions">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    void runAction(`review-${func.name}`, () => {
                      setReviewedPlugins((current) => ({ ...current, [func.name]: true }));
                    })
                  }
                  isLoading={busyKey === `review-${func.name}`}
                >
                  <ClipboardCheck size={14} />
                  审核插件
                </Button>
                <Button
                  size="sm"
                  variant={func.enabled ? 'danger' : 'primary'}
                  disabled={!hasPermission('settings:write')}
                  onClick={() => void runAction(`toggle-${func.name}`, async () => togglePluginFunction(func.name, !func.enabled))}
                  isLoading={busyKey === `toggle-${func.name}`}
                >
                  {func.enabled ? <Lock size={14} /> : <ShieldCheck size={14} />}
                  {func.enabled ? '停用' : '启用'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel>
        <SectionHeader
          title="审计检索"
          action={
            <div className="search-box">
              <Search size={16} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索人员、事件或目标" />
            </div>
          }
        />
        {filteredLogs.length ? (
          <div className="audit-table">
            {filteredLogs.map((log) => (
              <div key={log.id} className="audit-row">
                <div>
                  <strong>{log.eventType}</strong>
                  <span>{log.traceId}</span>
                </div>
                <span>{log.actor}</span>
                <StatusBadge status={log.severity} />
                <StatusBadge status={log.result} />
                <code>{log.evidenceHash}</code>
                <Button size="sm" variant="secondary">
                  <Trash2 size={14} />
                  归档
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="无审计结果" description="调整搜索关键词后重试。" />
        )}
      </Panel>
    </div>
  );
}
