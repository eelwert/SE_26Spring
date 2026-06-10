import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, KeyRound, Lock, PlugZap, Search, ShieldCheck, ToggleLeft, ToggleRight, UserMinus, UsersRound, XCircle } from 'lucide-react';
import { useSession } from '../context/SessionContext';
import { useWorkspace } from '../context/WorkspaceContext';
import { Button, EmptyState, MetricCard, Panel, SectionHeader, StatusBadge } from '../components/ui';
import { roleLabels, type PermissionCode, type RoleCode } from '../types/domain';

const permissionLabels: Record<PermissionCode, string> = {
  'dashboard:view': '工作台',
  'project:read': '读取项目',
  'project:write': '编辑项目',
  'asset:replace': '替换资产',
  'layout:edit': '编辑布局',
  'task:dispatch': '任务下发',
  'multimodal:execute': '智能交互',
  'simulation:run': '运行仿真',
  'audit:read': '查看审计',
  'version:rollback': '版本回滚',
  'settings:write': '系统管理',
};

const permissionOptions = Object.keys(permissionLabels) as PermissionCode[];
const roleOptions: RoleCode[] = ['modeler', 'analyst', 'admin'];

export function AdminPortalPage() {
  const { session, hasPermission } = useSession();
  const {
    functions,
    users,
    pluginReviews,
    settings,
    auditLogs,
    versions,
    health,
    updateSetting,
    togglePluginFunction,
    updateUserRole,
    updateUserPermissions,
    deleteUser,
    reviewPlugin,
  } = useWorkspace();
  const [query, setQuery] = useState('');
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [permissionDrafts, setPermissionDrafts] = useState<Record<string, PermissionCode[]>>({});

  const isAdmin = session?.user.role === 'admin' && hasPermission('settings:write');

  const filteredLogs = useMemo(
    () => auditLogs.filter((log) => `${log.actor} ${log.eventType} ${log.target}`.toLowerCase().includes(query.toLowerCase())).slice(0, 8),
    [auditLogs, query],
  );
  const riskyFunctions = functions.filter((func) => func.risk !== 'low');
  const pendingReviews = pluginReviews.filter((review) => review.status === 'pending');
  const adminCount = users.filter((user) => user.role === 'admin').length;

  useEffect(() => {
    setPermissionDrafts((current) => {
      const next: Record<string, PermissionCode[]> = {};
      users.forEach((user) => {
        next[user.id] = current[user.id] ?? user.permissions;
      });
      return next;
    });
  }, [users]);

  const runAction = async (key: string, action: () => Promise<unknown> | void) => {
    setBusyKey(key);
    try {
      await action();
    } finally {
      setBusyKey(null);
    }
  };

  const togglePermissionDraft = (userId: string, permission: PermissionCode) => {
    setPermissionDrafts((current) => {
      const permissions = current[userId] ?? [];
      const nextPermissions = permissions.includes(permission)
        ? permissions.filter((item) => item !== permission)
        : [...permissions, permission];
      return { ...current, [userId]: nextPermissions };
    });
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
        <MetricCard label="待审核插件" value={pendingReviews.length} meta="管理员处理" tone={pendingReviews.length ? 'warn' : 'good'} />
      </div>

      {isAdmin ? (
        <div className="two-column uneven admin-governance-grid">
          <Panel>
            <SectionHeader title="用户权限分配" description="为演示用户分配角色与前端可见能力。" />
            {users.length ? (
              <div className="user-admin-list">
                {users.map((user) => {
                  const draftPermissions = permissionDrafts[user.id] ?? user.permissions;
                  const isLastAdmin = user.role === 'admin' && adminCount <= 1;
                  return (
                    <div key={user.id} className="user-admin-row user-permission-row">
                      <div className="user-admin-main">
                        <UsersRound size={18} />
                        <div>
                          <strong>{user.name}</strong>
                          <span>{user.email} / {user.department}</span>
                        </div>
                      </div>
                      <div className="user-role-controls">
                        <label>
                          <span>角色</span>
                          <select
                            value={user.role}
                            onChange={(event) =>
                              void runAction(`role-${user.id}`, async () =>
                                updateUserRole(user.id, { role: event.target.value as RoleCode }),
                              )
                            }
                            disabled={busyKey === `role-${user.id}`}
                          >
                            {roleOptions.map((role) => (
                              <option key={role} value={role}>
                                {roleLabels[role]}
                              </option>
                            ))}
                          </select>
                        </label>
                        <StatusBadge status={user.role === 'admin' ? 'critical' : 'ready'} />
                      </div>
                      <div className="permission-chip-grid" aria-label={`${user.name} 权限`}>
                        {permissionOptions.map((permission) => (
                          <label key={permission} className="permission-chip">
                            <input
                              type="checkbox"
                              checked={draftPermissions.includes(permission)}
                              onChange={() => togglePermissionDraft(user.id, permission)}
                            />
                            <span>{permissionLabels[permission]}</span>
                          </label>
                        ))}
                      </div>
                      <div className="row-actions">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() =>
                            void runAction(`permissions-${user.id}`, async () =>
                              updateUserPermissions(user.id, { permissions: draftPermissions }),
                            )
                          }
                          isLoading={busyKey === `permissions-${user.id}`}
                        >
                          <KeyRound size={14} />
                          保存权限
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          disabled={isLastAdmin}
                          onClick={() => void runAction(`delete-${user.id}`, async () => deleteUser(user.id))}
                          isLoading={busyKey === `delete-${user.id}`}
                        >
                          <UserMinus size={14} />
                          删除用户
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState title="暂无用户" description="后端未返回可管理用户。" />
            )}
          </Panel>

          <Panel>
            <SectionHeader title="审核插件" description="审核中高风险插件函数，上架后进入白名单任务流。" />
            {pluginReviews.length ? (
              <div className="plugin-review-list">
                {pluginReviews.map((review) => (
                  <div key={review.id} className="plugin-review-row">
                    <div className="plugin-card-head">
                      <PlugZap size={18} />
                      <div>
                        <strong>{review.title}</strong>
                        <span>{review.functionName}</span>
                      </div>
                      <StatusBadge status={review.status === 'approved' ? 'success' : review.status === 'rejected' ? 'denied' : 'pending'} />
                    </div>
                    <div className="plugin-meta">
                      <StatusBadge status={review.risk === 'high' ? 'critical' : review.risk === 'medium' ? 'warning' : 'info'} />
                      <span>申请方：{review.requestedBy}</span>
                      {review.reviewedBy ? <span>审核人：{review.reviewedBy}</span> : null}
                    </div>
                    {review.note ? <p>{review.note}</p> : null}
                    <div className="row-actions">
                      <Button
                        size="sm"
                        variant="primary"
                        disabled={review.status === 'approved'}
                        onClick={() =>
                          void runAction(`approve-${review.id}`, async () =>
                            reviewPlugin(review.id, { status: 'approved', note: '审核通过，允许插件函数进入白名单。' }),
                          )
                        }
                        isLoading={busyKey === `approve-${review.id}`}
                      >
                        <CheckCircle2 size={14} />
                        审核通过
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        disabled={review.status === 'rejected'}
                        onClick={() =>
                          void runAction(`reject-${review.id}`, async () =>
                            reviewPlugin(review.id, { status: 'rejected', note: '审核拒绝，普通用户不可调用该插件函数。' }),
                          )
                        }
                        isLoading={busyKey === `reject-${review.id}`}
                      >
                        <XCircle size={14} />
                        审核拒绝
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="暂无审核项" description="中高风险插件函数会在这里等待审核。" />
            )}
          </Panel>
        </div>
      ) : null}

      <Panel>
        <SectionHeader title="运行参数" description="只允许管理员修改后端已开放的运行参数。" />
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

      <Panel>
        <SectionHeader title="插件函数白名单" description="启用或停用后端函数白名单中的能力。" />
        <div className="plugin-grid">
          {functions.map((func) => (
            <div key={func.name} className="plugin-card">
              <div className="plugin-card-head">
                <PlugZap size={18} />
                <div>
                  <strong>{func.title}</strong>
                  <span>{func.name}</span>
                </div>
                <StatusBadge status={func.enabled ? 'healthy' : 'offline'} />
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
